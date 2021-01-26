import os
import sys
import gc
import _thread
import time


_keep_running = False
_lock = _thread.allocate_lock()
__version__ = '1.0.0'

print('esp32_control_file.py version:', __version__)


def _gc_loop(*_, **__):
    print('gc thread started')

    _lock.release()
    while _keep_running:
        time.sleep(0.5)
        gc.collect()

    print('gc thread stopped')
    _lock.release()


def run_esp_32_control():
    global _keep_running

    if _keep_running is False:
        _keep_running = True
        print('starting gc thread')
        _lock.acquire()

        _thread.start_new_thread(_gc_loop, (), {})

        _lock.acquire()
        _lock.release()


def stop_esp32_control():
    global _keep_running
    print('stopping gc thread')
    _lock.acquire()

    _keep_running = False

    _lock.acquire()
    _lock.release()


def _split(path):
    return path.split('/')


def _splitext(path):
    path = _split(path)
    if '.' in path[-1]:
        path[-1], ext = path[-1].rsplit('.', 1)
        ext = '.' + ext
    else:
        ext = ''

    path = _join(path)

    return path, ext


def _convert_path(path):
    path = path.replace('\\', '/')
    return path.strip().strip('/')


def _join(*args):
    return '/'.join(args)


def _isdir(path):
    try:
        os.listdir(path)
        return True
    except OSError:
        return False


def _exists(path):
    if _isdir(path):
        return True
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def remove_tree(path):
    path = _convert_path(path)
    print('**removing_tree**' + path)
    for f in os.listdir(path):
        f = _join(path, f)
        if _isdir(f):
            remove_tree(f)
        else:
            os.remove(f)
            print('**remove_file**' + f)

    os.rmdir(path)
    print('**remove_tree**' + path)


def remove_file(path):
    path = _convert_path(path)
    os.remove(path)
    print('**remove_file**' + path)


def make_dir(path):
    path = _convert_path(path)
    os.mkdir(path)
    print('**make_dir**' + path)


def make_dirs(path):
    path = _convert_path(path)
    os.makedirs(path)
    print('**make_dirs**' + path)


def is_dir(path):
    path = _convert_path(path)
    if _isdir(path):
        print('**is_dir**True*' + path)
    else:
        print('**is_dir**False*' + path)


def exists(path):
    path = _convert_path(path)
    if _exists(path):
        print('**exists**True*' + path)
    else:
        print('**exists**False*' + path)


def remove_dir(path):
    path = _convert_path(path)
    os.rmdir(path)
    print('**remove_dir**' + path)


def dir_contents(path):
    path = _convert_path(path)
    for f in os.listdir(path):
        stat = os.stat(_join(path, f))

        if _isdir(_join(path, f)):
            f += '*' + str(stat[8]) + '<dir>'
        else:
            f += '*' + str(stat[8]) + '*' + str(stat[6])

        print(f)

    print('**dir_contents**' + path)


make_file = None


def make_file_open(path, overwrite):
    global make_file

    path = _convert_path(path)
    if not overwrite and _exists(path):
        print('**make_file_open err**' + path)
        return

    make_file = open(path, 'wb')
    print('**make_file_open**' + path)


def make_file_write(data):
    make_file.write(data)
    print('**make_file_write**')


def make_file_close():
    global make_file
    make_file.close()
    make_file = None
    print('**make_file_close')


def move_file(src, dst, overwrite):
    src = _convert_path(src)
    dst = _convert_path(dst)

    if not overwrite and _exists(dst):
        print('**move_file err**' + dst)
        return

    with open(src, 'rb') as f1:
        with open(dst, 'wb') as f2:
            f2.write(f1.read())

    remove_file(src)
    print('**move_file**' + dst)


def copy_file(src, dst, overwrite):
    src = _convert_path(src)
    dst = _convert_path(dst)

    if not overwrite and _exists(dst):
        print('**copy_file err**' + dst)
        return

    with open(src, 'rb') as f1:
        with open(dst, 'wb') as f2:
            f2.write(f1.read())

    print('**copy_file**' + dst)


def move_tree(src, dst, merge):
    src = _convert_path(src)
    dst = _convert_path(dst)

    if not merge and _exists(dst):
        print('**move_tree err**' * dst)
        return

    if not _exists(dst):
        make_dir(dst)

    for f in os.listdir(src):
        f_src = _join(src, f)
        f_dst = _join(dst, f)
        if _isdir(f_src):
            move_tree(f_src, f_dst, merge)
        else:
            if _exists(f_dst):
                f_dst, ext = _splitext(f_dst)
                count = 1
                f_dst += '(1)' + ext
                while _exists(f_dst):
                    f_dst = f_dst.rreplace('(' + str(count) + ')', '(' + str(count + 1) + ')', 1)
                    count += 1

            copy_file(f_src, f_dst, False)

    remove_tree(src)
    print('**move_tree**' + dst)


def rename(src, dst):
    src = _convert_path(src)
    dst = _convert_path(dst)

    if _exists(dst):
        print('**rename err**' + dst)
        return

    os.rename(src, dst)
    print('**rename**' + dst)


def download_file(path):
    path = _convert_path(path)
    size = os.stat(path)[6]
    bytes_read = 0
    data = ' ' * 32

    with open(path, 'rb') as f:
        while bytes_read < size:
            data = f.read(32)
            bytes_read += len(data)
            sys.stdout.write(data.decode('utf-8'))

    print('**preview_file**' + path)


preview_file = download_file
