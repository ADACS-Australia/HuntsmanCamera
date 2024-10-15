from libasi import ASIDriver
# from panoptes.pocs.camera.libasi import ASIDriver
# from panoptes.pocs.camera.zwo import Camera as ZWOCam


if __name__ == '__main__':
    kwargs = {}
    kwargs['serial_number'] = '1f2f190206070900'
    cam = ASIDriver(**kwargs)
    ver = cam.get_SDK_version()
    print(f'SDK Version is {ver}')
    
    # cam = ZWOCam(**kwargs)

