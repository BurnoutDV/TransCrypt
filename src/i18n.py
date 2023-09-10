#!/usr/bin/env python
# coding: utf-8
# Copyright 2023 by BurnoutDV, <development@burnoutdv.com>
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

"""
There is probably somewhere a proper i18n utility that is way more sophisticated, but this works
"""

import json
from pathlib import PurePath


class ROOi18nProvider:
    DEFAULT_LANGUAGE = "en"  #  fallback

    def __init__(self, language_file: str or PurePath, language="en"):
        """


        :param language_file str or PurePath:
        :param language str: language as ISO code
        """
        self.active = False
        self.language = language
        self._repo = {"en": {}}
        if self.load_from_json(language_file):
            self.active = True

    def load_from_json(self, filepath: str):
        try:
            with open(filepath, "r") as json_object:
                correct_json = json.load(json_object)
                self._repo = correct_json
        except OSError as err:
            return None
        except json.JSONDecodeError as err:
            return None
        return True

    def t(self, token: str, language=None, fallback=None):
        """
        shorthand for translate

        :param token: language translation token
        :param language: manual override for language other than class default
        :param fallback: fallback language in case main language yields no result
        :return:
        """
        return self.translate(token, language, fallback)

    def translate(self, token: str, language=None, fallback=None):
        """
        translates a single token from the local repository

        :param token: language translation token
        :param language: manual override for language other than class default
        :param fallback: fallback language in case main language yields no result
        :return:
        """
        if not self.active:
            return token
        if not language:
            language = self.language
        if language in self._repo and token in self._repo[language]:
            return self._repo[language][token]
        elif fallback and fallback in self._repo and token in self._repo[fallback][token]:
            return self._repo[fallback][token]
        elif ROOi18nProvider.DEFAULT_LANGUAGE in self._repo and token in self._repo[ROOi18nProvider.DEFAULT_LANGUAGE]:
            return self._repo[ROOi18nProvider.DEFAULT_LANGUAGE][token]
        else:
            return token

    def translate_set(self, data: set, language=None, fallback=None):
        """
        Expects a set of only strings {[str], [str], [str], ...}

        :param data:
        :param language: manual override for language other than class default
        :param fallback: fallback language in case main language yields no result
        :return:
        """
        return set(self.translate_list(list(data), language, fallback))

    def translate_tuple(self, data: tuple, language=None, fallback=None):
        """
        Expects a tuple of only strings ([str], [str], [str], ...)

        :param data:
        :param language: manual override for language other than class default
        :param fallback: fallback language in case main language yields no result
        :return:
        """
        return tuple(self.translate_list(list(data), language, fallback))

    def translate_list(self, data: list, language=None, fallback=None):
        """
        Expects a list of only string [str, str, str, str, ...]

        :param data:
        :param language: manual override for language other than class default
        :param fallback: fallback language in case main language yields no result
        :return:
        """
        new_list = []
        for each in data:
            new_list.append(self.translate(each, language, fallback))
        return new_list

    def transEsc(self, token: str, language=None, fallback=None):
        """
        Escapes translation

        :param token:
        :return:
        """
        return self.translate(token, language, fallback)
