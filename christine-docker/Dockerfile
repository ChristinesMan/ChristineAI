FROM python:3.11

RUN apt update && apt -y upgrade
RUN apt install -y --no-install-recommends wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev git vim ffmpeg libffi-dev libc6-dev uuid-dev libsqlite3-dev libgdbm-compat-dev liblzma-dev libbz2-dev libssl-dev libreadline-dev libasound2-dev portaudio19-dev libsndfile1-dev openssh-server sudo ca-certificates alsa-utils jq less
RUN apt autoremove -y
RUN apt-get clean

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config && echo 'root:Christine@3' | chpasswd
RUN sed -i 's/#Port 22/Port 2222/g' /etc/ssh/sshd_config
COPY /.ssh /root/.ssh
RUN chown -R root:root /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

RUN pip install --no-cache-dir wheel gnureadline requests
RUN pip install --no-cache-dir smbus numpy mpu6050-raspberrypi bottle RPi.GPIO Adafruit-Blinka adafruit-circuitpython-mpr121 pyserial webrtcvad-wheels
RUN pip install --no-cache-dir google-generativeai pyaudio pydub debugpy pvcobra nltk scipy langchain weaviate-client pveagle
RUN pip install --no-cache-dir requests-sse tiktoken spacy openai google-cloud-aiplatform jsons vertexai google-cloud-texttospeech adafruit-circuitpython-mcp230xx
RUN python3 -m spacy download en_core_web_sm
#RUN sed -i 's@"/completions",@"/prompt",@g' /usr/lib/python3.11/site-packages/openai/resources/completions.py
#RUN sed -Ei "s/os\.getenv\('TEMORARILY_DISABLE_PROTOBUF_VERSION_CHECK'\)/'true'/" /usr/lib/python3.11/site-packages/google/protobuf/runtime_version.py

# This seems to fix the error:
# Missing privilege separation directory: /run/sshd
RUN service ssh start

# Add later when time to rebuild
# apt install sqlite (the cli command)

# move up there when time to fully rebuild
COPY /vcgencmd /usr/bin/vcgencmd
RUN chmod 700 /usr/bin/vcgencmd
COPY /.bashrc /root/.bashrc

#EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
