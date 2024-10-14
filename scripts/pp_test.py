from panoptes.pocs.camera.libasi import ASIDriver
from panoptes.pocs.camera.zwo import Camera as ZWOCam


if __name__ == '__main__':
    kwargs['serial_number'] = '1f2f190206070900'
    cam = ZWOCam(**kwargs)

