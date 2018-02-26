from setuptools import setup, find_packages
import os

HERE = os.path.abspath(os.path.dirname(__file__))


def get_description():
    README = os.path.join(HERE, 'README')
    f = open(README, 'r')
    try:
        return f.read()
    finally:
        f.close()


def main():
    setup_args = dict(
        name='debian_packager',
        version='1.0.6',
        author='Roman Shuvalov',
        author_email='rshuvalov@abtronics.ru',
        description='deb package creation utility',
        long_description=get_description(),
        url='http://abtronics.ru',
        packages=find_packages('.'),
        package_dir={'': '.'},
        package_data={},
        install_requires=[],
        platforms='linux',
        license='MIT',
    )
    setup(**setup_args)

if __name__ == '__main__':
    main()