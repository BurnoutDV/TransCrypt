#!/usr/bin/env python
# coding: utf-8

import re
import logging
from pathlib import PurePath

from pydub import AudioSegment
from whisper import Whisper

from db_util import CryptDB



logger = logging.getLogger(__name__)


def single_out_speaker(audiofile: str, piped_list: list[dict], speaker: str, out_file: str):
    raw_audio = AudioSegment.from_file(audiofile, "wav")
    raw_audio.set_frame_rate(44100)
    new_audio = AudioSegment.silent(0, 44100)
    logger.debug(f"Speaker is {speaker}")
    last_segment = 0
    for i, each in enumerate(piped_list, start=1):
        if each['speaker_id'] == speaker:
            silence = each['start_ms']-last_segment
            logger.debug(f"{speaker} found [{each['start']}:{each['stop_ms']}] - {len(raw_audio[each['start_ms']:each['stop_ms']])} - {silence}ms Silence")
            new_audio += AudioSegment.silent(duration=silence, frame_rate=44100)
            new_audio += raw_audio[each['start_ms']:each['stop_ms']]
            last_segment = each['stop_ms']
        if i == len(piped_list):  # last round
            # putting silence till the end of the file
            if last_segment < each['stop_ms']:
                silence = each['stop_ms'] - last_segment
                new_audio += AudioSegment.silent(duration=silence, frame_rate=44100)
                logger.debug(f"adding {silence}ms of end silence")
    logger.debug(f"Done - {len(new_audio)}")
    new_audio.export(out_file, format="wav")


def _detect_audio(file_path: str) -> str:
    """
    Simply assigns a file path by file extension, no fancy mime types

    :param file_path: absolute or relative file path
    :return: file type: mp3, wav, ogg, flac, 3gp, aac
    """
    pure = str(PurePath(file_path).suffix).lower()
    formats = {"mp3": "mp3", "wav": "wav", "wave": "wav", "ogg": "ogg", "opus": "ogg",
               "flac": "flac", "3gp": "3gp", "aac": "aac", "ac3": "aac", "mp4": "aac"}
    return formats.get(pure, "wav")


def speech_parts(main_audiofile: str,
                 piped_list: list[dict],
                 sub_folder=".\\temp\\",
                 db_handler=None) -> list[dict]:
    """
    Creates an audio file for each instance of speech found by PyAnnote

    :param main_audiofile:
    :param piped_list:
    :param sub_folder:
    :param CryptDB db_handler: handler for database entry
    :return:
    """
    try:
        raw_audio = AudioSegment.from_file(main_audiofile, _detect_audio(main_audiofile))
        raw_audio.set_frame_rate(44100)
    except FileNotFoundError as err:
        logger.error(f"Util.SpeechParts: can not open audio file: {main_audiofile} - {err}")
        return []

    enriched_piped_list = []
    for i, each in enumerate(piped_list, start=1):
        new_audio = raw_audio[each['start_ms']:each['stop_ms']]
        #  TODO: change this, its insane as it is
        file_export_name = f"{sub_folder}{main_audiofile}_{i}.wav"
        if db_handler and isinstance(db_handler, CryptDB) and 'uid' in each:
            db_handler.update_line(each['uid'], sub_file_path=file_export_name)
        new_audio.export(file_export_name, "wav")
        enriched_piped_list.append({
            "start_ms": each['start_ms'],
            "stop_ms": each['stop_ms'],
            "speaker_id": each['speaker_id'],
            "sub_file_path": file_export_name
        })
    return enriched_piped_list


def create_stage_script(finalized_piped_list: list[dict], names_map: dict, biases=None):
    # simplest form
    output = []
    for each in finalized_piped_list:
        clear = cleanup_transcript(each['transcription'], biases)
        if clear:
            output.append(f"[{names_map.get(each['speaker_id'], each['speaker_id'])}]: {clear}\n")
    return output


def cleanup_transcript(input_txt: str, biases=None):
    trimmed = input_txt.strip()
    if biases:
        for bias in biases:
            if trimmed == bias:
                return ""
    return trimmed


def transcribe_enriched(enriched_piped_list: list[dict], model="medium", language="en"):
    """
    This uses the GPU..or CPU, but big time in any case. I really hate this because it uses some model it will
    download from somewhere and just do magic stuff, but without this it wouldnt work half as well.

    What it does is using whisper and torch to transcribe the temporary files created be enriched pipe

    :param enriched_piped_list: the list[dict] created by util.speech_parts
    :param str model:
    :return:
    """
    import torch
    import whisper

    devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = whisper.load_model(model, device=devices)

    for each in enriched_piped_list:
        result = model.transcribe(each['sub_file_path'], language=language)
        logger.debug(result)
        each['transcription'] = str(result['text'])
        each['transcribe'] = result

    return enriched_piped_list


def transcribe_line(line: dict, model: Whisper, language="en") -> dict:
    """
    Takes a singular 'line' dictionary as input, only relevant part is the 'file' path,
    everything else just gets passed along

    :param dict line:
    :param Whisper model: loaded Whisper model
    :param str language: optional language specifier, default "en"
    :return: the same line dictionary but with 'transcribe' and 'transcription' as additional
    keys, the first containing all whisper json data, the latter just the transcribed text
    """
    result = model.transcribe(line['sub_file_path'], language=language)
    logger.debug(result)
    line['transcription'] = str(result['text'])
    line['transcribe'] = result
    return line  # as its a dict it should already be updated by reference


def _unspecific_timestring_to_mill(time: str):
    """
    Takes a string of the format '00:00:07.095' to become time in milliseconds
    :param time:
    :return:
    """
    spl = time.split(":")
    s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
    return s


def create_pipelinetxt(audio_file, auth_token):
    """
    This uses your CPU/GPU for torch neuronal network stuff and also torch under the hood. Its even worse than
    whisper because it will use some pretrained model we just obtain "somehow" via the internet. You actually
    need an API key for this, dont worry, if you do not have one, it will tell you about it, loud.

    :param audio_file:
    :param auth_token:
    :return:
    """
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization',
                                        use_auth_token=auth_token, cache_dir="model")
    one_file = {
        'uri': "notnecessary",
        'audio': audio_file
    }
    pipe_txt = pipeline(one_file)

    return str(pipe_txt)


def pipelinetxt2dict(inputblock: str, mode=0) -> list[dict]:
    """
    Transforms the output of pyannote pipeline into something one can work with

    I really don't know why I have to do this, shouldn't there already be a function that does this for me?

    :param str inputblock: a block of cheese..or the output of pyannote
    :param int mode: if 0 millisecond timings, else string times will be used
    :return: list of dictionary with three keys: start, end, speaker
    """
    pattern = r"\[\s([0-9]+:[0-9]+:[0-9]+\.[0-9]+)\s-->\s\s([0-9]+:[0-9]+:[0-9]+\.[0-9]+)\]\s+.+(SPEAKER_[0-9]+)"

    lines = inputblock.split("\n")
    many_words = []
    for each in lines:
        groupos = re.search(pattern, each)
        if len(groupos.regs) == 4:
            f = groupos.regs
            start = each[f[1][0]:f[1][1]]
            end = each[f[2][0]:f[2][1]]
            if mode == 0:
                start = _unspecific_timestring_to_mill(start)
                end = _unspecific_timestring_to_mill(end)
            words = {
                "start_ms": start,
                "stop_ms": end,
                "speaker_id": each[f[3][0]:f[3][1]]
            }
            many_words.append(words)
    return many_words


def piped_speakers(piped_list: list[dict]) -> list:
    """
    Just "counts" the unique names inside the given pipeline list

    :param list piped_list: list with dictionaries in it
    :return: list of speakers
    """

    speakers = set()
    for each in piped_list:
        speakers.add(each.get("speaker_id", None))
    return list(speakers)


if __name__ == "__main__":
    print("Testing functionality...")
    defo = """[ 00:00:01.240 -->  00:00:03.062] A SPEAKER_00
[ 00:00:04.514 -->  00:00:05.661] B SPEAKER_00
[ 00:00:06.674 -->  00:00:07.095] CI SPEAKER_01
[ 00:00:08.057 -->  00:00:08.884] CJ SPEAKER_01
[ 00:00:09.610 -->  00:00:16.950] CK SPEAKER_01
[ 00:00:16.950 -->  00:00:20.325] C SPEAKER_00
[ 00:00:23.127 -->  00:00:23.194] D SPEAKER_00
[ 00:00:23.194 -->  00:00:35.985] CL SPEAKER_01
[ 00:00:35.327 -->  00:00:36.998] E SPEAKER_00"""
    one_list = pipelinetxt2dict(defo)
    print(str(one_list))
    print(str(piped_speakers(one_list)))
