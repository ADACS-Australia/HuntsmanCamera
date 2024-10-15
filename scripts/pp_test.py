from typing import Final
from astropy import units as u

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
    
    # this ain't work
    #ID = cam.get_ID(cam_id)
    #print(f'ID {ID}')

    info = cam.get_camera_property(cam_id)
    print(f'Camera info: {info}')

    n_controls = cam.get_num_of_controls(cam_id)
    print(f'n_controls {n_controls}')

    controls = cam.get_control_caps(cam_id)
    print(f'Camera control caps {controls}')

    supported_modes = cam.get_camera_supported_mode(cam_id)
    print(f'Camera supported modes {supported_modes}')

    roi_format = cam.get_roi_format(cam_id)
    print(f'ROI format {roi_format}')

    start_x, start_y = cam.get_start_position(cam_id)
    print(f'ROI start X={start_x} Y={start_y}')

    roi_format['image_type'] = 'RAW16'
    roi_format['height'] = 1000 * u.pixel
    roi_format['width'] = 1000 * u.pixel
    print(f'ROI format {roi_format}')



    