#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys
from os import path
from glob import glob

name = 'panwid'
setup(name=name,
      version='0.3.5',
      description='Useful widgets for urwid',
      author='Tony Cebzanov',
      author_email='tonycpsu@gmail.com',
      url='https://github.com/tonycpsu/panwid',
      python_requires='>=3.6',
      classifiers=[
          'Environment :: Console',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Intended Audience :: Developers'
      ],
      packages=find_packages(),
      data_files=[('share/doc/%s' % name, ['LICENSE','README.md']),
              ],
      install_requires=[
          "urwid",
          "urwid-utils >= 0.1.2",
          "six",
          "raccoon >= 3.0.0",
          "orderedattrdict",
          "urwid_readline ~= 0.13"
      ],
      test_suite="test",
      # dependency_links=[
      #     "https://github.com/tonycpsu/urwid_utils/tarball/master#egg=urwid_utils-0.0.5dev"
      # ],
     )
