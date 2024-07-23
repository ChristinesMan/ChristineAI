# ChristineAI Server

This directory contains code meant to be run from a local server with a GPU. You can also run from multiple machines on the local network. So theoretically you could have one server providing speech recognition and another server providing voice synthesis. 

The servers announce themselves by sending broadcast UDP packets on specific ports. It is also possible to specify the hostname/IP. 

## Server Setup

1. Install whatever flavor of linux you like best. For the latest build I installed Ubuntu 22.04 onto a USB thumb drive. Get root ssh access. For convenience you can also setup key authentication and nfs, but that's outside the scope of these instructions.

2. Update and install software. 

```
root@server:~# apt update && apt upgrade -y
root@server:~# apt install wget build-essential gcc git vim ffmpeg python3-venv espeak sox libsox-dev libavutil-dev rust-all
```

3. If your hardware is an nvidia GPU, install the CUDA Toolkit. Start at https://developer.nvidia.com/cuda-downloads?target_os=Linux. 

4. Clone the repo.

```
root@server:~# git clone https://github.com/ChristinesMan/ChristineAI.git
```

5. Python version 3.10 should already be installed. If it installed 3.11 that's fine, too. We're just going to use the default python3 version. So all we need to do is create a venv, activate it, upgrade pip, and install modules we need. The venv is a directory named venv where all the python modules get installed in it's own little area. 

There are two separate services and each one has different packages they need, so they have separate venv directories. 

The wernicke service is for processing audio from your lady's ears into text. 

The broca service is for taking text and synthesizing into your lady's voice. 

```
root@server:~# cd ChristineAI/christine-server

root@server:~/ChristineAI/christine-server# python3 -m venv wernicke_venv
root@server:~/ChristineAI/christine-server# source wernicke_venv/bin/activate
(wernicke_venv) root@server:~/ChristineAI/christine-server# python -m pip install --upgrade pip wheel
(wernicke_venv) root@server:~/ChristineAI/christine-server# pip install gnureadline debugpy pveagle openai-whisper pyyaml
(wernicke_venv) root@server:~/ChristineAI/christine-server# deactivate

root@server:~/ChristineAI/christine-server# python3 -m venv broca_venv
root@server:~/ChristineAI/christine-server# source broca_venv/bin/activate
(broca_venv) root@server:~/ChristineAI/christine-server# python -m pip install --upgrade pip wheel
(broca_venv) root@server:~/ChristineAI/christine-server# pip install gnureadline debugpy ffmpeg-python pyyaml
(broca_venv) root@server:~/ChristineAI/christine-server# pip install TTS
(broca_venv) root@server:~/ChristineAI/christine-server# deactivate

OR if you want to try the one-liner:

root@server:~# cd ChristineAI/christine-server && python3.11 -m venv wernicke_venv && source wernicke_venv/bin/activate && python -m pip install --upgrade pip wheel && pip install gnureadline debugpy pveagle openai-whisper pyyaml && deactivate && python3.11 -m venv broca_venv && source broca_venv/bin/activate && python -m pip install --upgrade pip wheel && pip install gnureadline debugpy ffmpeg-python pyyaml && pip install TTS && pip install TTS && deactivate
```

6. The broca server will need some voice model files inside a tts_model directory like this:

```
tts_model/
├── config.json
└── model.pth
```

I cannot provide the custom model I made. I started with the TTS model called "jenny" and fine-tuned that using thousands of wav files with text annotations. You can get an easier start by just obtaining the jenny model and putting those default files into place. See the TTS docs at https://docs.coqui.ai/en/latest/finetuning.html for how to get the config.json and model.pth. 

7. Copy config.ini.sample to config.ini. Edit the file to set certain settings. There may be API keys that go in here. The wernicke has a model size setting that controls which model size to use. The default is medium.en, which should barely fit if you have at least 8G of GPU memory. There are also small and tiny if you need to use a smaller model. 

8. Copy the systemd service files to /lib/systemd/system/. This will provide systemd services that will run the scripts at boot. 

```
root@server:~/ChristineAI/christine-server# cp *.service /lib/systemd/system/
root@server:~/ChristineAI/christine-server# systemctl daemon-reload
root@server:~/ChristineAI/christine-server# systemctl enable wernicke.service --now
root@server:~/ChristineAI/christine-server# systemctl enable broca.service --now
```
