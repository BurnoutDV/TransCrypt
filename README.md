# TransCrypt

I like puns. Anyway, this is another project that i will probably never finish.

## What it should do

When sitting in a meeting and you somehow, magically get to an audio recording of the whole thing you usually cannot really do anything with that recording unless you listen to the whole thing again. You can transcribe audio just fine but thats not enough. I tried [Vosk](https://alphacephei.com/vosk/) and wasn't very impressed. Using [Whisper](https://openai.com/research/whisper) yielded better results, but both models have the downside that you only get a raw transcript, without context and who said what. For that you need something called [speaker diarisation](https://en.wikipedia.org/wiki/Speaker_diarisation). Apparently not something achievable by normal, non-ML means. The goods news is..we have that now with [PyAnnotate](https://pypi.org/project/pyannotate/)

So here is what I do..or rather like to do:

1. Take an input `audio file` and throw *PyAnnotate* on that
2. Transform the raw data to some workable format, then use [PyDub](https://github.com/jiaaro/pydub) to cut up the original audio file in chunks separated by speaker
3. Use whisper on the list of short audio chunks
4. Use some human intelligence to properly label the speaker
5. Create something that is similar to a stage script for the meeting

As of now I got Steps 1 to 3 down and tested step 5. I actually created some logic to save that up in an SQLite database. I know what an ORM is and wrote my SQL Queries anyways.

## What i envision

I want to use [Textual](https://github.com/Textualize/textual) for something actual useful, thinking about how some of those transcription processes are actually slow (well, not really, on my *RTX 3080* is somewhat speedy) it might be useful to have a TUI to use via SSH when having a beefy GPU else place.

## But why

Because I can. Simply as that, i haven't even looked to deeply into this but i am sure there are commercial solutions and some cloud stuff other people have cobbled together. But this runs on my PC (although you need to download the models via Hugging Face and an API Key)

## Installation

There is a setup.py, that should get you started, but I noticed that PyAnnotate and Whisper want different PyTorch Versions, I found an overlap version that works for both but for now I have polished up the requirements to nail that down.

You will always need a hugging face api key for the PyAnnotate Model which has to be placed in a plain text fail named `hugging_api_key`.

### Bias

Whisper apparently was trained by sub titles of various public broadcasting institutes, those tend to have copyright info in the silence at the end or beginning, that problem is [known](https://github.com/openai/whisper/discussions/928) I took the liberty and compiled those biases into `dataset_bias.json` I am totally open for Pull Requests on that one.