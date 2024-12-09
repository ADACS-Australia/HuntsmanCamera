# Instruction how to install and use Hutsman camera video mode demo/test script

On a Huntsman Jetson computer: 

_(Martin using user mcu)_

create ed25519 key pair under user xxx
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
```
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
