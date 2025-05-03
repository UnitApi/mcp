#!/bin/bash
# Script to demonstrate how to use speaker_control.py with a sample audio file

# Load .env if present
if [ -f ../.env ]; then
  set -a
  . ../.env
  set +a
  echo "Loaded environment variables from ../.env file"
elif [ -f ../.env.development ]; then
  set -a
  . ../.env.development
  set +a
  echo "Loaded environment variables from ../.env.development file"
else
  echo "Warning: No .env or .env.development file found. Using default values."
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
fi

# Set default values if not provided in .env
: ${DEFAULT_WAV:="sample_tone.wav"}
: ${AUDIO_DURATION:="3"}
: ${AUDIO_FREQUENCY:="440"}

# Create a sample audio file if it doesn't exist
SAMPLE_WAV="${DEFAULT_WAV}"

if [ ! -f "$SAMPLE_WAV" ]; then
    echo "Creating sample audio file: $SAMPLE_WAV"
    # Generate a tone with configurable frequency and duration
    ffmpeg -f lavfi -i "sine=frequency=${AUDIO_FREQUENCY}:duration=${AUDIO_DURATION}" -c:a pcm_s16le -ar 44100 "$SAMPLE_WAV"
fi

# Get script directory
SCRIPT_DIR="${EXAMPLES_DIR:-$(dirname "$0")}"

# Play the sample audio file
echo "Playing sample audio file using speaker_control.py..."
python "$SCRIPT_DIR/speaker_control.py" --file "$SAMPLE_WAV" --host "${RPI_HOST:-127.0.0.1}" --port "${RPI_PORT:-8080}"

echo "Done!"
