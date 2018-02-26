# -*- coding: utf-8 -*-
"""
Main configuration module
.. moduleauthor: rshuvalov@abtronics.ru (Roman Shuvalov)
"""
import os
import shutil
import re
import debian
import settings


def setup(files, name, **kwargs):
    """Options and parameters for packaging
    Path is considered as package/module if it is directory and contains __init__.py file in root
    it will be installed in python dist-packages

    Note: as of now, support only binary package distribution. Source distribution may come later

    :param name: package name
    :type name: string
    :param files: list of file/dirs/packages
    path tuples (install_from_path, install_to_path, options) to package
    install_from_path is relative to script and install_to_path is absolute from system root
    or package name alone for python modules/packages
    :type files: list
    :param kwargs: package options
    :return: void
    """
    # Start parse parameters
    props = {}
    # common
    props['name'] = re.sub('[\W]', '', name.lower())
    props['version'] = kwargs.get('version', '1.0')
    props['architecture'] = architecture = kwargs.get('architecture', 'all')
    if architecture not in settings.allowed_architecture:
        raise SystemExit(
            'Error: {} is not allowed architecture, allowed: {}'\
            .format(architecture, ', '.join(settings.allowed_architecture))
        )
    props['maintainer'] = kwargs.get('maintainer', 'UNKNOWN')
    props['maintainer_email'] = kwargs.get('maintainer_email', 'UNKNOWN')
    provides = kwargs.get('provides', [])
    props['provides'] = ', '.join(provides)
    props['section'] = section = kwargs.get('section', 'misc')
    if section not in settings.allowed_section:
        raise SystemExit(
            'Error: {} is not allowed section, allowed: {}'.format(section, ', '.join(settings.allowed_section))
        )
    props['description'] = kwargs.get('description', 'UNKNOWN')
    props['short_description'] = kwargs.get('short_description', 'UNKNOWN')
    # dependencies
    props['python_depends'] = kwargs.get('python_depends', [])  # Python specific modules required for package
    props['depends'] = ', '.join(kwargs.get('depends', []))
    props['python_major_version'] = kwargs.get('python_major_version', 2)
    props['predepends'] = ', '.join(kwargs.get('predepends', []))
    props['conflict'] = ', '.join(kwargs.get('conflict', []))
    props['replaces'] = ', '.join(kwargs.get('replaces', []))
    props['recommends'] = ', '.join(kwargs.get('recommends', []))
    props['suggests'] = ', '.join(kwargs.get('suggests', []))
    if architecture == 'source':
        builddepends = ', '.join(kwargs.get('builddepends', []))
    else:
        builddepends = ''
    props['builddepends'] = builddepends
    # package specific
    props['priority'] = priority = kwargs.get('priority', 'optional')
    if priority not in settings.allowed_priority:
        raise SystemExit(
            'Error: {} is not allowed priority, allowed: {}'.format(priority, ', '.join(settings.allowed_priority))
        )
    props['essential'] = kwargs.get('essential', False)  # Essential packages cannot be uninstalled
    props['origin'] = kwargs.get('origin', None)  # Package origin
    props['xsource'] = kwargs.get('xsource', None)  # Full path for source download
    props['watch'] = kwargs.get('watch', '')
    props['autostart'] = kwargs.get('autostart', [])
    # changelog specific
    props['changelog_file'] = kwargs.get('changelog_file', None)
    # install specific shell extensions to be included in appropriate pre/post install/remove scripts
    props['preinstall_ext_sh'] = kwargs.get('preinstall_ext_sh', [])
    props['postinstall_ext_sh'] = kwargs.get('postinstall_ext_sh', [])
    props['preremove_ext_sh'] = kwargs.get('preremove_ext_sh', [])
    props['postremove_ext_sh'] = kwargs.get('postremove_ext_sh', [])
    # End parse parameters

    # Build path
    if not os.path.exists(settings.build_path):
        os.makedirs(settings.build_path)
    if not os.path.exists(settings.debian_path):
        os.makedirs(settings.debian_path)
    # Purge conffiles content
    conffiles_location = os.path.join(settings.debian_path, 'conffiles')
    if os.path.exists(conffiles_location):
        with open(conffiles_location, 'wr+') as f:
            f.write('')
    # End Build path

    # Finding files and python packages
    for f in files:
        try:
            path_from, path_to = f
            path_from = os.path.join(settings.local_path, path_from)
            if '/man' in path_to:
                manpage_type = ''.join(re.findall('\.([\d]+)$', os.path.basename(path_from)))
                debian.manpage(path_from, int(manpage_type))
                continue
            final_destination_path = copy_files(path_from, path_to)
            if '/etc' in path_to:
                debian.add_to_conffiles(final_destination_path.replace(settings.build_path, '', 1))
            if '/bin' in path_to:
                debian.set_executable(final_destination_path)
        except ValueError:
            package = f
            copy_package(package)
        # Process file copy to build directory
    # Create .desctop autostart configs
    for programm in props['autostart']:
        pname, pcommand = programm
        debian.autostart(pname, pcommand, **props)
    # End Finding files and python packages

    # Creating debian files
    debian.control(**props)
    debian.changelog(**props)
    # debian.compat()  # not used in binary distribution
    debian.install_scripts(**props)
    debian.copyright(**props)
    debian.watch(**props)
    debian.md5sum()
    # End Creating debian files

    # Build package
    p = debian.make_binary_package(**props)
    lintian_out, lintian_err = debian.test_binary_package(p)
    # End Build package

    lintian_expected_success_out = (
        'N: Using profile ubuntu/main.\n'
        'N: Setting up lab in /tmp/temp-lintian-lab-XXXXXXXXXXXX ...\n'
        'N: Unpacking packages in group observer/1.3.0-systemd\n'
        'N: ----\n'
        'N: Processing binary package observer (version 1.3.0-systemd, arch all) ...\n'
    )

    # Finish
    if (len(lintian_out) - len(lintian_expected_success_out)) <= 10 and lintian_err is None:
        print 'Building finished successfully'
        clear_build_directory()
        print 'Build directory cleared'
    else:
        print 'Building finished. Please review lintian report.'
        print lintian_out
        print lintian_err


def clear_build_directory():
    """"""
    for the_file in os.listdir(settings.build_path):
        file_path = os.path.join(settings.build_path, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Error while clearing build directory')
            print(e)


def copy_files(path_from, path_to):
    """copy files from location to build folder

    :param path_from: os path to copy from
    :param path_to:  os path to install location, will be placed under /build root
    :return: void
    """
    if not os.path.exists(path_from):
        print 'Warning: {} don\'t exist!'.format(path_from)
        return False
    build_path_to = ''.join([settings.build_path, path_to])
    print 'copying {} to {}'.format(path_from, build_path_to)
    try:
        if os.path.isdir(path_from):
            shutil.copytree(path_from, build_path_to)
        else:
            if not os.path.exists(os.path.dirname(build_path_to)):
                os.makedirs(os.path.dirname(build_path_to))
            shutil.copy(path_from, build_path_to)
        return os.path.join(build_path_to, os.path.basename(path_from))
    except OSError, e:
        raise SystemExit(e)


def copy_package(name):
    """Copy package or module by name.
    Will copy only .py files.

    :param name: package name, or module path
    :return: void
    """
    name = name.split('.')
    pacakge_path = os.path.join(settings.local_path, *name)
    for dirpath, dirnames, filenames in os.walk(pacakge_path):
        if '__init__.py' not in filenames:
            dirname = ''.join(re.findall('/([^/]*)$', dirpath)).strip()
            print 'Warning: {} not a python package or module'.format(dirname)
            continue

        for filename in filenames:
            if not filename.endswith('py'):
                continue
            path_from = os.path.join(dirpath, filename)
            dpath = dirpath.replace(settings.local_path, '', 1)
            path_to = ''.join([settings.python_package_path, dpath, '/', filename])
            copy_files(path_from, path_to)
