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

import os
import sqlite3
import logging
import json
from datetime import datetime

from crypt_statics import db_schema

logger = logging.getLogger(__name__)


class CryptDB:

    def __init__(self, filepath: str, dummy=False):
        self.db = None
        self.cur = None
        self._open(filepath)

    def _open(self, db_path: str) -> bool:
        if not os.path.exists(db_path):
            logger.warning(f"CryptDB: db file '{db_path}' does not exist, creating one")
            self.db = sqlite3.connect(db_path)
            self.db.row_factory = sqlite3.Row  # ! changes behaviour of all future cursors
            self.cur = self.db.cursor()
            self._create_scheme()
        else:
            try:
                self.db = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
                self.db.row_factory = sqlite3.Row  # ! changes behaviour of all future cursors
                self.cur = self.db.cursor()
            except sqlite3.OperationalError as err:
                logger.error(f"CryptDB-Exception: {err}")

    def _create_scheme(self):
        for value in db_schema.values():
            try:
                self.cur.execute(value)
            except sqlite3.OperationalError as err:
                logger.error(f"CryptDB|Operation: {err}")
            except sqlite3.DataError as err:  # subclass of DB Error
                logger.error(f"CryptDB|Data: {err}")
            except sqlite3.DatabaseError as err:  # subclass of Error
                logger.error(f"CryptDB|Database: {err}")
            except sqlite3.Error as err:  # should be a catch all
                logger.error(f"CryptDB|Error: {err}")
        self.db.commit()

    def fetch_project(self, project_id: int) -> dict:  # TODO: develop project Data Transfer Object
        """
        Fetches a singular project with the exact, given unique id

        :param project_id: unique identifier for a line
        :return: a dictionary with `column_name: column_value` notation
        :rtype: dict
        """
        query = "SELECT * FROM project WHERE uid = ? LIMIT 1"
        self.cur.execute(query, (project_id,))
        row = self.cur.fetchone()
        if not row or len(row) <= 0:
            logger.error(f"CryptDB: Can not fetch project '{project_id}' because it does not exist")
            return {}
        return {key: row[key] for key in row.keys()}

    def list_project(self, limit=20, **kwargs) -> list[dict]:
        """
        fetches the fist `limit` projects and gives all informations available, additional filters possible

        :param int limit: maximum amounts of projects that get fetched
        :param **kwargs: filters
        :key max_speakers: int, maximum amount of speakers, equals 'x <= ?'
        :key min_speakers: int, minimum amount of speakers, equals 'x >= ?'
        :key speakers: int, exact number of speakers, equals 'x = ?'
        :return: a list of dictionaries that are in the format `column_name: column_value`
        :rtype: list(dict)
        """
        parameters = {
            "num_speaker": {
                "type": int,
                "alias": ("max_speaker", "min_speaker", "speaker"),
                "alias_condition": ("num_speaker <= ", "num_speaker >= ", "num_speaker = ")
            }
        }
        query = "SELECT * FROM project"
        query += " LIMIT ?"
        try:
            self.cur.execute(query, (limit, ))
            all_rows = self.cur.fetchall()
        except sqlite3.Error as err:
            logger.error(f"CryptDB: Can not list projects because: '{err}'\n Query: '{query}'")
            return []
        return [{key: row[key] for key in row.keys()} for row in all_rows]

    def fetch_line(self, line_id: int) -> dict:  # TODO: develop line DTO
        """
        Fetches a singular line with the exact, given unique id

        :param line_id: unique identifier for a line
        :return: a dictionary with `column_name: column_value` notation
        :rtype: dict
        """
        query = "SELECT * FROM line WHERE uid = ? LIMIT 1"
        self.cur.execute(query, (line_id,))
        row = self.cur.fetchone()
        if not row or len(row) <= 0:
            logger.error(f"CryptDB: Can not fetch line '{line_id}' because it does not exist")
            return {}
        return {key: row[key] for key in row.keys()}

    def fetch_project_lines(self, project_id: int, limit=500) -> list[dict]:
        """
        Fetches as many as `limit` lines belonging to a project

        :param int project_id: existing id of a project
        :param int limit: maximum number of lines per this query, default = 500
        :return: list of line dictionaries with `column_name: column_value` notation
        :rtype: list[dict]
        """
        query = "SELECT * FROM line WHERE project_id = ? LIMIT ?"
        try:
            self.cur.execute(query, (project_id, limit))
            all_rows = self.cur.fetchall()
        except sqlite3.Error as err:
            logger.error(f"CryptDB: Can not list project lines because: '{err}'")
            return []
        return [{key: row[key] for key in row.keys()} for row in all_rows]

    def fetch_speaker(self, project_id: int, speaker_id: str) -> dict:  # TODO: develop speaker DTO
        """
        Fetches a singular speaker alias row with the exact given project_id and speaker_id

        I doubt the usefulness of this function by a lot

        :param project_id: unique identifier for a specific project
        :param speaker_id: text speaker id, assigned by pyannotate
        :return: a dictionary with `column_name: column_value` notation
        :rtype: dict
        """
        query = "SELECT * FROM speaker WHERE project_id = ? and speaker_id = ? LIMIT 1"
        try:
            self.cur.execute(query, (project_id, speaker_id))
            row = self.cur.fetchone()
        except sqlite3.Error as err:
            logger.error(f"CryptDB: Can not fetch speaker 'Proj:{project_id}-{speaker_id}' because: '{err}'")
            return []
        if not row or len(row) <= 0:
            logger.error(f"CryptDB: Can not fetch speaker 'Proj:{project_id}-{speaker_id}' because it does not exist")
            return {}
        return {key: row[key] for key in row.keys()}

    def fetch_project_speaker(self, project_id:int) -> list[dict]:
        query = "SELECT * FROM speaker WHERE project_id = ?"
        try:
            self.cur.execute(query, (project_id, ))
            all_rows = self.cur.fetchall()
        except sqlite3.Error as err:
            logger.error(f"CryptDB: Can not list project speakers because: '{err}'")
            return []
        return [{key: row[key] for key in row.keys()} for row in all_rows]

    def create_project(self, **kwargs) -> int:
        """
        Creates a new transliteration project. Blank slate

        :key given_name: str, name of the project, just display usage
        :key num_speakers: int, number of detected speakers, statistics
        :key length_ms: int, length of the original audio file in milliseconds
        :key file_path: str, path to the original audio file
        :key status: int, current processing status
        :key num_lines: int, number of detected audio lines
        :key num_true_lines: int, number of detected audio lines with actual content
        :return: the uid of the newly created project
        :rtype: int
        """
        parameters = {"given_name": str, "num_speakers": int, "length_ms": int, "file_path": str,
                      "status": int, "num_lines": int, "num_true_lines": int}
        insert = {}
        for key, value in kwargs.items():
            if key in parameters:
                if isinstance(value, parameters[key]):
                    insert[key] = value
        query = "INSERT INTO project ("
        query += ", ".join(insert.keys()) + ")"
        query += " VALUES (" + ",".join(["?"] * len(insert.values())) + ")"
        #  RETURNING uid  # <-- apparently currently breaks as of 2023
        try:
            self.cur.execute(query, tuple(insert.values()))
            # row = self.cur.fetchone()  # if only RETURNING uid would work
            inserted_id = self.cur.lastrowid if self.cur.lastrowid else -1
            self.db.commit()
            return inserted_id
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: Couldn't create new project - {err}\n Query: '{query}'")
            return -1

    def update_project(self, project_id: int, **kwargs) -> bool:
        """

        :param int project_id: existing uid from the database
        :key given_name: str, name of the project, just display usage
        :key num_speakers: int, number of detected speakers, statistics
        :key length_ms: int, length of the original audio file in milliseconds
        :key file_path: str, path to the original audio file
        :key status: int, current processing status
        :key num_lines: int, number of detected audio lines
        :key num_true_lines: int, number of detected audio lines with actual content
        :return:
        """
        # check if the project actually exists
        query = "SELECT uid FROM project WHERE uid = ? LIMIT 1"
        row = self.cur.execute(query, (project_id,)).fetchone()
        if not row or len(row) <= 0:
            logger.warning(f"CryptDB: Cannot update project '{project_id}' because it does not exist")
            return False
        parameters = {"given_name": str, "num_speakers": int, "length_ms": int, "file_path": str,
                      "status": int, "num_lines": int, "num_true_lines": int}
        update = {}
        for key, value in kwargs.items():
            if key in parameters:
                if isinstance(value, parameters[key]):  # ! PyCharm insist that this isn't possible Oo
                    update[key] = value
        if len(update) <= 0:
            logger.warning(f"CryptDB: trying to update project '{project_id}' with empty data, nothing happens")
            return False
        update['last_change'] = datetime.now().isoformat(sep=" ", timespec="seconds")
        query = "UPDATE project SET "
        query += " = ?, ".join(update.keys()) + " = ?"  # * straight 6 out of 10 in terms of ugly hacks
        query += " WHERE uid = ?"
        try:
            self.cur.execute(query, (tuple(update.values()) + (project_id, )))
            self.db.commit()
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't update project - {project_id} - {err}\n Query: '{query}'")
            return False

    def create_line(self, project_id: int, speaker_id: str, **kwargs) -> int:
        """
        Creates a 'line', words spoken from a singular speaker, divided by the detection of another speaker

        :param int project_id: existing uid from the database
        :param speaker_id:
        :key content: str, actual text that was transcribed in this line
        :key length_ms: int, length in milliseconds of this line
        :key language: str, language detected by whisper, 2 letter codes like de, en, fr...
        :key start_ms: int, start of this chunk in the original audio file as milliseconds from the absolute start
        :key stop_ms: int, stop of this chunk in the original audio file as milliseconds from the absolute start
        :key previous: int, UID of the line that is logically before this one
        :key next: int, UID of the line that logically after this one
        :key sub_file_path: str, path to the temporally audio file created while processing
        :return:
        """
        # check if the project actually exists
        query = "SELECT uid FROM project WHERE uid = ? LIMIT 1"
        row = self.cur.execute(query, (project_id,)).fetchone()
        if not row or len(row) <= 0:
            logger.warning(f"CryptDB: Creating new line not possible as project ID '{project_id}' does not exist.")
            return -1
        insert = {"speaker_id": speaker_id, "project_id": project_id}
        parameters = {"content": str, "length_ms": int, "language": str, "start_ms": int, "stop_ms": int,
                      "previous": int, "sub_file_path": str}  # ,"next": int  # logically you cannot know which ID the next one got
        for key, value in kwargs.items():
            if key in parameters:
                if isinstance(value, parameters[key]):
                    if parameters[key] == int and value == -1:
                        value = None
                    insert[key] = value
        query = "INSERT INTO line ("
        query += ", ".join(insert.keys()) + ")"
        query += " VALUES (" + ",".join(["?"] * len(insert.values())) + ")"
        try:
            self.cur.execute(query, tuple(insert.values()))
            inserted_id = self.cur.lastrowid if self.cur.lastrowid else -1
            self.db.commit()
            return inserted_id
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't insert line for - {project_id} - {err}\n Query: '{query}'")
            return -1

    def create_bulk_line(self, project_id, refined_pipe: list[dict]) -> bool:
        """
        Takes a refined-pipe dictionary from the pyannotate input and creates the appropriate amount of entries

        :param int project_id: existing uid from the database
        :param refined_pipe: dictionary with keys ['start_ms', 'stop_ms', 'speaker_id']
        :return: true/false whether the operation succeded or not
        """
        query = "INSERT INTO line (project_id, start_ms, stop_ms, length_ms, speaker_id) VALUES (?, ?, ?, ?, ?)"
        speaker_set = set()
        [speaker_set.add(e['speaker_id']) for e in refined_pipe]  # comprehension abuse, yeah
        for each in speaker_set:
            self.create_speaker_id(project_id, each, "")
        try:
            self.cur.executemany(query,
                                 [(project_id,
                                  e['start_ms'],
                                  e['stop_ms'],
                                  e['stop_ms']-e['start_ms'],
                                  e['speaker_id'])
                                  for e in refined_pipe]
                                 )
            self.db.commit()
            return True
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't insert line for - {project_id} - {err}")
            return False

    def reorder_lines(self, project_id: int):
        """
        Indexes all lines of a projects and sorts them by starting time, rearranging the previous/next key

        :param int project_id: existing uid from the database
        :return:
        """
        pass

    def update_line(self, line_id: int, **kwargs) -> bool:
        """


        :param line_id: Unique ID of an existing line
        :key project_id: int, unique ID of a project TODO: check if projects exists
        :key speaker_id: str, text based ID of the speaker as detected by PyAnnote
        :key content: str, actual text that was transcribed in this line
        :key length_ms: int, length in milliseconds of this line
        :key language: str, language detected by whisper, 2 letter codes like de, en, fr...
        :key start_ms: int, start of this chunk in the original audio file as milliseconds from the absolute start
        :key stop_ms: int, stop of this chunk in the original audio file as milliseconds from the absolute start
        :key previous: int, UID of the line that is logically before this one
        :key next: int, UID of the line that logically after this one
        :key sub_file_path: str, path to the temporally audio file created while processing
        :return: bool
        """
        # check if the project actually exists
        query = "SELECT uid FROM line WHERE uid = ? LIMIT 1"
        row = self.cur.execute(query, (line_id,)).fetchone()
        if not row or len(row) <= 0:
            logger.warning(f"CryptDB: Cannot update line '{line_id}' because it does not exist")
            return False
        parameters = {"content": str, "length_ms": int, "language": str, "start_ms": int, "stop_ms": int,
                      "previous": int, "next": int, "sub_file_path": str, "speaker_id": str, "project_id": int}
        update = {}
        for key, value in kwargs.items():
            if key in parameters:
                if isinstance(value, parameters[key]):  # ! PyCharm insist that this isn't possible Oo
                    update[key] = value
        if len(update) <= 0:
            logger.warning(f"CryptDB: trying to update line '{line_id}' with empty data, nothing happens")
            return False
        query = "UPDATE line SET "
        query += " = ?, ".join(update.keys()) + " = ?"  # * straight 6 out of 10 in terms of ugly hacks
        query += " WHERE uid = ?"
        try:
            self.cur.execute(query, (tuple(update.values()) + (line_id,)))
            self.db.commit()
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't update line - {line_id} - {err}\n Query: '{query}'")
            return False

    def create_speaker_id(self, project_id: int, speaker_id: str, alias: str) -> bool:
        """
        Adds an empty speaker to the database, if this combination of project_id and speaker_id does
        not yet exists, allows to initialise with a given set of names

        :param project_id:
        :param speaker_id:
        :return:
        """
        # check for existing entry
        query = "SELECT EXISTS (SELECT uid FROM speaker WHERE project_id = ? and speaker_id = ? LIMIT 1)"
        num = self.cur.execute(query, (project_id, speaker_id)).fetchone()[0]
        if num:
            logger.warning(
                f"CryptDB: trying to create speaker '{speaker_id}' for project '{project_id}', but it exists")
            return False
        query = "INSERT INTO speaker (project_id, speaker_id, name) VALUES (?, ?, ?)"
        if not alias:
            alias = speaker_id
        try:
            self.cur.execute(query, (project_id, speaker_id, alias))
            self.db.commit()
            return True
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't insert speaker - {project_id}|{speaker_id} - {err}\n Query: '{query}'")
            return False

    def update_speaker_alias(self, project_id: int, speaker_id: str, alias: str) -> bool:
        query = "SELECT name FROM speaker WHERE project_id = ? and speaker_id = ? LIMIT 1"
        speaker_row = self.cur.execute(query, (project_id, speaker_id)).fetchone()
        if not speaker_row or len(speaker_row) <= 0:
            logger.error(f"CryptDB: Combination {project_id}|{speaker_id} does not exist, can not update")
            return False
        query = "UPDATE speaker SET name = ? WHERE project_id = ? and speaker_id = ?"
        if not alias:
            alias = speaker_id
        try:
            self.cur.execute(query, (alias, project_id, speaker_id))
            self.db.commit()
            return True
        except sqlite3.Error as err:
            logger.error(f"CryptDB|Sqlite3Error: couldn't update speaker - {project_id}|{speaker_id} - {err}\n Query: '{query}'")
            return False

    @staticmethod
    def _speaker_alias_escape(speaker_aliases: list) -> list:
        """
        Always returns a save to insert dictionary of speaker aliases

        :param list speaker_aliases: a one dimensional list of speaker
        :return: a list of names (technically a set because duplicates are eliminated)
        """
        if isinstance(speaker_aliases, str):
            return [speaker_aliases]
        elif not isinstance(speaker_aliases, list):
            return []
        return list(set(speaker_aliases))

    def _debug_import_annowhisper_json(self,
           in_file_path: str,
           original_audio_file_path: str) -> bool:
        """Imports the verbose pyannot plus whisper json output to a db file"""
        try:
            with open(in_file_path, "r") as json_file:
                raw_dict = json.load(json_file)
        except OSError as err:
            logger.error(f"CryptDB|OSError, couldnt handle file '{in_file_path}'")
            return False
        except json.JSONDecodeError as err:
            logger.error(f"CryptDB|JsonError: debug import function cannot import supposed json file '{in_file_path}' because: {err}")
            return False
        proj_id = self.create_project(given_name="Imported Project",
                                      status=4,
                                      num_lines=len(raw_dict),
                                      file_path=original_audio_file_path)
        previous = -1
        speaker_set = set()
        total_length = 0
        for each in raw_dict:
            current = self.create_line(proj_id,
                                        each.get('speaker', each.get('speaker_id', None)),
                                        start_ms=each.get('start', each.get('start_ms', None)),
                                        stop_ms=each.get('end', each.get('stop_ms', None)),
                                        sub_file_path=each['file'],
                                        content=each['transcribe']['text'],
                                        language=each['transcribe'].get('language', "un"),
                                        length_ms=each.get('end', each.get('stop_ms', None))-each.get('start', each.get('start_ms', None)),
                                        previous=previous)
            if previous > 0:
                self.update_line(previous, next=current)
            previous = current
            total_length += each.get('end', each.get('stop_ms', None))-each.get('start', each.get('start_ms', None))
            speaker_set.add(each.get('speaker', each.get('speaker_id', None)))
        for each in speaker_set:
            self.create_speaker_id(proj_id, each, "")
        self.update_project(proj_id, num_speakers=len(speaker_set), length_ms=total_length)

    def close(self):
        """
        Closes database
        :return:
        """
        if self.db:
            self.db.close()


if __name__ == "__main__":
    test = CryptDB("./transcrypt.db")
    raw = test.fetch_project(1)
    print(json.dumps(raw, indent=3))
    raw = test.list_project()
    print(json.dumps(raw, indent=3))
    rawest = test.fetch_project_lines(1, 20)
    print(json.dumps(rawest))
    print(test.fetch_project_speaker(1))
    exit()
    test._debug_import_annowhisper_json("./terrible.json", "./hunttest.wav")

    uid = test.create_project(given_name="New Project")
    #test.update_project(uid, given_name="Mein Projekt", num_lines=25)
    test.update_project(uid, num_true_lines=10, fantasy_par=12)
    test.update_project(uid, length_ms="string")
    test.update_project(uid)
    test.create_speaker_id(uid, 18)
    test.create_speaker_id(uid, 19)
    test.create_speaker_id(uid, 20)
    test.create_speaker_id(uid, 21, ["Marcel"])
    test.create_speaker_id(uid, 22, ["Marcel", "Christian"])
    test.create_speaker_id(uid, 25, ["Bernd", "Dude"])
    test.create_speaker_id(uid, 23, "Marcus")
    test.add_speaker_alias(uid, 20, "Felix")
    test.add_speaker_alias(uid, 19, ["Heinz", "Paul"])
    test.add_speaker_alias(uid, 19, ["Berbel"])
    test.add_speaker_alias(uid, 25, ["Ingrid"])
    test.add_speaker_alias(uid, 26, ["Plön", "Kevin"])
    test.create_line(uid, "SPEAKER_01", content="bla fasel")
    test.create_line(uid, "SPEAKER_02", content="mau", length_ms=1200, start_ms=500, stop_ms=650)
    test.close()