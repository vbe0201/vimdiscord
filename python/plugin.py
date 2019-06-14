import logging
import time
import vim

import rpc

logger = logging.getLogger()

START_TIME = int(time.time())

BASE_ACTIVITY = {
    'details': 'Idle',
    'timestamps': {
        'start': START_TIME
     },
    'assets': {
        'large_text': 'Vim',
        'large_image': 'vim_logo',
        'small_text': 'The one true editor',
        'small_image': 'vim_logo'
     }
 }

CLIENT_ID = '589111267986243624'

has_thumbnail = [
    'html',
    'css',
    'js',
    'php',
    'scss',
    'py',
    'rs',
    'c',
    'h',
    'cpp',
    'hpp',
    'cxx',
    'cc',
    'cs',
    'java',
    'ex',
    'md',
    'ts',
    'go',
    'kt',
    'kts',
    'cr',
    'rb',
    'clj',
    'hs',
    'json',
    'vue',
    'groovy',
    'swift',
    'lua',
    'jl',
    'dart',
]


def get_filename():
    return vim.eval('expand("%:t")')


def get_extension():
    return vim.eval('expand("%:e")')


def get_cwd():
    return vim.eval('getcwd()')


def run(connection):
    while not rpc.connection_closed:
        time.sleep(10)

        activity = BASE_ACTIVITY
        filename = get_filename()
        cwd = get_cwd()
        if not filename or not cwd:
            continue
    
        activity['details'] = 'Editing ' + get_filename()
        activity['assets']['small_text'] = 'Working on project ' + get_cwd()

        if get_extension() and get_extension() in has_thumbnail:
            activity['assets']['large_image'] = get_extension()
        else:
            activity['assets']['large_image'] = 'unknown'

        try:
            rpc.set_activity(connection, activity)
            time.sleep(10)
        except NameError:
            logger.error('Discord is not running!')
            break
        except BrokenPipeError:
            logger.error('Connection to Discord lost!')
            break

    rpc.close(connection)
