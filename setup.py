# -*- coding: utf-8 -*-
from distutils.core import setup
from glob import glob

PACKAGE_NAME = 'minescrubber'
PACKAGE_VERSION = '0.4'

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description='The classic game of minesweeper',
    author='Alok Gandhi',
    author_email='alok.gandhi2002@gmail.com',
    url='https://github.com/alok1974/minescrubber',
    packages=[
        'minescrubber',
        'minescrubber.resources',
    ],
    package_data={
        'minescrubber': ['*.py'],
        'minescrubber.resources': ['*.png', '*.css', '*.ttf'],
    },
    package_dir={
        'minescrubber': 'src/minescrubber'
    },
    scripts=glob('src/scripts/*'),
    install_requires=[
        'minescrubber_core>=0.4',
        'PySide2>=5.15.0',
        'shiboken2>=5.15.0',
        'Pillow>=7.2.0'
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment :: Board Games',
        'License :: OSI Approved :: MIT License',
    ],
)
