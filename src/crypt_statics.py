#!/usr/bin/env python
# coding: utf-8
# Copyright 2021 by BurnoutDV, <development@burnoutdv.com>
#
# This file is part of TransCrypt.
#
# TransCrypt is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# TransCrypt is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>

db_schema = {}
# project is more or less a sole statistic
db_schema['project'] = """CREATE TABLE IF NOT EXISTS project (
                        uid INTEGER PRIMARY KEY AUTOINCREMENT,
                        given_name TEXT,
                        num_speakers INTEGER,
                        length_ms INTEGER,
                        file_path TEXT,
                        status INTEGER,
                        num_lines INTEGER,
                        num_true_lines INTEGER,
                        last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );"""
db_schema['line'] = """CREATE TABLE IF NOT EXISTS line (
                        uid INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER REFERENCES project(uid),
                        speaker_id TEXT NOT NULL,
                        content TEXT,
                        sub_file_path TEXT,
                        length_ms INTEGER,
                        language TEXT,
                        start_ms INTEGER,
                        stop_ms INTEGER,
                        previous INTEGER REFERENCES line(uid),
                        next INTEGER REFERENCES line(uid)
                        );"""
db_schema['speaker'] = """CREATE TABLE IF NOT EXISTS speaker (
                        uid INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER REFERENCES project(uid),
                        speaker_id TEXT NOT NULL,
                        name TEXT NOT NULL
                        );"""

if __name__ == "__name__":
    print("This is a static config file, dont execute it please, you are scaring the bits and bytes.")
