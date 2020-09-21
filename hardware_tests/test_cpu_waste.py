"""
Produces load on all available CPU cores
"""
from multiprocessing import Pool
from multiprocessing import cpu_count

def f(x):
    while True:
        x*x

if __name__ == '__main__':
    processes = 1   # cpu_count() (usually 4)
    print('-' * 20)
    print('Running load on CPU')
    print('Utilizing %d cores' % processes)
    print('-' * 20)
    pool = Pool(processes)
    pool.map(f, range(processes))
