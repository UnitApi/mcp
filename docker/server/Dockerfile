FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libasound2-dev \
    python3-dev \
    linux-headers-amd64 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ /app/src/
COPY setup.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Install additional dependencies for hardware simulation
RUN pip install --no-cache-dir \
    opencv-python-headless \
    pillow \
    pydub \
    simpleaudio \
    numpy

# Copy the server script
COPY docker/server/hardware_server.py /app/

# Expose the port for the hardware server
EXPOSE 8080

# Run the server
CMD ["python", "hardware_server.py"]
