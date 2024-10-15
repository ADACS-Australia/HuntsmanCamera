from typing import Final

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

