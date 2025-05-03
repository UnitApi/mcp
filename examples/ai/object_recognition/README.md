# Object Recognition Example

This example demonstrates how to use UnitMCP's vision capabilities for object recognition. The system can:

1. Capture images from a camera
2. Process images using computer vision techniques
3. Detect and identify objects in the images
4. Display results with bounding boxes and labels
5. Optionally trigger actions based on detected objects

## Architecture

The example uses a client-server architecture:

- **Client**: Captures images and displays results
- **Server**: Processes images and runs object detection models

## Components

- `runner.py`: Sets up and runs both client and server
- `client.py`: Handles image capture and display
- `server.py`: Processes images and runs object detection
- `config/`: Configuration files for the example

## Hardware Requirements

- Camera (webcam or Raspberry Pi camera)
- Display for visualization
- Optional: Raspberry Pi or other hardware for physical device control

## Running the Example

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the example by editing the files in the `config/` directory.

3. Run the complete example:

```bash
python runner.py
```

Or run the client and server separately:

```bash
# Terminal 1
python server.py

# Terminal 2
python client.py
```

## Usage

The system will:
1. Capture images from the camera
2. Send them to the server for processing
3. Display the results with bounding boxes around detected objects
4. Optionally trigger actions based on specific objects

## Customization

You can customize the object recognition by:

1. Changing the object detection model in `config/server.yaml`
2. Adjusting detection thresholds in `config/server.yaml`
3. Adding custom actions for specific detected objects in `server.py`
4. Modifying the visualization settings in `config/client.yaml`
