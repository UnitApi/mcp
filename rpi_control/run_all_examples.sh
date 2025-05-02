#!/bin/bash
set -e

EXAMPLES_DIR="$(dirname "$0")/examples"

examples=(
    "hello_world.py"
    "led_control.py"
    "audio_record.py"
    "play_audio_unitmcp.py"
    "speaker_control.py"
    "mqtt_example.py"
    "port.py"
    "llm_hardware_client.py"
    "llm_hardware_control.py"
    "full_demo.py"
    "rpi_control.py"
    "test_llm_mcp.py"
)

for example in "${examples[@]}"; do
    if [[ "$example" == *.py ]]; then
        echo "\n==============================="
        echo "Running $example"
        echo "===============================\n"
        python3 "$EXAMPLES_DIR/$example"
        echo "\n===============================\n"
        sleep 1
    fi
    if [[ "$example" == *.sh ]]; then
        echo "\n==============================="
        echo "Running $example"
        echo "===============================\n"
        bash "$EXAMPLES_DIR/$example"
        echo "\n===============================\n"
        sleep 1
    fi
done
