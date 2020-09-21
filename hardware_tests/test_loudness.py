import numpy
import pyaudio
import analyse

pyaud = pyaudio.PyAudio()

stream = pyaud.open(
    format = pyaudio.paInt16,
    channels = 1,
    rate = 16000,
    input_device_index = 2,
    input = True)

while True:
    rawsamps = stream.read(16000)
    samps = numpy.fromstring(rawsamps, dtype=numpy.int16)
    print(analyse.loudness(samps))
#    print(analyse.detect_pitch(samps))
