#!/bin/bash

# Optimization script for running unitmcp on Raspberry Pi
# This script configures system settings for optimal performance

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "This script is intended for Raspberry Pi systems"
    exit 1
fi

echo "Optimizing system settings for unitmcp..."

# Update package lists
echo "Updating package lists..."
apt-get update

# Install required packages
echo "Installing required packages..."
apt-get install -y \
    v4l-utils \
    ffmpeg \
    python3-opencv \
    python3-picamera2 \
    python3-pip \
    python3-venv \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libasound2-dev \
    portaudio19-dev \
    python3-all-dev

# Configure GPU memory split
echo "Configuring GPU memory..."
if ! grep -q "gpu_mem=" /boot/config.txt; then
    echo "gpu_mem=256" >> /boot/config.txt
else
    sed -i 's/gpu_mem=.*/gpu_mem=256/' /boot/config.txt
fi

# Configure USB ports for cameras
echo "Configuring USB ports..."
if ! grep -q "max_usb_current=1" /boot/config.txt; then
    echo "max_usb_current=1" >> /boot/config.txt
fi

# Configure system limits
echo "Configuring system limits..."
cat > /etc/sysctl.d/99-unitmcp.conf << EOL
# Increase USB buffer size
vm.dirty_background_bytes = 25165824    # 24MB
vm.dirty_bytes = 50331648               # 48MB

# Increase network buffers
net.core.rmem_max = 16777216            # 16MB
net.core.wmem_max = 16777216            # 16MB
net.core.rmem_default = 1048576         # 1MB
net.core.wmem_default = 1048576         # 1MB
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Increase maximum number of open files
fs.file-max = 100000
EOL

# Apply sysctl settings
sysctl -p /etc/sysctl.d/99-unitmcp.conf

# Configure user limits
cat > /etc/security/limits.d/99-unitmcp.conf << EOL
# Increase maximum number of open files for unitmcp user
unitmcp soft nofile 32768
unitmcp hard nofile 65536

# Increase real-time priority limits
unitmcp soft rtprio 99
unitmcp hard rtprio 99
EOL

# Configure video devices
echo "Configuring video devices..."
cat > /etc/udev/rules.d/99-unitmcp-video.rules << EOL
# Give video devices appropriate permissions
KERNEL=="video[0-9]*", SUBSYSTEM=="video4linux", GROUP="video", MODE="0660"
KERNEL=="vchiq", GROUP="video", MODE="0660"
EOL

# Configure audio devices
echo "Configuring audio devices..."
cat > /etc/udev/rules.d/99-unitmcp-audio.rules << EOL
# Give audio devices appropriate permissions
KERNEL=="pcmC[0-9]*D[0-9]*[cp]", GROUP="audio", MODE="0660"
KERNEL=="controlC[0-9]*", GROUP="audio", MODE="0660"
EOL

# Reload udev rules
udevadm control --reload-rules
udevadm trigger

# Configure CPU governor
echo "Configuring CPU governor..."
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo "performance" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
    # Make it persistent
    cat > /etc/tmpfiles.d/unitmcp-cpu.conf << EOL
w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor - - - - performance
EOL
fi

# Configure camera module
echo "Configuring camera module..."
if ! grep -q "start_x=1" /boot/config.txt; then
    echo "start_x=1" >> /boot/config.txt
fi

# Configure memory split for camera
if ! grep -q "cma_lwm=" /boot/cmdline.txt; then
    sed -i '$ s/$/ cma_lwm=16 cma_hwm=32/' /boot/cmdline.txt
fi

# Create log rotation configuration
echo "Configuring log rotation..."
cat > /etc/logrotate.d/unitmcp << EOL
/var/log/unitmcp/unitmcp.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 640 unitmcp unitmcp
}
EOL

echo "System optimization complete!"
echo "Please reboot your system for all changes to take effect."
