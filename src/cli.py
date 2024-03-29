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

import sys
import logging
import json
import os
import argparse

import torch
import whisper

import util
from db_util import CryptDB

logging.basicConfig(filename='TransCrypt.log', format='[%(asctime)s] %(levelname)s:%(message)s', level=logging.INFO)


def save_dict_as_json(filepath: str, data):
    with open(filepath, "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=3)


def cli_process_plain(audio_file: str,
                      out_file: str,
                      temp_folder="./temp/",
                      language="de",
                      silent=False,
                      bias_file="dataset_bias.json"):
    speakers = {
        "SPEAKER_00": "Max",
        "SPEAKER_01": "Moritz",
        "SPEAKER_02": "Werner"
    }

    biases = None
    if not silent:
        print("TransCrypt - This process might take a while")
        print(f"Chosen file is '{audio_file}'")
        print("Continue? (y/N)")
        user_in = input()
        if user_in != "y":
            exit(1)
    logging.info(f"Input file '{audio_file}', language={language}, temp_folder='{temp_folder}'")

    # attempting biases
    if os.path.exists(bias_file):
        with open(bias_file, "r", encoding="utf-8") as bias_fh:
            biases = json.load(bias_fh)
    # retrieve API Key
    with open("hugging_api_key", "r") as key_file:
        api_key = key_file.read()
    logging.info("Calling pyannote")
    raw_pipetxt = util.create_pipelinetxt(audio_file, api_key)
    save_dict_as_json("Crypt001-rawpipe.json", raw_pipetxt)
    logging.info(f"PyAnnote done - {len(raw_pipetxt)} -> refining (converting in a useable list)")
    refined = util.pipelinetxt2dict(raw_pipetxt)
    save_dict_as_json("Crypt002-refined.json", refined)
    logging.info(f"Refinement done - {len(refined)} entries, found: {len(util.piped_speakers(refined))} Speakers")
    enriched = util.speech_parts(audio_file, refined, temp_folder)
    save_dict_as_json("Crypt003-enriched.json", enriched)
    logging.info(
        "Created temp files for each singular line, this might be many, calling whisper now, embrace your GPU Ram!")
    diamonds = util.transcribe_enriched(enriched, "medium", language)
    save_dict_as_json("Crypt004-diamond.json", diamonds)
    logging.info("Transcription done, saving up raw data now")
    with open("last_run.json", "w", encoding="utf-8") as raw_json:
        json.dump(diamonds, raw_json, indent=2)
    dialogue = util.create_stage_script(diamonds, speakers, biases=biases.get(language, None))
    with open(out_file, "w", encoding="utf-8") as txt_file:
        txt_file.writelines(dialogue)
    logging.info("Process finished")


def cli_process_db(audio_file: str,
                   language=None,
                   temp_folder="./temp/",
                   silent=False,
                   bias_file="assets/dataset_bias.json",
                   model_size="medium",
                   db_file="transcrypts.db"):
    """Tries to utilise database for processing"""
    biases = None
    if not silent:
        print("TransCrypt - This process might take a while")
        print(f"Chosen file is '{audio_file}'")
        print("Continue? (y/N)")
        user_in = input()
        if user_in != "y":
            exit(1)
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info(f"Input file '{audio_file}', language={language}, temp_folder='{temp_folder}'")
    # attempting biases
    if bias_file:
        if os.path.exists(bias_file):
            with open(bias_file, "r", encoding="utf-8") as bias_fh:
                try:
                    biases = json.load(bias_fh)
                    logging.info(f"Loaded BIASES from '{bias_file}'")
                except json.JSONDecodeError as err:
                    logging.warning(f"Couldnt load biases - {err}")
                    biases = None
        else:
            logging.warning(f"Bias file '{bias_file}' got entered but cannot be found")
    # retrieve API Key
    with open("hugging_api_key", "r") as key_file:
        api_key = key_file.read()
    # * Creating DB
    backend = CryptDB(db_file)
    p_id = backend.create_project(file_path=str(audio_file), status=0)
    logging.info("Calling pyannote")
    raw_pipetxt = util.create_pipelinetxt(audio_file, api_key)
    # TODO: save up raw annotate files for whatever reason
    logging.info(f"PyAnnote done - {len(raw_pipetxt)} -> refining (converting in a useable list)")
    refined = util.pipelinetxt2dict(raw_pipetxt)
    lines = len(refined)
    num_speaker = len(util.piped_speakers(refined))
    # TODO: get the actual length of the file
    backend.update_project(p_id, num_speaker=num_speaker, status=1, num_lines=lines)
    logging.info(f"Refinement done - {lines} entries, found: {num_speaker} Speakers")
    backend.create_bulk_line(p_id, refined)
    # this step is a bit illogical because we just gave all the data IN the database, now we
    # extract it again to get the proper line_ids
    db_pipe = backend.fetch_project_lines(p_id, 99999)
    check = util.speech_parts(audio_file, db_pipe, temp_folder, backend)

    if not check:
        return False
    # don't like this part
    db_pipe = backend.fetch_project_lines(p_id, 99999)
    logging.info(
        "Created temp files for each singular line, this might be many, calling whisper now, embrace your GPU Ram!")

    devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = whisper.load_model(model_size, device=devices)

    for each in db_pipe:
        crypt = util.transcribe_line(each, model, language)
        if crypt:
            backend.update_line(each['uid'],
                                content=each['transcribe']['text'],
                                language=each['transcribe'].get('language', "un"))
            # TODO: delete file after processing and reference in db
    backend.update_project(p_id, status=2)


def continue_from_refined(project_id: int, temp_folder, language):
    logging.info(f"Trying to continue a project, ID: {project_id}")
    backend = CryptDB("transcrypts.db")
    project = backend.fetch_project(project_id)
    if project['status'] != 1:
        logging.warning(f"Can not continue {project_id} because its in the wrong status")
        return False
    db_pipe = backend.fetch_project_lines(project_id, 99999)
    check = util.speech_parts(project['file_path'], db_pipe, temp_folder, backend)
    if not check:
        return False
    # don't like this part
    db_pipe = backend.fetch_project_lines(project_id, 99999)
    logging.info(
        "Created temp files for each singular line, this might be many, calling whisper now, embrace your GPU Ram!")

    devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = whisper.load_model("medium", device=devices)

    for each in db_pipe:
        crypt = util.transcribe_line(each, model, language)
        if crypt:
            backend.update_line(each['uid'],
                                content=each['transcribe']['text'],
                                language=each['transcribe'].get('language', "un"))
            # TODO: delete file after processing and reference in db
    backend.update_project(project_id, status=3)


def cli():
    """
    Put argparse here Alan
    """
    parser = argparse.ArgumentParser(
        description="TransCrypt - a frankensteined transcription tool",
        usage="%(prog)s -i WAVFILE.wav -o TRANSCRIPT.txt")
    # all the things she said..or arguments we had
    parser.add_argument("-t", "--textui", action="store_true",
                        help="starts the text user interface (ignores all other parameters)")
    parser.add_argument("-db", "--databasepath", type=str, default="transcrypts.db",
                        help="Path and name to the SQLite file used for operations")
    processings = parser.add_mutually_exclusive_group()
    processings.add_argument("-i", "--input", type=str, help="Input file, preferably .wav")
    processings.add_argument("-r", "--resume", type=int,
                        help="continues the given project_id if there is something to continue in that project")
    parser.add_argument("-o", "--output", type=str, help="theater style script with default names")
    parser.add_argument("--timestamps", action="store_true", help="adds timestamps in script")
    parser.add_argument("--modelsize", type=str, help="size of the whisper model", default="medium")
    parser.add_argument("--language", type=str,
                        help="two character language code for whisper, by default it will try to figure it out")
    parser.add_argument("--biases", type=str, default="./assets/dataset_bias.json",
                        help="json files with biases for specific languages")
    parser.add_argument("--tempfolder", type=str, default="./temp/",
                        help="Manually defines folder for temporary audiofiles")


    args = parser.parse_args()

    print(args)

    if args.textui or (not args.input and not args.resume):
        from tui import TCApp  # <- I googled a bit around, and it seems to be okay in this specific case
        app = TCApp()
        app.run()

    if args.input:
        params = {
            "audio_file": str(args.input)
        }
        if args.biases:
            params['bias_file'] = str(args.biases)
        if args.tempfolder:
            params['temp_folder'] = str(args.tempfolder)
        if args.language:
            params['language'] = str(args.language)
        if args.modelsize:
            params['model_size'] = str(args.modelsize)
        if args.output:
            params['out_file'] = str(args.output)
            cli_process_plain(**params)
        else:
            cli_process_db(**params)


if __name__ == "__main__":
    cli()
    #continue_from_refined(2, ".\\temp\\", "de")
