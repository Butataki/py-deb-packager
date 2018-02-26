# -*- coding: utf-8 -*-
"""
settings options for build
.. moduleauthor: rshuvalov@abtronics.ru (Roman Shuvalov)
"""
import sys
import os
allowed_architecture = ['i386', 'amd64', 'all', 'source']
allowed_section = ['admin', 'base', 'comm', 'contrib', 'devel', 'doc', 'editors', 'electronics', 'embedded', 'games',
                   'gnome', 'graphics', 'hamradio', 'interpreters', 'kde', 'libs', 'libdevel', 'mail', 'math', 'misc',
                   'net', 'news', 'non-free', 'oldlibs', 'otherosfs', 'perl', 'python', 'science', 'shells', 'sound',
                   'tex', 'text', 'utils', 'web', 'x11']
allowed_priority = ['extra', 'optional', 'standard', 'important', 'required']
python_path = sys.path
local_path = python_path[0]
build_path = os.path.join(local_path, 'build')
debian_path = os.path.join(build_path, 'DEBIAN')
core_path = os.path.dirname(os.path.abspath(__file__))
python_package_path = ''
for path in python_path:
    if path.endswith('packages') and 'local' not in path:
        python_package_path = path
if len(python_package_path) == 0:
    raise SystemExit('Error: cannot find appropriate pacakge location in sys path')
print local_path, python_package_path
