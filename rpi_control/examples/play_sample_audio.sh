#!/bin/bash
# Script to demonstrate how to use speaker_control.py with a sample audio file

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
fi

# Create a sample audio file if it doesn't exist
SAMPLE_WAV="sample_tone.wav"

if [ ! -f "$SAMPLE_WAV" ]; then
    echo "Creating sample audio file: $SAMPLE_WAV"
    # Generate a 3-second 440Hz tone
    ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -c:a pcm_s16le -ar 44100 "$SAMPLE_WAV"
fi

# Play the sample audio file
echo "Playing sample audio file using speaker_control.py..."
python speaker_control.py --file "$SAMPLE_WAV"

echo "Done!"
