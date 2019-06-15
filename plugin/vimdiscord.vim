" Discord RPC implementation for Vim

if !has('python3')
    echo 'Compile Vim with +python3 in order to run vimdiscord'
    finish
endif

if exists('g:vimdiscord')
    finish
endif
let g:vimdiscord = 1

let s:plugin_root = fnamemodify(resolve(expand('<sfile>:p')), ':h')

function! vimdiscord#version()
    return '1.0.0'
endfunction

function! vimdiscord#run()
python3 << EOF
import os
import sys
import threading
import vim

plugin_root = vim.eval('s:plugin_root')
python_root = os.path.normpath(os.path.join(plugin_root, '..', 'python'))
sys.path.insert(0, python_root)

import plugin

connection = plugin.rpc.connect()
plugin.rpc.perform_handshake(connection, plugin.CLIENT_ID)
plugin.logger.info('Connection successfully established.')

activity = plugin.BASE_ACTIVITY
plugin.rpc.set_activity(connection, activity)
EOF
endfunction

function! vimdiscord#update()
python3 << EOF
plugin.update_presence(connection)
EOF
endfunction

function! vimdiscord#stop()
python3 << EOF
plugin.rpc.connection_closed = True
EOF
endfunction

call vimdiscord#run()

command! VimdiscordVersion call vimdiscord#version()
command! -nargs=0 UpdatePresence call vimdiscord#update()

augroup VimdiscordAutoStart
    autocmd!
    autocmd BufNewFile,BufRead,BufEnter * :call vimdiscord#update()
augroup END
