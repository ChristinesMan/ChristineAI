import os
import wave
import numpy as np

import pitch

files = os.listdir('.')

for file in files:

    p = pitch.find_pitch(file)
    pz = str(int(p)).zfill(5)
    print(f'./{file} has pitch {pz}')

    os.rename(file, f'{pz}_{file}')