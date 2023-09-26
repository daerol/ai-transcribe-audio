import openai
import flask
import os
import openai
import math
import glob

from pydub import AudioSegment
from pydub.utils import mediainfo
from pydub.utils import make_chunks
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
 
openai.api_key = os.getenv("OPENAI_API_KEY")
DIRECTORY = os.getenv("DIRECTORY") or str(Path.cwd())


def create_audio_chunk(file):
    file_name = os.path.basename(file)
    file_name_without_extension = file_name.split(".")[0]
    file_name_extension = file_name.split(".")[1]

    if not os.path.exists(DIRECTORY+"/"+file_name):
        # Create a directory with the name of the file
        os.mkdir(DIRECTORY+"/"+file_name_without_extension)
        # Create a directory for the preprocessed audio
        os.mkdir(DIRECTORY+"/"+file_name_without_extension+"/preprocessed")

    # Convert the audio to wav
    convert_to_wav(file_name_without_extension, file_name_extension)

    # Get the preprocessed audio converting from m4a to wav
    preprocessed_audio = AudioSegment.from_file(DIRECTORY + "/"+ file_name_without_extension +"_preprocessed.wav", "wav")
    directory_with_audio = DIRECTORY + "/"+ file_name_without_extension +"_preprocessed.wav"
    directory_for_preprocessed_audio = DIRECTORY + "/"+ file_name +"/preprocessed/"

    # Get the audio file properties
    channel_count = preprocessed_audio.channels  
    sample_width = preprocessed_audio.sample_width 
    duration_in_sec = len(song) / 1000 #Length of audio in sec
    sample_rate = song.frame_rate
    bit_rate = int(mediainfo(directory_with_audio)['bits_per_sample'])

    # Calculate the total bytes of audio
    wav_file_size = (sample_rate * bit_rate * channel_count * duration_in_sec) / 8


    # 24Mb OR 24, 000, 000 bytes
    file_split_size = 24000000
    total_chunks =  wav_file_size // file_split_size

    #in sec
    chunk_length_in_sec = math.ceil((duration_in_sec * 24000000 ) /wav_file_size)
    chunk_length_ms = chunk_length_in_sec * 1000
    chunks = make_chunks(song, chunk_length_ms)

    for i, chunk in enumerate(chunks):
        chunk_name = file_name + "_processed_chunk_{0}.wav".format(i)
        print("exporting", chunk_name)
        chunk.export(directory_for_preprocessed_audio + chunk_name, format="wav")

    create_transcript(chunks, directory_for_preprocessed_audio, file_name_without_extension)

def convert_to_wav(d, ext):
    # d for directory, ext for extension
    existing_audio = AudioSegment.from_file(d, ext)
    existing_audio.export(DIRECTORY+"/"+ file_name +"_preprocessed.wav", format="wav")


def check_file_exist(file):
    if os.path.exists(file):
        os.remove(file)

def create_transcript(chunks, d, file_name_without_extension):
    concat_string = ""
    for i, chunk in enumerate(chunks):
        file_name = file_name_without_extension + "_processed_chunk_{0}.wav".format(i)
        audio_file = open(d +  file_name, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        concat_string += " " + transcript.text

    with open(DIRECTORY+"/"+ file_name_without_extension +"/"+ file_name_without_extension_transcript +".txt", "w") as f:
        f.write(concat_string)


if __name__ == "__main__":
    for file in glob.glob(DIRECTORY+"/audio/*.m4a"):
        create_audio_chunk(file)