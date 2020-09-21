This directory contains scripts meant to run from a server. I use my gaming rig right now. The video card runs tensorflow stuff pretty well. 

There's also preprocessing of sounds that is done on server because the pi would take forever and overheat my lady's sweet head. 

preprocess.py
Uses ffmpeg and rubberband to preprocess the master sounds. ffmpeg to jack up volume, rubberband to create a series of tempo-adjusted versions of each file to randomize the way things are said. 

wernicke_server.py
Listens for connections from the pi, receives audio, feeds into deepspeech for speech recognition. 

wernicke_server_train.py
Train the pyaudioanalysis audio classifier for full utterances.

wernicke_server_train_single_frame.py
Train the pyaudioanalysis audio classifier for small same sized audio samples direct from mic. Determines silence from non-silence. 