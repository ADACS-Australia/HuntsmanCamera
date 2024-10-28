from typing import Final
from astropy import units as u
import numpy as np
import time
from datetime import datetime, timezone, timedelta
import multiprocessing
import argparse
import yaml

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

def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def write_file_thread(data, header, filename):
    fits_utils.write_fits(data, header, filename, overwrite=True)
    # The thread will automatically exit when this function completes


def spawn_file_write(data, header, filename):
    process = multiprocessing.Process(target=write_file_process, args=(data, header, filename))
    process.daemon = True
    process.start()
    # The process will run independently


def main():   
    parser = argparse.ArgumentParser(description='Camera configuration script')
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to the YAML configuration file')
    
    args = parser.parse_args()
    
    # Load the YAML configuration
    config = load_yaml_config(args.config)
    
    # Now you can access the configuration data
    cameras = config.get('cameras', {})
    devices = cameras.get('devices', [])
    
    for device in devices:
        print(f"Camera: {device['name']}")
        print(f"Serial Number: {device['serial_number']}")
        print(f"Exposure Time: {device['exposure_time']}")
        # ... and so on for other parameters
        print("---")
        
    kwargs = {}   
    kwargs['serial_number'] = CAM_SN
    
    # cam = ZWOCam(**kwargs)
    
    cam = ASIDriver(**kwargs)
    ver = cam.get_SDK_version()
    print(f'SDK Version is {ver}')
    
    cameras = cam.get_devices()
    print(f'Devices {cameras}')
    
    ids = cam.get_product_ids()
    # print(f'Product IDs {ids}')
    
    cam_id = cameras[CAM_SN] 
    
    cam.open_camera(cam_id)
    cam.init_camera(cam_id)
    
    info = cam.get_camera_property(cam_id)
    print(f'Camera info: {info}')

    n_controls = cam.get_num_of_controls(cam_id)
    print(f'n_controls {n_controls}')

    controls = cam.get_control_caps(cam_id)
    print(f'Camera control caps {controls}')

    supported_modes = cam.get_camera_supported_mode(cam_id)
    print(f'Number of camera supported modes: {len(supported_modes)}')
    print(f'Camera supported modes {supported_modes}')
    
    print(f'ROI and offset full frame')

    ff_roi_format = cam.get_roi_format(cam_id)
    print(f'ROI format {ff_roi_format}')

    ff_start_x, ff_start_y = cam.get_start_position(cam_id)
    print(f'ROI start X={ff_start_x} Y={ff_start_y}')

    gain = cam.get_control_value(cam_id, 'GAIN')
    print(f'Gain={gain}')
    exp_time = cam.get_control_value(cam_id, 'EXPOSURE')
    print(f'Exposure_time={exp_time}')

    hw_bin = cam.get_control_value(cam_id, 'HARDWARE_BIN')
    print(f'Hardware binning={hw_bin}')


    print(f'----- Camera config set and read back -----')
    
    # activate HW binning
    cam.set_control_value(cam_id, 'HARDWARE_BIN', True)
    hw_bin = cam.get_control_value(cam_id, 'HARDWARE_BIN')
    print(f'Hardware binning={hw_bin}')

    # set and print ROI and offset

    # binning 2x2 is HW - this is the only one that makes sense for speed-up
    # binning 3x3 is SW
    # binning 4x4 is HW (2x2) + SW (second time 2x2) 
    binning = 2
    
    # ROI - crop size
    sq_crop = 400
    size_x = sq_crop
    size_y = sq_crop
    size_pix_x = size_x * u.pixel
    size_pix_y = size_y * u.pixel
    print(f"size_pix_x={size_pix_x}")
    print(ff_roi_format['width'])
    # cam.set_roi_format(cam_id, size_pix_x, size_pix_y, binning, 'RAW16')
    cam.set_roi_format(cam_id, 
                       ff_roi_format['width']/binning, 
                       ff_roi_format['height']/binning, 
                       binning, 'RAW16')
    
    roi_format = cam.get_roi_format(cam_id)
    print(f'ROI format {roi_format}')    
    
    # ROI - crop offset (start)
    #x = ff_roi_format['width']/2 - size_pix_x/2
    #y = ff_roi_format['height']/2 - size_pix_y/2
    # x = (x / 4) * 4
    # y = (y / 4) * 4
    y = 400
    x = 400
    print(f'Try to set ROI start X={x} Y={y}')
    cam.set_start_position(cam_id, x, y)
    start_x, start_y = cam.get_start_position(cam_id)
    print(f'ROI start X={start_x} Y={start_y}')
    start_x_int = int(get_quantity_value(start_x, unit=u.pix))
    start_y_int = int(get_quantity_value(start_y, unit=u.pix))
    
    cam.set_control_value(cam_id, 'GAIN', 100)
    gain = cam.get_control_value(cam_id, 'GAIN')
    print(f'Gain={gain}')
    # exposure is in uS
    exposure_time = 20000
    cam.set_control_value(cam_id, 'EXPOSURE', exposure_time)
    exp_time = cam.get_control_value(cam_id, 'EXPOSURE')
    print(f'Exposure_time={exp_time}')
    exp_time_us_int = int(round(get_quantity_value(exp_time[0], unit=u.us)))
    print(f'Read back exposure_time [int]={exp_time_us_int}')
    
    ### TODO
    # ASISetControlValue(CamInfo.CameraID,ASI_BANDWIDTHOVERLOAD, 40, ASI_FALSE); //low transfer speed
	# ASISetControlValue(CamInfo.CameraID,ASI_HIGH_SPEED_MODE, 0, ASI_FALSE);
    bw_overload = cam.get_control_value(cam_id, 'BANDWIDTHOVERLOAD')
    print(f'bandwidth overload = {bw_overload}')
    hs_mode = cam.get_control_value(cam_id, 'HIGH_SPEED_MODE')
    print(f'High speed mode = {hs_mode}')

    num_frames = 20
    frames_count = 0
    cam.start_video_capture(cam_id)
    
    # create memory bufer to read out and save frames
        
    start_datetime = datetime.now(timezone.utc)
    start_time = time.perf_counter()
    frame_start_datetime = start_datetime
    frame_start_time = start_time
        
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
            print(f'ISO frame start: {iso_start_date}  end: {iso_end_date}')
            header = { 'FILE': filename, 'TEST': True, 'EXPTIME': exp_time_us_int,
                       'START_X': start_x_int, 'START_Y': start_y_int,
                       'DATE-OBS': iso_start_date,
                       'DATE-STA': iso_start_date,
                       'DATE-END': iso_end_date
                     }
            # fits_utils.write_fits(data, header, filename, overwrite=True)
            write_file_thread(data, header, filename)
            frame_start_time = frame_got_data_time
            frame_start_datetime = frame_end_datetime
        else:
            print("No data.")
        frames_count += 1

    end_time = time.perf_counter()
        
    cam.stop_video_capture(cam_id)

    elapsed_time = end_time - start_time
    print(f"Recorded {frames_count} frames, elapsed time: {elapsed_time:.6f} seconds")
    print(f"Measured FPS: {frames_count/elapsed_time:.2f}")
    
    dropped_frames = cam.get_dropped_frames(cam_id)
    print(f"Number of dropped frames: {dropped_frames}")


if __name__ == '__main__':
    main()
    
    