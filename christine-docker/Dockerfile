FROM debian:bullseye-slim

RUN apt update && apt -y upgrade
RUN apt install -y --no-install-recommends wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev git vim ffmpeg libffi-dev libc6-dev uuid-dev libsqlite3-dev libgdbm-compat-dev liblzma-dev libbz2-dev libssl-dev libreadline-dev libasound2-dev portaudio19-dev libsndfile1-dev openssh-server sudo ca-certificates
RUN apt autoremove -y
RUN apt-get clean

RUN wget -qO - https://raw.githubusercontent.com/tvdsluijs/sh-python-installer/main/python.sh | bash -s 3.11.4; exit 0

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config && echo 'root:Christine@3' | chpasswd
COPY /.ssh /root/.ssh
RUN chown -R root:root /root/.ssh && chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys && service ssh start

RUN pip install wheel gnureadline requests smbus numpy mpu6050-raspberrypi bottle RPi.GPIO Adafruit-Blinka adafruit-circuitpython-mpr121 pyserial google-generativeai pyaudio pydub debugpy pvcobra nltk scipy langchain weaviate-client pveagle requests-sse tiktoken spacy openai google-cloud-aiplatform jsons vertexai google-cloud-texttospeech
RUN python3.11 -m spacy download en_core_web_sm
RUN sed -i 's@"/completions",@"/prompt",@g' /usr/lib/python3.11/site-packages/openai/resources/completions.py
RUN sed -Ei "s/os\.getenv\('TEMORARILY_DISABLE_PROTOBUF_VERSION_CHECK'\)/'true'/" /usr/lib/python3.11/site-packages/google/protobuf/runtime_version.py

# enable audio for testing, really should be up there ^
RUN apt update && apt -y upgrade
RUN apt install -y --no-install-recommends alsa-utils jq less && apt-get clean

# The touch sensor module needed some customization
COPY /adafruit_mpr121.py /usr/lib/python3.11/site-packages/adafruit_mpr121.py

EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
