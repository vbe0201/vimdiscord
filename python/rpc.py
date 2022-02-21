import enum
import json
import logging
import os
import socket
import sys
import struct
import uuid

import plugin
logger = logging.getLogger(__name__)
logger.setLevel(20)

connection_closed = True

ON_WINDOWS = sys.platform == 'win32'
PIPE_PATH = R'\\?\pipe\discord-ipc-{}' if ON_WINDOWS else R'discord-ipc-{}'

class Opcodes(enum.Enum):
    HANDSHAKE = 0
    FRAME = 1
    CLOSE = 2
    PING = 3
    PONG = 4


def _write(connection, data):
    if connection is not None:
        if ON_WINDOWS:
            connection.write(data)
            connection.flush()
        else:
            connection.sendall(data)


def _receive(connection, size):
    if connection is not None:
        if ON_WINDOWS:
            return connection.read(size)
        else:
            return connection.recv(size)


def _receive_exactly(connection, size):
    if connection is not None:
        buffer = b''
        while size:
            chunk = _receive(connection, size)
            buffer += chunk
            size -= len(chunk)

        return buffer


def _receive_header(connection):
    if connection is not None:
        return struct.unpack('<II', _receive_exactly(connection, 8))


def _get_pipe_path(i):
    env_keys = ('XDG_RUNTIME_DIR', 'TMPDIR', 'TMP', 'TEMP', 'run')
    for key in env_keys:
        dir_path = os.environ.get(key)
        if dir_path:
            break
    else:
        dir_path = '/tmp'

    return os.path.join(dir_path, PIPE_PATH.format(i))


def send(connection, data, op=Opcodes.FRAME):
    if connection is not None:
        data = json.dumps(data, separators=(',', ':'))
        data = data.encode('utf-8')
        logger.debug('Sending %s', data)
        header = struct.pack('<II', op.value, len(data))

        _write(connection, header)
        _write(connection, data)


def receive(connection):
    if connection is not None:
        op, length = _receive_header(connection)
        payload = _receive_exactly(connection, length)
        data = json.loads(payload.decode('utf-8'))

        logger.debug('Received %s', data)
        return op, data


def send_receive(connection, data, op=Opcodes.FRAME):
    send(connection, data, op)
    return receive(connection)


def set_activity(connection, activity):
    data = {
        'cmd': 'SET_ACTIVITY',
        'args': {'pid': os.getpid(), 'activity': activity},
        'nonce': str(uuid.uuid4())
    }

    send(connection, data)


def connect():
    global connection_closed

    if not connection_closed:
        return

    logger.debug('Attempting to connect to Discord RPC...')

    if not ON_WINDOWS:
        _socket = socket.socket(socket.AF_UNIX)

    for i in range(10):
        if ON_WINDOWS:
            path = PIPE_PATH.format(i)

            try:
                pipe = open(path, 'wb')
            except OSError:
                pass
            else:
                connection_closed = False
                return pipe
        else:
            path = _get_pipe_path(i)

            if not os.path.exists(path):
                continue

            try:
                _socket.connect(path)
            except OSError:
                pass
            else:
                connection_closed = False
                return _socket
    #print(path)
    plugin.logger.info('Failed to establish a connection to DiscordRPC')
    pass
    #raise RuntimeError('Failed to establish a connection to Discord RPC.')


def perform_handshake(connection, client_id):
    if connection is not None:
        op, data = send_receive(connection, {'v': 1, 'client_id': client_id}, Opcodes.HANDSHAKE)
        if op == Opcodes.FRAME.value and data['cmd'] == 'DISPATCH' and data['evt'] == 'READY':
            return
        else:
            if op == Opcodes.CLOSE.value:
                close(connection)

            raise RuntimeError(data)


def close(connection):
    if connection is not None:

        global connection_closed

        logger.debug('Closing connection.')
        try:
            send(connection, {}, Opcodes.CLOSE)
        finally:
            connection.close()
            connection_closed = True
