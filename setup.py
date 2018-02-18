#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import sys
from os import path
from glob import glob

name = 'urwid_datatable'
setup(name=name,
      version='0.2.0',
      description='A simple data table widget for urwid',
      author='Ton Cebzanov',
      author_email='tonycpsu@gmail.com',
      url='https://github.com/tonycpsu/urwid-datatable',
      classifiers=[
          'Environment :: Console',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Intended Audience :: Developers'],
      packages=['urwid_datatable'],
      data_files=[('share/doc/%s' % name, ['LICENSE','README.md']),
              ],
      install_requires = ["urwid", "urwid-utils", "raccoon", "orderedattrdict"]
     )
