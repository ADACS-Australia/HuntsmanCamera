from typing import Final
from astropy import units as u
# import numpy as np
import time
from datetime import datetime, timezone, timedelta
import multiprocessing
import argparse
import yaml
import logging
import os

# fitsio provides way better performance for FITS compression
import fitsio
# from panoptes.utils.images import fits as fits_utils
# import fits as fits_utils

from panoptes.utils.utils import get_quantity_value

# local mended lib
from libasi import ASIDriver
# from panoptes.pocs.camera.libasi import ASIDriver
# from panoptes.pocs.camera.zwo import Camera as ZWOCam

DFN_ASI1600MMPro_SN: Final[str] = '1f2f190206070900'
JETSON009_ASI178_SN: Final[str] = '0e2c420013090900'

# Other Huntsman camera serial numbers are in
# repo huntsman-config$ /conf_files/pocs/huntsman.yaml

# A global list of processes, to be able to wait for all frames
# to be written to files.
processes = []


def setup_logger(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='ZWO ASI camera video record demo script')
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to the YAML configuration file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-p', '--parallel_write', action='store_true', help='write files in parallel with multiprocessing')
    parser.add_argument('-C', '--compress', type=str, default=None, required=False, 
                        nargs='?', const='RICE',
                        help='Enable FITS compression (RICE, GZIP, PLIO, None)')
    return parser.parse_args()


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def write_file_process(data, header, filename, compress):
    ### using panoptes.utils.images.fits as fits_utils
    # fits_utils.write_fits(data, header, filename, overwrite=True, compress=compress)
    ### using fitsio wrapper fro cfitsio
    fitsio.write(filename, data, header=header, compress=compress, clobber=True)
    # The thread will automatically exit when this function completes


def spawn_file_write(data, header, filename, compress):
    process = multiprocessing.Process(target=write_file_process, 
                                      args=(data, header, filename, compress))
    process.daemon = True
    process.start()
    processes.append(process)
    # The process will run independently and disappear when ends


def main():
    args = parse_args()   
    logger = setup_logger(args.debug)

    # Load the YAML configuration
    logger.info(f"Loading configuration from: {args.config}")
    config = load_yaml_config(args.config)

    logger.info(f"Use compression: {args.compress}")

    if args.parallel_write:
        logger.info(f"Write files in parallel threads")

    # Now you can access the configuration data
    cameras = config.get('cameras', {})
    devices = cameras.get('devices', [])

    # print config to log
    for device in devices:
        logger.info(f"Camera: {device['name']}")
        for key, value in device.items():
            if key != 'name':
                logger.info(f"  {key}: {value}")

    kwargs = {}
    kwargs['serial_number'] = device['serial_number']
    cam = ASIDriver(**kwargs)

    # libasi.py might need to be updated for later ZWO SDK versions
    # this was tested with V1.33 and V1.29
    ver = cam.get_SDK_version()
    logger.info(f'SDK Version is {ver}')

    cameras = cam.get_devices()
    logger.debug(f'Devices {cameras}')

    ids = cam.get_product_ids()
    logger.debug(f'Product IDs {ids}')

    cam_id = cameras[device['serial_number']]
    cam.open_camera(cam_id)
    cam.init_camera(cam_id)

    # read and print initial camera configs
    info = cam.get_camera_property(cam_id)
    logger.info(f'Camera info: {info}')

    camera_name = info['name']
    pixel_size = get_quantity_value(info['pixel_size'], unit=u.um)

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
        size_x_int = int(get_quantity_value(info['max_width'], unit=u.pix))
        size_y_int = int(get_quantity_value(info['max_height'], unit=u.pix))
        cam.set_roi_format(cam_id,
                           ((size_x_int / binning) // 8) * 8,
                           ((size_y_int / binning) // 8) * 8,
                           binning, img_type)

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
    gain = int(gain[0])

    # exposure is in uS
    exposure_time = device['exposure_time']
    cam.set_control_value(cam_id, 'EXPOSURE', exposure_time)
    exp_time = cam.get_control_value(cam_id, 'EXPOSURE')
    logger.debug(f'Exposure_time = {exp_time}')
    exp_time_us_int = int(round(get_quantity_value(exp_time[0], unit=u.us)))
    logger.info(f'Exposure_time [int] = {exp_time_us_int}')

    ### check this? or leave defaults?
    # ASISetControlValue(CamInfo.CameraID,ASI_BANDWIDTHOVERLOAD, 40, ASI_FALSE); //low transfer speed
	# ASISetControlValue(CamInfo.CameraID,ASI_HIGH_SPEED_MODE, 0, ASI_FALSE);
    bw_overload = cam.get_control_value(cam_id, 'BANDWIDTHOVERLOAD')
    logger.debug(f'Bandwidth overload = {bw_overload}')
    hs_mode = cam.get_control_value(cam_id, 'HIGH_SPEED_MODE')
    logger.debug(f'High speed mode = {hs_mode}')

    cam.set_control_value(cam_id, 'TARGET_TEMP', device['target_temperature'])
    target_temp = cam.get_control_value(cam_id, 'TARGET_TEMP')
    logger.debug(f'Target temperature = {target_temp}')
    target_temp_float = get_quantity_value(target_temp[0], unit=u.deg_C)
    logger.info(f'Target temperature [float] = {target_temp_float}')

    cam.set_control_value(cam_id, 'COOLER_ON', True)
    cooler_on = cam.get_control_value(cam_id, 'COOLER_ON')
    logger.info(f'Cooler status = {cooler_on}')

    num_frames = device['num_frames']
    frames_count = 0
    logger.info(f'Starting to capture {num_frames} frames')

    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.info(f"Files open soft limit: {soft}, hard limit: {hard}")

    cam.start_video_capture(cam_id)

    start_datetime = datetime.now(timezone.utc)
    start_time = time.perf_counter()
    frame_start_datetime = start_datetime
    frame_start_time = start_time

    output_folder = device['output_folder']

    while frames_count < num_frames:
        temp = cam.get_control_value(cam_id, 'TEMPERATURE')
        temp_C = temp[0] / 10.0

        # timeout 500 is from Dale's example
        data = cam.get_video_data(cam_id, roi_format['width'], roi_format['height'], img_type, 500)
        frame_got_data_time = time.perf_counter()
        frame_end_datetime = datetime.now(timezone.utc) 
        if data is not None:
            filename = str(f'frame{frames_count:06d}.fits')
            start_date = frame_start_datetime.replace(microsecond=int((frame_start_time % 1) * 1e6))
            end_date = start_date + timedelta(microseconds=exp_time_us_int)
            exp_time = exp_time_us_int / 1e6
            # end_date = frame_end_datetime.replace(microsecond=int((frame_got_data_time % 1) * 1e6))
            iso_start_date = start_date.isoformat(timespec='milliseconds').replace('+00:00', '')
            iso_end_date = end_date.isoformat(timespec='milliseconds').replace('+00:00', '')
            logger.debug(f'ISO frame start: {iso_start_date}  end: {iso_end_date}  temp: {temp_C}')
            header = { 'FILE': filename, 
                       'TEST': True, 
                       'EXPTIME': exp_time,
                       'EXPOSURE': exp_time,
                       'EXPOINUS': exp_time_us_int,
                       'START_X': start_x_int,
                       'START_Y': start_y_int,
                       'DATE-OBS': iso_start_date,
                       'DATE-STA': iso_start_date,
                       'DATE-END': iso_end_date,
                       'XBINNING': binning,
                       'YBINNING': binning,
                       'GAIN': gain,
                       'BAYERPAT': 'NONE',
                       'COLORTYP': img_type,
                       'INSTRUME': camera_name,
                       'XPIXSZ': pixel_size,
                       'YPIXSZ': pixel_size,
                       'CCD_TEMP': get_quantity_value(temp_C, unit=u.deg_C)
                     }
            full_path = os.path.join(output_folder, filename)

            ### using panoptes.utils.images.fits as fits_utils
            # fits_utils.write_fits(data, header, full_path, 
            #                      overwrite=True,
            #                      compress=args.compress)
            # ### using multiprocessing to write file in a side thread is not really faster
            # spawn_file_write(data, header, full_path, compress=args.compress)

            ### using fitsio wrapper for cfitsio
            # clobber=True is to overwrite existing files

            if args.parallel_write:
                # ### using multiprocessing to write file in a side thread is not really faster
                spawn_file_write(data, header, full_path, args.compress)
            else:
                fitsio.write(full_path, data, header=header, compress=args.compress, clobber=True)

            frame_start_time = frame_got_data_time
            frame_start_datetime = frame_end_datetime
        else:
            logger.error("No data.")
        frames_count += 1

    end_time = time.perf_counter()

    cam.stop_video_capture(cam_id)

    if filename is not None:
        logger.info(f'last frame file name: {full_path}')    

    elapsed_time = end_time - start_time
    logger.info(f"Recorded {frames_count} frames, elapsed capture time: {elapsed_time:.6f} seconds")
    logger.info(f"Measured FPS: {frames_count/elapsed_time:.2f}")

    dropped_frames = cam.get_dropped_frames(cam_id)
    logger.info(f"Number of dropped frames: {dropped_frames}")

    if args.parallel_write:
        # Wait for all processes to complete
        for process in processes:
            process.join()
        logger.info(f"All file writing processes have completed.")
        end_write_time = time.perf_counter()
        elapsed_time = end_write_time - end_time
        logger.info(f"Writing files in parallel to catch up took extra time: {elapsed_time:.6f} seconds")


if __name__ == '__main__':
    main()
