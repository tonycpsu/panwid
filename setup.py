#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys
from os import path
from glob import glob

name = 'panwid'
setup(name=name,
      version='0.1.0',
      description='Useful widgets for urwid',
      author='Tony Cebzanov',
      author_email='tonycpsu@gmail.com',
      url='https://github.com/tonycpsu/panwid',
      classifiers=[
          'Environment :: Console',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Intended Audience :: Developers'
      ],
      packages=find_packages(),
      data_files=[('share/doc/%s' % name, ['LICENSE','README.md']),
              ],
      install_requires = ["urwid", "urwid-utils"],
      extras_require = {
          "datatable": ["raccoon", "blist", "orderedattrdict"],
      }
     )
