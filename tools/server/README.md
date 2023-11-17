This directory contains scripts meant to run off pi, for speech recognition and voice synthesis purposes.
This server would be on the local network, but could be remote. 
My machine has about 8G of GPU memory. You could use a less accurate speech recognition model if it's tight.


wernicke_server.py
Listens for connections from the pi, receives audio, feeds into whisper for speech recognition, returns text. 

wernicke.service
This file should be copied to /lib/systemd/system/ on a server to create the systemd service.


wernicke_training_block/
Tools made for sorting and training the single block classifier model. (no longer used)

wernicke_training_proximity/
Tools used for training proximity model. 


broca_server.py
Listens for connections from the pi, receives text, returns speech synthesis.

broca.service
This file should be copied to /lib/systemd/system/ on a server to create the systemd service.

