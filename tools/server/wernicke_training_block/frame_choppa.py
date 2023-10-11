import termios, fcntl, sys, os
from pydub import AudioSegment
from pydub.playback import play
import wave

def get_char_keyboard():
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    c = None
    try:
        c = sys.stdin.read(1)
    except IOError: pass

    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return c

# how far to skip for each block
step_ms = 125

# aka 4000 samples at 16000 samples per second
block_ms = 250

mainwav = AudioSegment.from_wav('./new/concat.wav')
mainlen = int(mainwav.duration_seconds) * 1000
print(f'mainlen: {mainlen}')

for position in range(0, mainlen, step_ms):

    if position + block_ms > mainlen:
        print(f'Looks like we met the end at position {position}')
        exit()

    wav = mainwav[position:position+block_ms]
    play(wav * 2)

    key_pressed = None
    while key_pressed not in ['l', 'f']:
        print('(l)over_close  (enter)replay  (f)delete  (q)uit')
        key_pressed = get_char_keyboard()
        if key_pressed == 'l':
            RecordFileName = './lover_mid/16129817760_{0}.wav'.format(position)
            print(f'Saved {RecordFileName}')
            wf = wave.open(RecordFileName, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(wav.raw_data)
            wf.close()
        elif key_pressed == "\n":
            play(wav * 2)
        elif key_pressed == 'q':
            exit()
