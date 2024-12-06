On a Jetson computer: 

(Martin using user mcu)

create ed25519 key pair under user xxx
```
   ssh-keygen -t ed25519
```
Put key on Github


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

checkout repo with the video demo script
```
cd ~
git clone git@github.com:ADACS-Australia/HuntsmanCamera.git
cd HuntsmanCamera
```

modify camera serial number etc in yaml and use the script
```
cd scripts
python3 pp_test.py -h
python3 pp_test.py -d -c ../config/ASI183MM_jetson005.yaml
```
There is a number of configuration files in the config subdirectory, for both 
ASI1600 ZWO camera connected to DFN system embedded PC inthe DFN lab on Curtin campus, and for ASI183 cameras 
connected to Jetson computers of the Huntsman telecope. 
(There are comments describing the parameters in yaml file [ASI183MM_jetson005.yaml](config/ASI183MM_jetson005.yaml) where needed.)
