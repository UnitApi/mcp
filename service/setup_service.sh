#!/bin/bash

# Setup script for installing unitmcp as a system service
# This script creates and enables a systemd service for unitmcp

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Get installation directory
INSTALL_DIR=$(python3 -c "import unitmcp; print(unitmcp.__path__[0])")
if [ $? -ne 0 ]; then
    echo "unitmcp package not found"
    exit 1
fi

# Create service user
echo "Creating service user..."
useradd -r -s /bin/false unitmcp || true

# Create config directory
echo "Creating config directory..."
mkdir -p /etc/unitmcp
chown unitmcp:unitmcp /etc/unitmcp

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log/unitmcp
chown unitmcp:unitmcp /var/log/unitmcp

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/unitmcp.service << EOL
[Unit]
Description=RT-ASP Audio/Video Stream Processing
After=network.target

[Service]
Type=simple
User=unitmcp
Group=unitmcp
ExecStart=/usr/local/bin/unitmcp server start
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=unitmcp_CONFIG_DIR=/etc/unitmcp
Environment=unitmcp_LOG_DIR=/var/log/unitmcp

[Install]
WantedBy=multi-user.target
EOL

# Create default config files
echo "Creating default config files..."

# Main config
cat > /etc/unitmcp/config.yaml << EOL
server:
  host: localhost
  port: 8080
  workers: 4
  ssl: false

logging:
  level: INFO
  format: "%(asctime)s [%(levelname)s] %(message)s"
  file: /var/log/unitmcp/unitmcp.log
EOL

# Devices config
cat > /etc/unitmcp/devices.yaml << EOL
devices:
  # Example device configurations
  # webcam:
  #   type: USB_CAMERA
  #   enabled: true
  #   settings:
  #     resolution: 1280x720
  #     framerate: 30
EOL

# Streams config
cat > /etc/unitmcp/streams.yaml << EOL
streams:
  # Example stream configurations
  # webcam_stream:
  #   device: webcam
  #   type: video
  #   enabled: true
  #   outputs:
  #     - type: RTSP
  #       url: rtsp://localhost:8554/webcam
EOL

# Pipelines config
cat > /etc/unitmcp/pipelines.yaml << EOL
pipelines:
  # Example pipeline configurations
  # face_detection:
  #   enabled: true
  #   stages:
  #     - name: source
  #       type: VIDEO_SOURCE
  #       device: webcam
  #     - name: detect
  #       type: FACE_DETECTION
  #       inputs: [source]
EOL

# Set permissions
chown -R unitmcp:unitmcp /etc/unitmcp
chmod 644 /etc/unitmcp/*.yaml

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable unitmcp
systemctl start unitmcp

echo "Service setup complete!"
echo "Check status with: systemctl status unitmcp"
echo "View logs with: journalctl -u unitmcp"
