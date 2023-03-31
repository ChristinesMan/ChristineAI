import termios, fcntl, sys, os, shutil
from pydub import AudioSegment
from pydub.playback import play

def get_char_keyboard():
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    c = None
    try:
        c = sys.stdin.read(1)
        if c == '':
            c = sys.stdin.read(2)
            if c == '[3':
                c = sys.stdin.read(1)
                c = 'del'
            elif c == '[F':
                c = 'end'
        elif c == "\n":
            c = 'enter'

    except IOError: pass

    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return c

# categories
cats = [
         ('l',   'lover',       'mv',     './lover/'),
         ('m',   'lover_maybe', 'mv',     './lover_maybe/'),
         ('i',   'ignore',      'mv',     './ignore/'),

         ('enter', 'replay',      'replay', ''),
         ('del',   'delete',      'delete', ''),
         ('end',   'quit',        'quit',   ''),
       ]

keys = []
menu = ''
for cat in cats:
    keys.append(cat[0])
    menu += f'({cat[0]}) {cat[1]}   '

files = os.listdir('./new/')
# files.sort()

for file in files:
    print(file)

    wav = AudioSegment.from_wav(f'./new/{file}') * 2
    play(wav)

    key_pressed = None
    while True:
        print(menu)
        key_pressed = get_char_keyboard()
        for cat in cats:
            if key_pressed == cat[0]:
                if cat[2] == 'mv':

                    # kludgerific
                    if 'lover' in cat[1]:
                        shutil.copy(f'./new/{file}', f'../wernicke_training_proximity/data/{file}')

                    os.rename(f'./new/{file}', f'{cat[3]}{file}')
                    key_pressed = None
                elif cat[2] == 'replay':
                    play(wav)
                elif cat[2] == 'delete':
                    os.unlink(f'./new/{file}')
                    key_pressed = None
                elif cat[2] == 'quit':
                    exit()

        if key_pressed == None:
            break