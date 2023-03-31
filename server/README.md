This directory contains scripts meant to run off pi, for speech recognition and audio analysis model training purposes. 

preprocess.py
Uses ffmpeg and rubberband to preprocess the master sounds. ffmpeg to jack up volume, rubberband to create a series of tempo-adjusted versions of each file to randomize the way things are said. 

wernicke_server.py
Listens for connections from the pi, receives audio, feeds into whisper for speech recognition. 

wernicke_training_block/
Tools made for sorting and training the single block classifier model.

wernicke_training_proximity/
Tools used for training proximity model. 

