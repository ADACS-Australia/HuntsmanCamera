from typing import Final
from astropy import units as u
import numpy as np
import time

from panoptes.utils.images import fits as fits_utils
from panoptes.utils.utils import get_quantity_value
    
# local mended lib
from libasi import ASIDriver
# from panoptes.pocs.camera.libasi import ASIDriver
# from panoptes.pocs.camera.zwo import Camera as ZWOCam

DFN_ASI1600MMPro_SN: Final[str] = '1f2f190206070900'


if __name__ == '__main__':
    kwargs = {}   
    kwargs['serial_number'] = DFN_ASI1600MMPro_SN
    
    # cam = ZWOCam(**kwargs)
    
    cam = ASIDriver(**kwargs)
    ver = cam.get_SDK_version()
    print(f'SDK Version is {ver}')
    
    cameras = cam.get_devices()
    print(f'Devices {cameras}')
    
    ids = cam.get_product_ids()
    # print(f'Product IDs {ids}')
    
    cam_id = cameras[DFN_ASI1600MMPro_SN] 
    
    cam.open_camera(cam_id)
    cam.init_camera(cam_id)
    
    info = cam.get_camera_property(cam_id)
    print(f'Camera info: {info}')

    n_controls = cam.get_num_of_controls(cam_id)
    print(f'n_controls {n_controls}')

    controls = cam.get_control_caps(cam_id)
    print(f'Camera control caps {controls}')

    supported_modes = cam.get_camera_supported_mode(cam_id)
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

    print(f'----- Camera config set and read back -----')
    # set and print ROI and offset
    sq_crop = 1000
    size_x = sq_crop
    size_y = sq_crop
    size_pix_x = size_x * u.pixel
    size_pix_y = size_y * u.pixel
    #roi_format['image_type'] = 'RAW16'
    #roi_format['height'] = sq_crop
    #roi_format['width'] = sq_crop
    cam.set_roi_format(cam_id, size_pix_x, size_pix_y, 1, 'RAW16')
    roi_format = cam.get_roi_format(cam_id)
    print(f'ROI format {roi_format}')
    
    x = ff_roi_format['width']/2 - size_pix_x/2
    y = ff_roi_format['height']/2 - size_pix_y/2
    cam.set_start_position(cam_id, x, y)
    start_x, start_y = cam.get_start_position(cam_id)
    print(f'ROI start X={start_x} Y={start_y}')
    start_x_int = int(get_quantity_value(start_x, unit=u.pix))
    start_y_int = int(get_quantity_value(start_y, unit=u.pix))

    cam.set_control_value(cam_id, 'GAIN', 100)
    gain = cam.get_control_value(cam_id, 'GAIN')
    print(f'Gain={gain}')
    # exposure is in uS
    exposure_time = 50000
    cam.set_control_value(cam_id, 'EXPOSURE', exposure_time)
    exp_time = cam.get_control_value(cam_id, 'EXPOSURE')
    print(f'Exposure_time={exp_time}')
    exp_time_us_int = int(round(get_quantity_value(exp_time[0], unit=u.us)))
    print(f'read back exposure_time [int]={exp_time_us_int}')
    
    num_frames = 20
    frames_count = 0
    cam.start_video_capture(cam_id)
    
    # create memory bufer to read out and save frames
    data = cam.get_video_data(cam_id, roi_format['width'], roi_format['height'], 'RAW16', 500)
        
    start_time = time.perf_counter()
    
    while frames_count < num_frames:
        # timeout 500 is from Dale's example
        filename = str(f'frame{frames_count:06d}.fits')
        header = { 'FILE': filename, 'TEST': True, 'EXPTIME': exp_time_us_int,
                   'START_X': start_x_int, 'START_Y': start_y_int
                 }
        fits_utils.write_fits(data, header, filename, overwrite=True)
        frames_count += 1

    end_time = time.perf_counter()
        
    cam.stop_video_capture(cam_id)

    elapsed_time = end_time - start_time
    print(f"Recorded {frames_count} frames, elapsed time: {elapsed_time:.6f} seconds")
    
    dropped_frames = cam.get_dropped_frames(cam_id)
    print(f"Number of dropped frames: {dropped_frames}")
    

    