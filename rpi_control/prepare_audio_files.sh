#!/bin/bash
set -e
EXAMPLES_DIR="$(dirname "$0")/examples"
cd "$EXAMPLES_DIR"

# Generate sample_tone.wav if missing
audio_file="sample_tone.wav"
if [ ! -f "$audio_file" ]; then
    echo "Generating $audio_file..."
    ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -c:a pcm_s16le -ar 44100 "$audio_file"
fi

echo "Audio files in $EXAMPLES_DIR:"
ls -lh *.wav *.mp3 2>/dev/null || true
