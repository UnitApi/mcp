#!/bin/bash

# Hardware configuration script for unitmcp
# This script helps configure various audio/video devices

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to list available devices
list_devices() {
    echo "Available video devices:"
    v4l2-ctl --list-devices 2>/dev/null || echo "No video devices found"
    echo
    echo "Available audio devices:"
    arecord -l 2>/dev/null || echo "No audio devices found"
}

# Function to configure video device
configure_video() {
    local device="$1"
    
    echo "Configuring video device: $device"
    
    # List device capabilities
    echo "Device capabilities:"
    v4l2-ctl --device "$device" --all

    # Get supported formats
    echo "Supported formats:"
    v4l2-ctl --device "$device" --list-formats-ext

    # Configure default format (1280x720 MJPEG)
    echo "Setting default format..."
    v4l2-ctl --device "$device" --set-fmt-video=width=1280,height=720,pixelformat=MJPG

    # Configure default framerate (30 fps)
    echo "Setting default framerate..."
    v4l2-ctl --device "$device" --set-parm=30

    # Configure default controls
    echo "Setting default controls..."
    v4l2-ctl --device "$device" \
        --set-ctrl=brightness=128 \
        --set-ctrl=contrast=128 \
        --set-ctrl=saturation=128 \
        --set-ctrl=white_balance_temperature_auto=1 \
        --set-ctrl=power_line_frequency=2 \
        --set-ctrl=white_balance_temperature=4000 \
        --set-ctrl=sharpness=128 \
        --set-ctrl=backlight_compensation=0 \
        --set-ctrl=exposure_auto=3

    echo "Video device configured"
}

# Function to configure audio device
configure_audio() {
    local card="$1"
    local device="$2"

    echo "Configuring audio device: hw:$card,$device"

    # Get device capabilities
    echo "Device capabilities:"
    arecord -D "hw:$card,$device" --dump-hw-params || true

    # Configure ALSA settings
    echo "Configuring ALSA settings..."
    cat > "/etc/asound.d/unitmcp-$card-$device.conf" << EOL
pcm.unitmcp_${card}_${device} {
    type hw
    card $card
    device $device
    format S16_LE
    rate 44100
    channels 2
}

ctl.unitmcp_${card}_${device} {
    type hw
    card $card
    device $device
}
EOL

    # Test recording
    echo "Testing recording..."
    timeout 1 arecord -D "hw:$card,$device" \
        -f S16_LE -c 2 -r 44100 \
        -d 1 /dev/null || true

    echo "Audio device configured"
}

# Function to configure Raspberry Pi camera
configure_picamera() {
    echo "Configuring Raspberry Pi camera..."

    # Check if camera is enabled
    if ! vcgencmd get_camera | grep -q "supported=1 detected=1"; then
        echo "Error: No Raspberry Pi camera detected"
        return 1
    fi

    # Configure camera settings
    echo "Setting camera parameters..."
    cat > "/etc/modprobe.d/unitmcp-picamera.conf" << EOL
# Raspberry Pi camera settings for unitmcp
options bcm2835-v4l2 max_video_width=1920 max_video_height=1080 max_rate=30
EOL

    # Create V4L2 configuration
    echo "Configuring V4L2 settings..."
    cat > "/etc/udev/rules.d/99-unitmcp-picamera.rules" << EOL
# Create symlink for Raspberry Pi camera
SUBSYSTEM=="video4linux", KERNEL=="video[0-9]*", ATTRS{name}=="bcm2835-v4l2", SYMLINK+="picam"
EOL

    echo "Raspberry Pi camera configured"
}

# Function to configure USB audio device
configure_usb_audio() {
    echo "Configuring USB audio device..."

    # Set USB audio as default
    cat > "/etc/asound.conf" << EOL
# Default audio device configuration
pcm.!default {
    type plug
    slave.pcm "usb"
}

pcm.usb {
    type hw
    card 1
}

ctl.!default {
    type hw
    card 1
}
EOL

    # Configure USB audio parameters
    cat > "/etc/modprobe.d/unitmcp-usb-audio.conf" << EOL
# USB audio settings for unitmcp
options snd_usb_audio index=1 vid=0x0000 pid=0x0000 nrpacks=1 async_unlink=1
EOL

    echo "USB audio device configured"
}

# Function to save device configuration
save_config() {
    local device_type="$1"
    local device_name="$2"
    shift 2
    local settings=("$@")

    # Create config directory if needed
    mkdir -p "$PROJECT_DIR/config/devices"

    # Save device configuration
    cat > "$PROJECT_DIR/config/devices/$device_name.yaml" << EOL
# Device configuration for $device_name
type: $device_type
enabled: true
settings:
EOL

    # Add settings
    for setting in "${settings[@]}"; do
        echo "  $setting" >> "$PROJECT_DIR/config/devices/$device_name.yaml"
    done

    echo "Configuration saved to: config/devices/$device_name.yaml"
}

# Main script

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Parse command line arguments
case "$1" in
    list)
        list_devices
        ;;
    video)
        if [ -z "$2" ]; then
            echo "Usage: $0 video /dev/videoX"
            exit 1
        fi
        configure_video "$2"
        save_config "USB_CAMERA" "camera1" \
            "resolution: 1280x720" \
            "framerate: 30" \
            "format: MJPEG"
        ;;
    audio)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 audio CARD DEVICE"
            exit 1
        fi
        configure_audio "$2" "$3"
        save_config "USB_MICROPHONE" "mic1" \
            "sample_rate: 44100" \
            "channels: 2" \
            "format: S16_LE"
        ;;
    picamera)
        configure_picamera
        save_config "CSI_CAMERA" "picam" \
            "resolution: 1920x1080" \
            "framerate: 30" \
            "format: H264"
        ;;
    usb-audio)
        configure_usb_audio
        save_config "USB_MICROPHONE" "usbmic" \
            "sample_rate: 44100" \
            "channels: 2" \
            "format: S16_LE"
        ;;
    *)
        echo "Usage: $0 COMMAND [ARGS]"
        echo
        echo "Commands:"
        echo "  list                List available devices"
        echo "  video DEVICE        Configure video device"
        echo "  audio CARD DEVICE   Configure audio device"
        echo "  picamera           Configure Raspberry Pi camera"
        echo "  usb-audio          Configure USB audio device"
        exit 1
        ;;
esac

echo "Hardware configuration complete!"
