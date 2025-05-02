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

# Instead of local playback, use MCPHardwareClient if available
try:
    from unitmcp import MCPHardwareClient
    USE_UNITMCP = True
except ImportError:
    USE_UNITMCP = False

def play_wav(file_path):
    print(f"Playing WAV file: {file_path}")
    wave_obj = sa.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def play_mp3(file_path):
    print(f"Playing MP3 file: {file_path}")
    audio = AudioSegment.from_mp3(file_path)
    pydub_play(audio)

async def is_server_active(host, port, timeout=2):
    import asyncio
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def play_remote(file_path):
    from dotenv import load_dotenv
    import base64
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    RPI_HOST = os.getenv('RPI_HOST', 'localhost')
    RPI_PORT = int(os.getenv('RPI_PORT', '8080'))
    if not await is_server_active(RPI_HOST, RPI_PORT):
        print(f"ERROR: No MCP server running at {RPI_HOST}:{RPI_PORT}. Start the server and try again.")
        return
    client = MCPHardwareClient(RPI_HOST, RPI_PORT)
    await client.connect()
    ext = os.path.splitext(file_path)[1].lower()[1:]
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    params = {"audio_data": audio_b64, "format": ext}
    print(f"Sending playAudio command for {file_path} to {RPI_HOST}:{RPI_PORT}")
    try:
        result = await client.send_request("audio.playAudio", params)
        if result.get("status") == "audio_played":
            print("Audio playback started successfully on remote device.")
        else:
            print(f"Failed to start remote audio playback: {result}")
    except Exception as e:
        print(f"Error during remote audio playback: {e}")
    await client.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Speaker control example: play WAV or MP3 file on remote device.")
    parser.add_argument('--file', '-f', required=True, help='Path to .wav or .mp3 file to play')
    parser.add_argument('--remote', action='store_true', help='Play audio on remote device using MCP')
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    if args.remote and USE_UNITMCP:
        import asyncio
        asyncio.run(play_remote(args.file))
        return

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
