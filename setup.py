#!/usr/bin/env python
# coding: utf-8

# Copyright 2021 by BurnoutDV, <development@burnoutdv.com>
#
# This file is part of SantonianCrawler.
#
# SantonianCrawler is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# SantonianCrawler is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>

from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='TransCrypt',
    version='0.2',
    description='A bunch of scripts to use PyAnnotate and Whisper to transcribe meeting notes and similar stuff',
    long_description=long_description,
    license="GPLv3",
    python_requires=">=3.9",  # if not for a single random walrus operator it would probably work with 3.4 or so
    author='BurnoutDV',
    author_email='development@burnoutdv.com',
    packages=['TransCrypt'],
    install_requires=['textual', 'whisper', 'torch', 'pydub'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "Operating System :: OS Independent",
        "License :: GPLv3",
        "License :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: German",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Topic :: System :: Archiving",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Terminals",
        "Topic :: Utilities"
    ]
)