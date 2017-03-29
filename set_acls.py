#!/usr/bin/env python2

'''
Copyright (c) 2017, Kenneth Langga (klangga@gmail.com)
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from settings import *
import argparse
import itertools
import logging
import multiprocessing
import os
import subprocess
import sys

_logger = logging.getLogger()
_LOG_LEVEL = logging.DEBUG
_CONS_LOG_LEVEL = logging.INFO
DEVNULL = open(os.devnull, 'w')
OWN_USR = 'datamanager'
OWN_GRP = 'data-managrs'
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
ACLS_CSV = os.path.join(BASE_DIR, 'acls.csv')
CPU_USAGE = .5
WORKERS = int(multiprocessing.cpu_count() * CPU_USAGE)


def _compare_tokens(fp_tokens, sp_tokens):
    match = 0
    for fp_token, sp_token in itertools.izip(fp_tokens, sp_tokens):
        if (sp_token == '*') or (fp_token == sp_token):
            match += 1
        else:
            break
    if match == len(sp_tokens) == len(fp_tokens):
        return 255
    else:
        return match


def _find_acl(full_path):
    full_path_tokens = full_path.split(os.sep)[1:]
    _logger.debug('full_path_tokens: %s', full_path_tokens)
    max_acl = ''
    max_sp = ''
    max_match = 0
    for acl, paths in sorted(ACLS.viewitems()):
        _logger.debug('#' * 80)
        _logger.debug('acl: {0}'.format(acl))
        _logger.debug('paths: {0}'.format(paths))
        for search_path in sorted(paths):
            search_path_tokens = search_path.split(os.sep)[1:]
            _logger.debug('search_path_tokens: %s', search_path_tokens)
            match = _compare_tokens(full_path_tokens, search_path_tokens)
            _logger.debug('match: %s', match)
            if match > max_match:
                max_match = match
                _logger.debug('max_match: %s', max_match)
                max_sp = search_path
                _logger.debug('max_sp: %s', max_sp)
                max_acl = acl
    return max_sp, max_acl


def _get_acl(full_path):
    # Get matching search path
    fp_tokens = full_path.replace(PREFIX, '').split(os.sep)
    _logger.debug('fp_tokens: %s', fp_tokens)
    max_sp = ''
    max_match = 0
    for search_path in sorted(SEARCH_PATHS):
        sp_tokens = search_path.split(os.sep)
        # _logger.debug('sp_tokens: %s', sp_tokens)
        match = _compare_tokens(fp_tokens, sp_tokens)
        # _logger.debug('match: %s', match)
        if match > max_match:
            max_match = match
            max_sp = search_path
    _logger.debug('max_match: %s', max_match)
    _logger.debug('max_sp: %s', max_sp)

    # Construct ACL
    buf = []
    for row in ACLS:
        if max_sp == row[0]:

            if POSIX:
                entry = []
                if row[4] == 'Yes':
                    entry.append('d')
                elif row[4] == 'No':
                    pass
                entry += row[1:3]
                if row[3] == 'read/write':
                    entry.append('rwx')
                elif row[3] == 'read/delete':
                    entry.append('rwx')
                elif row[3] == 'read only':
                    entry.append('r-x')
                if entry[0] == 'd':
                    buf.append(entry[1:])
                buf.append(entry)

            else:
                entry = row[1:3]
                if row[3] == 'read/write':
                    entry.append('rwxpD-aARWc---')
                elif row[3] == 'read/delete':
                    entry.append('r-x-Dda-R-c---')
                elif row[3] == 'read only':
                    entry.append('r-x---a-R-c---')
                if row[4] == 'Yes':
                    entry.append('fd----')
                elif row[4] == 'No':
                    entry.append('------')
                entry.append('allow')
                buf.append(entry)

    if POSIX:
        buf.append(['d', 'user', '', 'rwx'])
        buf.append(['d', 'group', '', 'rwx'])
        buf.append(['d', 'other', '', '---'])

    else:
        buf.append(['owner@', 'rwxpDdaARWcCos', 'fd----', 'allow'])
        buf.append(['group@', 'rwxpDdaARWcCos', 'fd----', 'allow'])
        buf.append(['everyone@', 'rwxpDdaARWcCos', 'fd----', 'deny'])

    acl = '\n'.join([':'.join(i) for i in buf])
    return max_sp, acl


def _get_lipad_acls(full_path, search_path, dir_acl):
    acl = []
    for l in dir_acl.split('\r\n'):
        if not 'ftp-others' in l:
            acl.append(l.strip())

    # Get username
    a = full_path.replace(PREFIX, '')
    _logger.debug('a: %s', a)
    b = a.replace(search_path, '')
    _logger.debug('b: %s', b)
    tokens = b.split(os.sep)
    _logger.debug('tokens: %s', tokens)
    username = tokens[1]
    _logger.debug('username: %s', username)

    acl.insert(0, 'd:user:' + username + ':r-x')
    acl.insert(0, 'user:' + username + ':r-x')

    return '\r\n'.join(acl)


def _apply_acl(full_path):

    root, fd = os.path.split(full_path)

    # Ignore NewFolder.py, RenameFolder.py and DeleteFolder.py
    if fd in ['NewFolder.py', 'RenameFolder.py', 'DeleteFolder.py', '.zfs']:
        return None
    if '.zfs' in root:
        return None

    # Get matching acl
    search_path, dir_acl = _get_acl(full_path)
    _logger.info('%s : %s', full_path, search_path)
    _logger.debug('dir_acl:\n%s', dir_acl)

    # Get proper lipad acls!
    if (search_path == "FTP/Others" and
            full_path != os.path.join(PREFIX,  search_path)):
        dir_acl = _get_lipad_acls(full_path, search_path, dir_acl)
        _logger.debug('lipad dir_acl:\n%s', dir_acl)

    # Use sudo if posix
    if POSIX:
        SUDO = ['sudo']
    else:
        SUDO = []

    # chown file/dir
    subprocess.call(SUDO + ['chown', OWN_USR + ':' + OWN_GRP, full_path])

    # chmod file/dir
    if os.path.isdir(full_path):
        subprocess.call(SUDO + ['chmod', '770', full_path])
    else:
        subprocess.call(SUDO + ['chmod', '660', full_path])

    # Reset acls
    subprocess.call(SUDO + ['setfacl', '-b', full_path])

    # Delete existing acls
    if not POSIX:
        while True:
            # Delete acl at position 0
            delete = subprocess.Popen(['setfacl', '-x', '0', full_path],
                                      stderr=subprocess.STDOUT,
                                      stdout=DEVNULL)
            if delete.wait() != 0:
                # Break if it can't delete anymore
                break

    # Set proper acl
    setfacl = subprocess.Popen(SUDO + ['setfacl', '-M', '-', full_path],
                               stdin=subprocess.PIPE)
    file_acl = None
    if os.path.isdir(full_path):
        setfacl.communicate(input=dir_acl)
    else:
        if POSIX:
            buf = []
            for line in dir_acl.split('\n'):
                _logger.debug('line: %s', line)
                if line.startswith('d:'):
                    buf.append(line[2:])
                else:
                    buf.append(line)
            _logger.debug('buf:\n%s', buf)
            file_acl = '\n'.join(buf)
        else:
            file_acl = dir_acl.replace(':fd', ':--')

        _logger.debug('file_acl:\n%s', file_acl)
        setfacl.communicate(input=file_acl)
    returncode = setfacl.wait()

    if returncode != 0:
        _logger.info('Error while running setfacl!')
        _logger.info('dir_acl:\n%s', dir_acl)
        _logger.info('file_acl:\n%s', file_acl)

    # Delete last acl
    if not POSIX:
        last_acl_id = str(len(dir_acl.split('\n')))
        _logger.debug(' '.join(['setfacl', '-x', last_acl_id, full_path]))
        subprocess.call(['setfacl', '-x', last_acl_id, full_path])


def _setup_logging(args):
    # Setup logging
    _logger.setLevel(_LOG_LEVEL)
    formatter = logging.Formatter('[%(asctime)s] %(filename)s \
(%(levelname)s,%(lineno)d) : %(message)s')
    # Check verbosity for console
    if args.verbose >= 1:
        global _CONS_LOG_LEVEL
        _CONS_LOG_LEVEL = logging.DEBUG
    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_CONS_LOG_LEVEL)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)


def _parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument('-fo', '--folder-only', action='store_true')
    parser.add_argument('-p', '--posix', action='store_true')
    parser.add_argument('filedir_path')
    args = parser.parse_args()
    return args


def _load_acls():
    acls = []
    search_paths = set()
    with open(ACLS_CSV, 'r') as open_file:
        first_line = True
        for line in open_file:
            # Skip first line
            if first_line:
                first_line = False
                continue
            tokens = line.strip().split(',')
            acls.append(tokens)
            search_paths.add(tokens[0])
    return acls, search_paths


if __name__ == '__main__':

    # Parse arguments
    _logger.info('Parsing arguments...')
    args = _parse_arguments()

    # Setup logging
    _setup_logging(args)

    # Check posix
    if args.posix:
        POSIX = True
    else:
        POSIX = False
    _logger.info('POSIX: %s', POSIX)

    # Load permissions from CSV and convert to ACLs
    ACLS, SEARCH_PATHS = _load_acls()

    # Get file/dir path
    filedir_path = os.path.abspath(args.filedir_path)
    _logger.info('Target path: %s', filedir_path)

    if os.path.isfile(filedir_path) or args.folder_only:

        # Process file
        _apply_acl(filedir_path)

    elif os.path.isdir(filedir_path):

        # Process dir
        _logger.info('WORKERS: %s', WORKERS)

        # Get dirs/files list
        dir_list = []
        file_list = []
        for root, dirs, files in os.walk(filedir_path):

            _logger.info('%s', root)
            dir_list.append(root)
            file_list += [os.path.join(root, filename) for filename in files]

        # Initialize pool
        pool = multiprocessing.Pool(processes=WORKERS)

        # Apply ACLs to folders 1st
        dir_procs = pool.map_async(_apply_acl, dir_list)
        dir_procs.wait()

        # Apply ACLs to files next
        file_procs = pool.map_async(_apply_acl, file_list)
        file_procs.wait()

        pool.close()

    else:
        _logger.error("%s doesn't exist! Exiting.", filedir_path)
        exit(1)
