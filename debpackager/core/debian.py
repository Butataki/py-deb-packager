"""
debian/* specific files creation module
.. moduleauthor: rshuvalov@abtronics.ru (Roman Shuvalov)
"""
import os
import datetime
from settings import build_path, debian_path, local_path
import subprocess
import re
import gzip


def get_size(start_path='.'):
    """path size in bytes

    :param start_path: path for size calculation
    :return: int
    """
    dir_size = 4100  # 4,1 Kb for unix system
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        total_size += dir_size
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size + 1024  # reserve 1Kb


def get_standarts_versions():
    """Get version of debian-policy standarts used to build

    :return: version string
    """
    cmd_call = 'apt-cache show debian-policy'.split()
    res = subprocess.Popen(cmd_call, stdout=subprocess.PIPE)
    out, err = res.communicate()
    version = str(''.join(re.findall('Version: ([\d\.]+)', out)))
    return version


def control(**kwargs):
    """Create debian/control file

    :param kwargs: .. module:core.setup parsed key arguments
    :return: void
    """
    file_path = os.path.join(debian_path, 'control')
    size = int(get_size(build_path) / 1024)
    content = []
    # main
    content.append('Package: {}'.format(kwargs['name']))
    content.append('Version: {}'.format(kwargs['version']))
    content.append('Provides: {}'.format(kwargs['provides']) if kwargs['provides'] else '')
    content.append('Maintainer: {} <{}>'.format(kwargs['maintainer'], kwargs['maintainer_email']))
    content.append('Architecture: {}'.format(kwargs['architecture']))
    content.append('Section: {}'.format(kwargs['section']))
    content.append('Description: {}'.format(kwargs['description']))
    # content.append('Standards-Version: {}'.format(get_standarts_versions()))  # Used in source distribution
    # dependencies
    content.append('Depends: {}'.format(kwargs['depends']) if kwargs['depends'] else '')
    content.append('Pre-Depends: {}'.format(kwargs['predepends']) if kwargs['predepends'] else '')
    content.append('Conflicts: {}'.format(kwargs['conflict']) if kwargs['conflict'] else '')
    content.append('Replaces: {}'.format(kwargs['replaces']) if kwargs['replaces'] else '')
    content.append('Recommends: {}'.format(kwargs['recommends']) if kwargs['recommends'] else '')
    content.append('Suggests: {}'.format(kwargs['suggests']) if kwargs['suggests'] else '')
    content.append('Build-Depends: {}'.format(kwargs['builddepends']) if kwargs['builddepends'] else '')
    # extra
    content.append('Installed-Size: {}'.format(size))
    content.append('Priority: {}'.format(kwargs['priority']))
    if kwargs['essential']:
        content.append('Essential: {}'.format('yes' if kwargs['essential'] else 'no'))
    content.append('Origin: {}'.format(kwargs['origin']) if kwargs['origin'] else '')
    content.append('X-Source: {}'.format(kwargs['xsource']) if kwargs['xsource'] else '')
    # user defined
    content = filter(len, content)
    content.append('')  # control file must always contain empty last string
    content = '\n'.join(content)
    with open(file_path, 'wr+') as f:
        f.write(content)


def changelog(**kwargs):
    """Creates debian/changelog or update it

    :param kwargs: .. module:core.setup parsed key arguments
    :return: void
    """
    content = ''
    location_org = os.path.join(local_path, kwargs['changelog_file'])
    if os.path.exists(location_org):
        with open(location_org, 'r') as f:
            content = f.read()
    location_dir = os.path.join(build_path, 'usr/share/doc/{}'.format(kwargs['name']))
    location = os.path.join(location_dir, 'changelog.gz')
    location_debian = os.path.join(location_dir, 'changelog.Debian.gz')
    if not os.path.exists(location_dir):
        os.makedirs(location_dir)
    with gzip.open(location, 'wb') as f:
        f.write(content)
    with gzip.open(location_debian, 'wb') as f:
        f.write(content)


def compat():
    """create compat(comparability) file

    :return: void
    """
    cmd_call = 'dpkg -p debhelper'.split()
    res = subprocess.Popen(cmd_call, stdout=subprocess.PIPE)
    out, err = res.communicate()
    content = str(''.join(re.findall('Version: ([\d]+)', out)))
    location = os.path.join(debian_path, 'compat')
    with open(location, 'wr+') as f:
        f.write(content)


def parse_sh_file(sh_file):
    location = os.path.join(local_path, sh_file)
    if not os.path.exists(location):
        print '{} not found'.format(sh_file)
    with open(location, 'r') as f:
        content = f.read()
    content = re.sub('(\#\![\s]*/bin/[\w]+\n)', '', content)
    return content


def install_scripts(**kwargs):
    """Generate debian/preinst, debian/postinst, debian/prerm, debian/postrm installation/removing scripts

    :param kwargs: .. module:core.setup parsed key arguments
    :return: void
    """
    # Error logging for installation scripts
    error_traping_template = """#!/bin/bash
set -e # fail on any error
set -u # treat unset variables as errors

# ======[ Trap Errors ]======#
set -E # let shell functions inherit ERR trap

# Trap non-normal exit signals:
# 1/HUP, 2/INT, 3/QUIT, 15/TERM, ERR
trap err_handler 1 2 3 15 ERR
function err_handler {{
    local exit_status=${{1:-$?}}
    logger -s -p "syslog.err" -t "{tag}" "{package} script '$0' error code $exit_status (line $BASH_LINENO: '$BASH_COMMAND')"
    exit $exit_status
}}

{body}

exit 0
    """

    # Forming debian/preinst
    # Install all python required packages
    body_preinst = """"""
    # Add python requirements installation
    if len(kwargs['python_depends']) > 0:
        for package in kwargs['python_depends']:
            body_preinst += "pip{} install {}\n".format(kwargs['python_major_version'], package)
    # add extensions body
    if len(kwargs['preinstall_ext_sh']) > 0:
        for sh in kwargs['preinstall_ext_sh']:
            body_preinst += parse_sh_file(sh) + '\n'
    location_preinst = os.path.join(debian_path, 'preinst')
    with open(location_preinst, 'wr+') as f:
        f.write(error_traping_template.format(tag=kwargs['maintainer'], package=kwargs['name'], body=body_preinst))
    os.chmod(location_preinst, 0755)
    #
    # Forming debian/postinst
    body_postinst = """"""
    # add extensions body
    if len(kwargs['postinstall_ext_sh']) > 0:
        for sh in kwargs['postinstall_ext_sh']:
            body_postinst += parse_sh_file(sh) + '\n'
    location_postinst = os.path.join(debian_path, 'postinst')
    with open(location_postinst, 'wr+') as f:
        f.write(error_traping_template.format(tag=kwargs['maintainer'], package=kwargs['name'], body=body_postinst))
    os.chmod(location_postinst, 0755)
    #
    # Forming debian/prerm
    body_prerm = """"""
    # add extensions body
    if len(kwargs['preremove_ext_sh']) > 0:
        for sh in kwargs['preremove_ext_sh']:
            body_prerm += parse_sh_file(sh) + '\n'
    location_prerm = os.path.join(debian_path, 'prerm')
    with open(location_prerm, 'wr+') as f:
        f.write(error_traping_template.format(tag=kwargs['maintainer'], package=kwargs['name'], body=body_prerm))
    os.chmod(location_prerm, 0755)
    #
    # Forming debian/postrm
    body_postrm = """"""
    # add extensions body
    if len(kwargs['postremove_ext_sh']) > 0:
        for sh in kwargs['postremove_ext_sh']:
            body_postrm += parse_sh_file(sh) + '\n'
    location_postrm = os.path.join(debian_path, 'postrm')
    with open(location_postrm, 'wr+') as f:
        f.write(error_traping_template.format(tag=kwargs['maintainer'], package=kwargs['name'], body=body_postrm))
    os.chmod(location_postrm, 0755)
    #


def make_binary_package(**kwargs):
    """Execute dpkg-deb build command

    :param kwargs: .. module:core.setup parsed key arguments
    :return: pacakge name
    """
    package = '{name}_{version}_{architecture}.deb'.format(
        name=kwargs['name'], version=kwargs['version'], architecture=kwargs['architecture']
    )
    cmd_call = 'fakeroot dpkg-deb --build {} {}'.format(build_path, package).split()

    res = subprocess.Popen(cmd_call, stdout=subprocess.PIPE)
    out, err = res.communicate()
    print out, err
    return package


def test_binary_package(package):
    """Autotest created package

    :param package: package to test
    :return: void
    """
    cmd_call = 'lintian -Ivi {} '.format(package).split()
    res = subprocess.Popen(cmd_call, stdout=subprocess.PIPE)
    out, err = res.communicate()
    return out, err


def add_to_conffiles(filepath):
    """Append filename to conffile controlling file

    :param filepath: path to file in /etc, note, that file path is local to build directory
    :return: void
    """
    location = os.path.join(debian_path, 'conffiles')
    content = filepath + '\n'
    if os.path.exists(location):
        with open(location, 'a') as f:
            f.write(content)
    else:
        with open(location, 'wr+') as f:
            f.write(content)


def manpage(manpage_file, manpage_type):
    """Copy man page for binary file
    manpage types:
    1 - User Commands
    2 - System Calls
    3 - C Library Functions
    4 - Devices and Special Files
    5 - File Formats and Conventions
    6 - Games et. Al.
    7 - Miscellanea
    8 - System Administration tools and Deamons


    :param manpage_file: manpage file path
    :param manpage_type: 1 for man1, 2 for man2 etc.
    :type manpage_type: int
    :return: void
    """
    if not os.path.exists(manpage_file):
        print '{} not found!'.format(manpage_file)
        return
    name = os.path.basename(manpage_file)
    with open(manpage_file, 'r') as f:
        content = f.read()
    location = os.path.join(build_path, 'usr/share/man', 'man{}/'.format(manpage_type))
    if not os.path.exists(location):
        os.makedirs(location)
    location = os.path.join(location, name + '.gz')
    with gzip.open(location, 'wr+') as f:
        f.write(content)


def set_executable(filepath):
    """Make file executable by everyone

    :param filepath: path to file in /bin, note, that file path must to be absolute
    :return: void
    """
    st = os.stat(filepath)
    os.chmod(filepath, st.st_mode | 0111)


def md5sum():
    call = 'md5sum {}'
    location = os.path.join(debian_path, 'md5sums')
    with open(location, 'wr+') as f:  # empty current md5sum file or create new
        f.write('')
    for dirpath, dirnames, filenames in os.walk(build_path):
        for filename in filenames:
            if 'DEBIAN' in dirpath:  # DEBIAN md5 sums is omitted at installation anyway
                continue
            res = subprocess.Popen(call.format(os.path.join(dirpath, filename)).split(), stdout=subprocess.PIPE)
            out, err = res.communicate()
            md5 = ''.join(re.findall('(^[^\s]*)', out))
            content = '{md} {path}\n'\
                .format(md=md5, path=os.path.join(dirpath, filename).replace(build_path + '/', '', 1))
            with open(location, 'a') as f:
                f.write(content)


def copyright(**kwargs):
    """created copyright file with MIT licence
    NOTE: support for per file/dir copyright/license type maybe included later
    NOTE: support for several authors maybe included later
    NOTE: support for years maybe included later

    :param kwargs: .. module:core.setup parsed key arguments
    :return: void
    """
    location = os.path.join(build_path, 'usr/share/doc/{}/'.format(kwargs['name']))
    location = os.path.join(location, 'copyright')
    print location
    with open(location, 'wr+') as f:  # empty current copyright file or create new
        f.write('')
    content = """Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {name}
Upstream-Contact: {maintainer_name} <{maintainer_email}>
Source: {xsource}


Files: *
Copyright:
    {year}, {maintainer_name}
License: MIT

Files: debian/*
Copyright:
    {year}, {maintainer_name}
License: MIT

License: MIT
    Copyright (c) {year} {maintainer_name}

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "{name}"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
    and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions
    of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
    TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
""".format(
        name=kwargs['name'],
        maintainer_name=kwargs['maintainer'],
        maintainer_email=kwargs['maintainer_email'],
        xsource=kwargs['xsource'],
        year=datetime.datetime.now().strftime('%Y')
    )
    with open(location, 'wr+') as f:
        f.write(content)


def watch(**kwargs):
    if len(kwargs['watch']) == 0:
        return
    location = os.path.join(debian_path, 'watch')
    content = """version=3

{}
    """.format(kwargs['watch'])
    with open(location, 'wr+') as f:
        f.write(content)


def autostart(app_name, app_command, **kwargs):
    location_org = 'etc/xdg/autostart/'
    location = os.path.join(build_path, location_org)
    if not os.path.exists(location):
        os.makedirs(location)
    location = os.path.join(location, '{}.desktop'.format(app_name))
    content = """[Desktop Entry]
Encoding=UTF-8
Version={version}
Name={name}
Comment={description}
Exec={c}
Terminal=false
Type=Application
StartupNotify=false
Terminal=false
    """.format(
        version=kwargs['version'],
        name=app_name,
        description=kwargs['short_description'],
        c=app_command
    )
    with open(location, 'wr+') as f:
        f.write(content)
    add_to_conffiles(os.path.join('/' + location_org, '{}.desktop'.format(app_name)))
