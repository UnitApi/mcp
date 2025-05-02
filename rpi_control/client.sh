#!/bin/bash
# client.sh: Run a client example
set -e

# Load .env if present
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

dir="${SCRIPT_DIR:-$(dirname "$0")}"
cd "$dir"

# Choose which example to run
python3 examples/full_demo.py
# python3 examples/audio_record.py
# python3 examples/led_control.py
# python3 examples/mqtt_example.py
# python3 examples/rpi_control.py
# python3 examples/hello_world.py
