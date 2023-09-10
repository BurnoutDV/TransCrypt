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

from textual.app import App, ComposeResult
from textual.widgets import Footer, Button, Static, Label, DataTable, Input, RichLog
from textual.containers import Container, Horizontal, Grid
from textual.screen import Screen

from time import monotonic
from db_util import CryptDB
from util import shorten_left_pad
from i18n import ROOi18nProvider


class MAIN(Screen):
    BINDINGS = [
        ("n", "app.new_process", "New Processing"),
        ("i", "import_json", "Import"),

    ]

    def __init__(self, i18n: ROOi18nProvider):
        super().__init__()
        self.i18n = i18n

    def compose(self) -> ComposeResult:
        yield Container (
            DataTable(id="dt_projects", zebra_stripes=True, classes="main_table"),
        )

        yield Label("Bla Fasel", id="rand_text")

        yield Footer()

    def action_import_json(self) -> None:
        self.query_one("#label_01").update(str(monotonic()))

    def _generate_datatable(self, table_id: str or DataTable) -> None:
        backend = CryptDB("transcrypts.db")
        projects = backend.list_project()
        backend.close()

        if isinstance(table_id, DataTable):
            table: DataTable = table_id
        else:
            table: DataTable = self.query_one(f"#{table_id}", DataTable)

        selected = ('uid', 'given_name', 'num_lines', 'num_speakers', 'status', 'last_change', 'file_path')
        shorten = {'file_path': 50, 'given_name': 24}

        table.add_columns(*self.i18n.translate_tuple(selected))
        for row in projects:
            one_row = []
            for col in selected:
                if col in shorten:
                    one_row.append(shorten_left_pad(row.get(col, ""), shorten[col]))
                elif col == "status":
                    one_row.append(CryptDB.status_map[row.get('status', -1)])
                else:
                    one_row.append(row.get(col, ""))
            table.add_row(*one_row)

    def on_mount(self) -> None:
        main_table = self.query_one("#dt_projects")
        main_table.cursor_type = 'row'
        self._generate_datatable(main_table)
        main_table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        event.stop()
        table: DataTable = self.query_one("#dt_projects", DataTable)
        label: Label = self.query_one("#rand_text", Label)
        row = event.cursor_row
        row_content = table.get_row_at(row)
        project_id = row_content[0]
        label.update(str(row) + " - " + str(row_content))
        self.app.push_screen(ProjectMenu(project_id, self.i18n))


class ProjectMenu(Screen):

    def __init__(self, project_id, i18n: ROOi18nProvider):
        super().__init__()
        self.project_id = project_id
        self.i18n = i18n

    def compose(self) -> ComposeResult:
        """
        IDee: tabbed bar oben, focus auf grid initial
        in tabs alle lines
        generation von zeug
        short keys bringen direkt auf tab
        """
        with Grid(id="DialogScreen", classes="dialogue-info"):
            yield Label("Summary of Project #", classes="grid_span2")
            yield Label(self.i18n.t("given_name"))
            yield Input(id="in_name", placeholder="Project Name")
            yield Label(self.i18n.t("file_path"))
            with Horizontal():
                yield Label("", id="in_path")
                yield Button("..", id="btn_relocate", classes="small_button")
            yield Label(self.i18n.t("status"))
            yield Label("", id="lbl_status")

            with Horizontal(classes="grid_span2"):
                yield RichLog(id="tl_translated", classes="grid_span2 translate-short")
            with Horizontal(classes="grid_span2"):
                yield Button(self.i18n.t("Apply"), variant="primary", id="btn_apply", classes="small_button")
                yield Button(self.i18n.t("Cancel"), variant="warning", id="btn_cancel", classes="small_button")

    def on_mount(self) -> None:
        backend = CryptDB("transcrypts.db")
        project = backend.fetch_project(self.project_id)
        lines = backend.fetch_project_lines(self.project_id, 20)
        preview = ""
        if project.get('status', 0) > 1 and len(lines) > 0:
            for each in lines:
                preview += each['content'] + "\n"
        else:
            preview = self.i18n.t("No Preview available")
        backend.close()
        self.query_one("#in_name").value = str(project['given_name'])
        self.query_one("#in_path").update(str(project['file_path']))
        self.query_one("#lbl_status").update(CryptDB.status_map[project.get('status', -1)])
        self.query_one("#tl_translated").write(preview)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.app.pop_screen()


class TCApp(App):
    """A Textual app to interface with the rest of TransCrypt"""

    CSS_PATH = "assets/textual.tcss"
    BINDINGS = [
        ("escape", "graceful_exit", "Exit"),
        ("d", "toggle_dark", "Toggle dark mode")
    ]
    SCREENS = {
        "main": MAIN(ROOi18nProvider("src/assets/i18n.json"))
    }

    def __init__(self):
        self.i18n = ROOi18nProvider("src/assets/i18n.json")
        super().__init__()

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

