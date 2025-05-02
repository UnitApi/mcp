import os
import sys
import argparse
import time

try:
    import simpleaudio as sa
except ImportError:
    print("simpleaudio not found, trying to install...")
    os.system(f"{sys.executable} -m pip install simpleaudio")
    import simpleaudio as sa

try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
except ImportError:
    print("pydub not found, trying to install...")
    os.system(f"{sys.executable} -m pip install pydub")
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play

def play_wav(file_path):
    print(f"Playing WAV file: {file_path}")
    wave_obj = sa.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def play_mp3(file_path):
    print(f"Playing MP3 file: {file_path}")
    audio = AudioSegment.from_mp3(file_path)
    pydub_play(audio)

def main():
    parser = argparse.ArgumentParser(description="Speaker control example: play WAV or MP3 file on remote device.")
    parser.add_argument('--file', '-f', required=True, help='Path to .wav or .mp3 file to play')
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    ext = os.path.splitext(args.file)[1].lower()
    if ext == '.wav':
        play_wav(args.file)
    elif ext == '.mp3':
        play_mp3(args.file)
    else:
        print("Unsupported file type. Please provide a .wav or .mp3 file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
