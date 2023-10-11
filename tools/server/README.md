This directory contains scripts meant to run off pi, for speech recognition and audio analysis model training purposes.
This server would be on the local network, but not required. It'll run faster with a GPU, but not required.


preprocess.py
Uses ffmpeg and rubberband to preprocess the master sounds. ffmpeg to jack up volume, rubberband to create a series of tempo-adjusted versions of each file to randomize the way things are said. 


wernicke_server.py
Listens for connections from the pi, receives audio, feeds into whisper for speech recognition, returns text. 

wernicke.service
This file should be copied to /lib/systemd/system/ on a server to create the systemd service.

wernicke.sh
This file should be copied to /usr/bin/ on a server. The systemd service calls this to start the server.

wernicke_training_block/
Tools made for sorting and training the single block classifier model.

wernicke_training_proximity/
Tools used for training proximity model. 


broca_server.py
Listens for connections from the pi, receives text, returns speech synthesis.

broca.service
This file should be copied to /lib/systemd/system/ on a server to create the systemd service.

broca.sh
This file should be copied to the /usr/bin/ on a server. The systemd service calls this to start the server.
