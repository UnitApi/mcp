#!/bin/bash

# Installation script for machine learning models
# This script downloads and installs required models for detection and recognition

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create models directory
MODELS_DIR="$PROJECT_DIR/models"
mkdir -p "$MODELS_DIR"

# Function to download file with progress
download_file() {
    local url="$1"
    local output="$2"
    if command -v wget &> /dev/null; then
        wget -O "$output" "$url" --show-progress
    else
        curl -L -o "$output" "$url" --progress-bar
    fi
}

echo "Installing machine learning models..."

# Create subdirectories
mkdir -p "$MODELS_DIR/video/detection"
mkdir -p "$MODELS_DIR/video/face"
mkdir -p "$MODELS_DIR/audio/speech"

# Install YOLO models for object detection
echo "Installing YOLO models..."
YOLO_DIR="$MODELS_DIR/video/detection/yolo"
mkdir -p "$YOLO_DIR"

# Download YOLOv3 files
echo "Downloading YOLOv3..."
download_file "https://pjreddie.com/media/files/yolov3.weights" "$YOLO_DIR/yolov3.weights"
download_file "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg" "$YOLO_DIR/yolov3.cfg"
download_file "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names" "$YOLO_DIR/coco.names"

# Download YOLOv3-tiny for resource-constrained devices
echo "Downloading YOLOv3-tiny..."
download_file "https://pjreddie.com/media/files/yolov3-tiny.weights" "$YOLO_DIR/yolov3-tiny.weights"
download_file "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg" "$YOLO_DIR/yolov3-tiny.cfg"

# Install face detection models
echo "Installing face detection models..."
FACE_DIR="$MODELS_DIR/video/face"

# Download OpenCV DNN face detection model
echo "Downloading face detection model..."
download_file "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel" \
    "$FACE_DIR/res10_300x300_ssd_iter_140000.caffemodel"
download_file "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt" \
    "$FACE_DIR/deploy.prototxt"

# Download Haar cascade for lightweight face detection
echo "Downloading Haar cascade..."
download_file "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml" \
    "$FACE_DIR/haarcascade_frontalface_default.xml"

# Install speech recognition models
echo "Installing speech recognition models..."
SPEECH_DIR="$MODELS_DIR/audio/speech"

# Download Vosk model
echo "Downloading Vosk model..."
VOSK_MODEL="vosk-model-small-en-us-0.15"
VOSK_URL="https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"
VOSK_ZIP="$SPEECH_DIR/${VOSK_MODEL}.zip"

download_file "$VOSK_URL" "$VOSK_ZIP"
echo "Extracting Vosk model..."
unzip -q -o "$VOSK_ZIP" -d "$SPEECH_DIR"
rm "$VOSK_ZIP"
mv "$SPEECH_DIR/$VOSK_MODEL" "$SPEECH_DIR/vosk-model-small-en"

# Create model configuration file
echo "Creating model configuration..."
cat > "$MODELS_DIR/config.yaml" << EOL
# Model configuration for unitmcp
video:
  detection:
    yolo:
      model: models/video/detection/yolo/yolov3.weights
      config: models/video/detection/yolo/yolov3.cfg
      classes: models/video/detection/yolo/coco.names
      tiny:
        model: models/video/detection/yolo/yolov3-tiny.weights
        config: models/video/detection/yolo/yolov3-tiny.cfg
  face:
    dnn:
      model: models/video/face/res10_300x300_ssd_iter_140000.caffemodel
      config: models/video/face/deploy.prototxt
    haar:
      cascade: models/video/face/haarcascade_frontalface_default.xml
audio:
  speech:
    vosk:
      model: models/audio/speech/vosk-model-small-en
EOL

# Set permissions
echo "Setting permissions..."
chmod -R 755 "$MODELS_DIR"
find "$MODELS_DIR" -type f -exec chmod 644 {} \;

echo "Model installation complete!"
echo "Models installed in: $MODELS_DIR"
echo "Configuration file: $MODELS_DIR/config.yaml"

# Optional: Install additional language models
if [ "$1" == "--all-languages" ]; then
    echo "Installing additional language models..."
    
    # Download additional Vosk models
    for lang in "fr" "de" "es" "it"; do
        echo "Downloading $lang model..."
        MODEL_NAME="vosk-model-small-${lang}-0.15"
        download_file "https://alphacephei.com/vosk/models/${MODEL_NAME}.zip" "$SPEECH_DIR/${MODEL_NAME}.zip"
        unzip -q -o "$SPEECH_DIR/${MODEL_NAME}.zip" -d "$SPEECH_DIR"
        rm "$SPEECH_DIR/${MODEL_NAME}.zip"
        mv "$SPEECH_DIR/$MODEL_NAME" "$SPEECH_DIR/vosk-model-small-$lang"
    done
fi

# Optional: Install GPU-optimized models
if [ "$1" == "--gpu" ]; then
    echo "Installing GPU-optimized models..."
    
    # Download YOLOv4-GPU
    echo "Downloading YOLOv4-GPU..."
    download_file "https://github.com/AlexeyAB/darknet/releases/download/yolov4/yolov4.weights" \
        "$YOLO_DIR/yolov4-gpu.weights"
    download_file "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4.cfg" \
        "$YOLO_DIR/yolov4-gpu.cfg"
fi

echo "Use --all-languages to install additional language models"
echo "Use --gpu to install GPU-optimized models"
