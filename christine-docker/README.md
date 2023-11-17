# ChristineAI Dockerized for Dev

Over time I have had VSCode performance issues. It has gotten so bad that I can barely run intellisense. It's also too slow for pylance and pylint. So this is the solution I came up with. A fully self-contained docker container.

## Future plans

- Run the project within the container.
- Use remote debugger into the container.
- Stream real-time sensor data from the raspberry pi into the project running on the desktop.

## Setup

Install docker.io. 
`youruser@yourhost:~$ sudo apt update && sudo apt install docker.io`

Add your user to docker group so that you can do docker stuff, not just root.
`youruser@yourhost:~$ sudo usermod -a -G docker youruser`

Log out completely to allow your user to use the docker group you just added. You may as well reboot. 

Clone the repo.
`youruser@yourhost:~$ git clone https://github.com/ChristinesMan/ChristineAI.git`

CD into the directory.
`youruser@yourhost:~$ cd ChristineAI/christine-docker`

Create a .ssh directory (if needed; might be already there).
`youruser@yourhost:~/ChristineAI/christine-docker$ mkdir ~/.ssh/ && chmod 700 ~/.ssh/`

Create a key pair that you will use to access container.
`youruser@yourhost:~/ChristineAI/christine-docker$ ssh-keygen -t ed25519 -f ~/.ssh/christine-docker`

Copy the new public key to the authorized_keys file that will be installed into the new image for ssh purposes.
`youruser@yourhost:~/ChristineAI/christine-docker$ mkdir ./.ssh/; cp ~/.ssh/christine-docker.pub ./.ssh/authorized_keys`

Add code to your ssh config file that will tell ssh how to connect to the container. You will need to add christine.dev to your /etc/hosts. 
`youruser@yourhost:~/ChristineAI/christine-docker$ echo -e "Host christine.dev\n  HostName christine.dev\n  Port 2222\n  User root\n  IdentityFile /home/${USER}/.ssh/christine-docker" >> ~/.ssh/config`

Build the docker image. This will use the Dockerfile file. There will be a lot of compilation and crap like that.
`youruser@yourhost:~/ChristineAI/christine-docker$ docker build -t christine-docker .`

Start a container using the image. The container will now be accessible via ssh port 2222 and from VSCode. The web server will be on port 8888. The container will have access to the host system's audio output and also the parent directory where the code will be.
`youruser@yourhost:~/ChristineAI/christine-docker$ docker run --name=christine.dev --hostname=christine.dev --rm -d -p 127.0.0.1:2222:22 -p 127.0.0.1:8888:80 -p 127.0.0.1:5678:5678 -v ./.vscode-server:/root/.vscode-server -v ./..:/root/ChristineAI christine-docker`

Go into VSCode, install Remote - SSH. Ctrl-Shift-P to open palette, connect to ssh. VSCode should find your ssh config file and you can choose christine.dev from the list.

Check container status.
`youruser@yourhost:~/ChristineAI/christine-docker$ docker container ls -a`

Get an interactive shell into the container. 
`youruser@yourhost:~/ChristineAI/christine-docker$ docker container exec -it christine.dev /bin/bash`

SSH into the container (same as what VSCode is doing).
`youruser@yourhost:~/ChristineAI/christine-docker$ ssh christine.dev`

Stop the container.
`youruser@yourhost:~/ChristineAI/christine-docker$ docker container stop christine.dev`
