## pp test
A Huntsman telescope video mode test/demo script [pp_test.py](scripts/pp_test.py) using Panoptes POCS ZWO ASI astronomical cameras driver [libasi](https://github.com/panoptes/POCS/blob/develop/src/panoptes/pocs/camera/libasi.py).
The libasi is a python ctypes wrapper for the proprietary closed source ASI astronomical cameras drive provided for [download](https://dl.zwoastro.com/software?app=DeveloperCameraSdk&platform=windows86&region=Overseas) by the camera manufacturer [ZWO](https://www.zwoastro.com/software/) -> OTHERS -> For Developers.

The [libasi.py](scripts/libasi.py) was copied here from the upstream panopes/pocs repo (release 0.7.8 used by Astrohuntsman/POCS) and modified (eg bug fixed and updated for later version of the underlaying binary lib.).

The [fits.py](scripts/fits.py) was also copied here from the upstream [panopes/utils](https://github.com/panoptes/panoptes-utils/blob/develop/src/panoptes/utils/images/fits.py) repo (release 0.2.35 used by Astrohuntsman/POCS) and modified to enable possiblilty to use internal FITRS compression. However, this FITS wrire/compression method based on astripy was later dropped for cfitsio providing better compression/write speed. It is kept here only prof possible experimentration, as there is still commended out code calling it in pp_test.py. Also this is the standard method panoptes and Hunstman POCS uses to write FITS files, and as such needs to be modified to call cfitsio wrapped by python (pip install fitsio).

## Instruction how to install and use Hutsman camera video mode demo/test script

On a Huntsman Jetson computer: 

_(Martin using user mcu)_

Create ed25519 key pair under user xxx, preferrably passphrase protected as it is a shared computer 
```
   ssh-keygen -t ed25519
```
Put the pub key on Github for the corresponding user.


Instal conda forge
```
CONDA_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh"
mkdir ~/down
cd ~/down/
wget -q "${CONDA_URL}" -O install-miniforge.sh
/bin/sh install-miniforge.sh -b -f -p "${HOME}/conda"
"${HOME}/conda/bin/conda" init
exit
```
Login again and create conda environment

```
ssh mcu@192.168.80.209
conda create -y -q -n huntsman python=3.9 mamba
conda activate huntsman
pip install panoptes-pocs
pip install matplotlib
...
conda list | grep panoptes
panoptes-pocs             0.7.8                    pypi_0    pypi
panoptes-utils            0.2.43                   pypi_0    pypi
```
_note: panuptes-utils seems to be later version than 0.2.35, which can be forced, but there are no apparent issues with the most recent available._

Since the camera demo app incudes compression functionality, fitsio package is needed.
The pip command below builds binary wheel of cfistio, plus one needs to install an OS lib for dependance:
```
sudo apt install libbz2-dev
pip install fitsio
```

The panoptes-config-server is not needed on Hunstan's Jetsons - alreay running
```
# /home/mcu/conda/envs/huntsman/bin/panoptes-config-server run --config-file config/zwo_video_demo.yaml
```

Checkout repo with the video demo script
```
cd ~
git clone git@github.com:ADACS-Australia/HuntsmanCamera.git
cd HuntsmanCamera
```

Modify camera serial number etc in yaml and use the script
```
cd scripts
python3 pp_test.py -h
usage: pp_test.py [-h] -c CONFIG [-d] [-p] [-a | -v] [-C [COMPRESS]]

ZWO ASI camera video record demo script

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the YAML configuration file
  -d, --debug           Enable debug logging
  -p, --parallel_write  Write files in parallel with multiprocessing
  -a, --auto_exptime    Enable automatic exposure time mode
  -v, --variable_exptime
                        Enable variable exposure time mode
  -C [COMPRESS], --compress [COMPRESS]
                        Enable FITS compression (RICE, GZIP, PLIO, None)
---

python3 pp_test.py -d -c ../config/ASI183MM_jetson005.yaml
python3 pp_test.py -p -C -c  ../config/ASI183MM_jetson005_nfs.yaml
python3 pp_test.py -a -d -C RICE -p -c ../config/ASI183MM_jetson005.yaml
```
There is a number of configuration files in the config subdirectory, for both 
ASI1600 ZWO camera connected to DFN system embedded PC inthe DFN lab on Curtin campus, and for ASI183 cameras 
connected to Jetson computers of the Huntsman telecope. 
(There are comments describing the parameters in yaml file [ASI183MM_jetson005.yaml](config/ASI183MM_jetson005.yaml) where needed.)

----

## Other notes

### Automation - calling the test script remotely from central computer



