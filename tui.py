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

from textual.app import App, ComposeResult
from textual.widgets import Footer, Button, Static, Label
from textual.containers import Container, Horizontal
from textual.screen import Screen

from time import monotonic


class MAIN(Screen):
    BINDINGS = [
        ("n", "app.new_process", "New Processing"),
        ("i", "import_json", "Import"),

    ]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Label("Nothing is here for now", id="label_01"),
            Button("This is a button", id="button_01")
        )

        yield Static("This is a static")

        yield Footer()

    def action_import_json(self) -> None:
        self.query_one("#label_01").update(str(monotonic()))


class TCApp(App):
    """A Textual app to interface with the rest of TransCrypt"""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("escape", "graceful_exit", "Exit")
    ]
    SCREENS = {
        "main": MAIN()
    }

    def compose(self) -> ComposeResult:
        yield Footer()

    def action_toogle_dark(self) -> None:
        self.dark = not self.dark

    def action_new_process(self):
        self.query_one("#label_01").value = "New Process started"

    def on_mount(self) -> None:
        self.push_screen("main")

    def action_graceful_exit(self) -> None:
        """
        Shutdown with all security and normal shutdown
        :return:
        :rtype:
        """
        exit(0)

if __name__ == "__main__":
    app = TCApp()
    app.run()

