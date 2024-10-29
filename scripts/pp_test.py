from typing import Final
from astropy import units as u
import numpy as np
import time
from datetime import datetime, timezone, timedelta
import multiprocessing
import argparse
import yaml
import logging
import os

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.utils import get_quantity_value
    
# local mended lib
from libasi import ASIDriver
# from panoptes.pocs.camera.libasi import ASIDriver
# from panoptes.pocs.camera.zwo import Camera as ZWOCam

DFN_ASI1600MMPro_SN: Final[str] = '1f2f190206070900'
JETSON009_ASI178_SN: Final[str] = '0e2c420013090900'

CAM_SN: Final[str] = DFN_ASI1600MMPro_SN

# Other Huntsman camera serial numbers are in 
# repo huntsman-config$ /conf_files/pocs/huntsman.yaml

def setup_logger(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Example script with logging')
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to the YAML configuration file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def write_file_thread(data, header, filename):
    fits_utils.write_fits(data, header, filename, overwrite=True)
    # The thread will automatically exit when this function completes


def spawn_file_write(data, header, filename):
    process = multiprocessing.Process(target=write_file_process, 
                                      args=(data, header, filename))
    process.daemon = True
    process.start()
    # The process will run independently


def main():
    args = parse_args()   
    logger = setup_logger(args.debug)
    
    # Load the YAML configuration
    logger.info(f"Loading configuration from: {args.config}")
    config = load_yaml_config(args.config)
    
    # Now you can access the configuration data
    cameras = config.get('cameras', {})
    devices = cameras.get('devices', [])
    
    for device in devices:
        logger.info(f"Camera: {device['name']}")
        # print(f"Serial Number: {device['serial_number']}")
        # print(f"Exposure Time: {device['exposure_time']}")
        for key, value in device.items():
            if key != 'name':
                logger.info(f"  {key}: {value}")
        
    kwargs = {}   
    kwargs['serial_number'] = device['serial_number']
        
    cam = ASIDriver(**kwargs)
    ver = cam.get_SDK_version()
    logger.info(f'SDK Version is {ver}')
    
    cameras = cam.get_devices()
    logger.debug(f'Devices {cameras}')
    
    ids = cam.get_product_ids()
    logger.debug(f'Product IDs {ids}')
    
    cam_id = cameras[device['serial_number']] 
    cam.open_camera(cam_id)
    cam.init_camera(cam_id)
    
    info = cam.get_camera_property(cam_id)
    logger.info(f'Camera info: {info}')

    n_controls = cam.get_num_of_controls(cam_id)
    logger.debug(f'Number of controls {n_controls}')

    controls = cam.get_control_caps(cam_id)
    logger.debug(f'Camera control caps {controls}')

    supported_modes = cam.get_camera_supported_mode(cam_id)
    logger.debug(f'Number of camera supported modes: {len(supported_modes)}')
    logger.debug(f'Camera supported modes {supported_modes}')
    
    logger.debug(f'Original ROI and offset full frame')

    ff_roi_format = cam.get_roi_format(cam_id)
    logger.debug(f'ROI format {ff_roi_format}')

    ff_start_x, ff_start_y = cam.get_start_position(cam_id)
    logger.debug(f'ROI start X = {ff_start_x} Y = {ff_start_y}')

    gain = cam.get_control_value(cam_id, 'GAIN')
    logger.debug(f'Gain={gain}')
    exp_time = cam.get_control_value(cam_id, 'EXPOSURE')
    logger.debug(f'Exposure_time={exp_time}')

    hw_bin = cam.get_control_value(cam_id, 'HARDWARE_BIN')
    logger.debug(f'Hardware binning={hw_bin}')


    logger.info(f'----- Camera configuration and read back to verify -----')
    
    # activate HW binning
    cam.set_control_value(cam_id, 'HARDWARE_BIN', True)
    hw_bin = cam.get_control_value(cam_id, 'HARDWARE_BIN')
    logger.info(f'Hardware binning={hw_bin}')

    # set and print ROI and offset

    # binning 2x2 is HW - this is the only one that makes sense for speed-up
    # binning 3x3 is SW
    # binning 4x4 is HW (2x2) + SW (second time 2x2) 
    binning = device['pix_binning']
    
    # RAW8 or RAW16 for monochrome cameras
    img_type = device['image_type']
    
    if device['use_crop']:
        # ROI - crop size
        size_x = device['size_x']
        size_y = device['size_y']
        size_pix_x = size_x * u.pixel
        size_pix_y = size_y * u.pixel
        cam.set_roi_format(cam_id, size_pix_x, size_pix_y, binning, img_type)
        # ROI - offset 
        start_x = device['start_x']
        start_y = device['start_y']
        logger.debug(f'Try to set ROI start X={start_x} Y={start_y}')
        cam.set_start_position(cam_id, start_x, start_y)
    else:
        cam.set_roi_format(cam_id,
                           ((ff_roi_format['width'] / binning) // 4) * 4,
                           ((ff_roi_format['height'] / binning) // 4) * 4,
                           binning, 'RAW16')
    
    roi_format = cam.get_roi_format(cam_id)
    logger.info(f'ROI format {roi_format}')
    start_x, start_y = cam.get_start_position(cam_id)
    logger.info(f'ROI start X={start_x} Y={start_y}')
    start_x_int = int(get_quantity_value(start_x, unit=u.pix))
    start_y_int = int(get_quantity_value(start_y, unit=u.pix))
    
    gain = device['gain']
    cam.set_control_value(cam_id, 'GAIN', gain)
    gain = cam.get_control_value(cam_id, 'GAIN')
    logger.info(f'Gain={gain}')
    
    # exposure is in uS
    exposure_time = device['exposure_time']
    cam.set_control_value(cam_id, 'EXPOSURE', exposure_time)
    exp_time_us_int = int(round(get_quantity_value(exp_time[0], unit=u.us)))
    logger.info(f'Exposure_time [int]={exp_time_us_int}')
    
    ### TODO - check this? or leave defaults?
    # ASISetControlValue(CamInfo.CameraID,ASI_BANDWIDTHOVERLOAD, 40, ASI_FALSE); //low transfer speed
	# ASISetControlValue(CamInfo.CameraID,ASI_HIGH_SPEED_MODE, 0, ASI_FALSE);
    bw_overload = cam.get_control_value(cam_id, 'BANDWIDTHOVERLOAD')
    logger.debug(f'bandwidth overload = {bw_overload}')
    hs_mode = cam.get_control_value(cam_id, 'HIGH_SPEED_MODE')
    logger.debug(f'High speed mode = {hs_mode}')

    num_frames = device['num_frames']
    frames_count = 0
    cam.start_video_capture(cam_id)
    
    # create memory bufer to read out and save frames
        
    start_datetime = datetime.now(timezone.utc)
    start_time = time.perf_counter()
    frame_start_datetime = start_datetime
    frame_start_time = start_time
        
    output_folder = device['output_folder']
        
    while frames_count < num_frames:
        # timeout 500 is from Dale's example
        data = cam.get_video_data(cam_id, roi_format['width'], roi_format['height'], 'RAW16', 500)
        frame_got_data_time = time.perf_counter()
        frame_end_datetime = datetime.now(timezone.utc) 
        if data is not None:
            filename = str(f'frame{frames_count:06d}.fits')
            start_date = frame_start_datetime.replace(microsecond=int((frame_start_time % 1) * 1e6))
            end_date = start_date + timedelta(microseconds=exposure_time)
            # end_date = frame_end_datetime.replace(microsecond=int((frame_got_data_time % 1) * 1e6))
            iso_start_date = start_date.isoformat(timespec='milliseconds').replace('+00:00', '')
            iso_end_date = end_date.isoformat(timespec='milliseconds').replace('+00:00', '')
            logger.debug(f'ISO frame start: {iso_start_date}  end: {iso_end_date}')
            header = { 'FILE': filename, 'TEST': True, 'EXPTIME': exp_time_us_int,
                       'START_X': start_x_int, 'START_Y': start_y_int,
                       'DATE-OBS': iso_start_date,
                       'DATE-STA': iso_start_date,
                       'DATE-END': iso_end_date
                     }
            # fits_utils.write_fits(data, header, filename, overwrite=True)
            full_path = os.path.join(output_folder, filename)
            write_file_thread(data, header, full_path)
            frame_start_time = frame_got_data_time
            frame_start_datetime = frame_end_datetime
        else:
            logger.error("No data.")
        frames_count += 1

    if filename is not None:
        logger.info(f'last frame file name: {full_path}')
        
    end_time = time.perf_counter()
        
    cam.stop_video_capture(cam_id)

    elapsed_time = end_time - start_time
    logger.info(f"Recorded {frames_count} frames, elapsed time: {elapsed_time:.6f} seconds")
    logger.info(f"Measured FPS: {frames_count/elapsed_time:.2f}")
    
    dropped_frames = cam.get_dropped_frames(cam_id)
    logger.info(f"Number of dropped frames: {dropped_frames}")


if __name__ == '__main__':
    main()
    
    