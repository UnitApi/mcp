FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ /app/src/
COPY setup.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for hardware simulation
RUN pip install --no-cache-dir \
    opencv-python-headless \
    pillow \
    pydub \
    simpleaudio \
    numpy

# Set PYTHONPATH so unitmcp is importable
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Set a dummy DISPLAY variable to avoid KeyError with pyautogui in headless environments
ENV DISPLAY=:0

# Copy the server script
COPY docker/server/hardware_server.py /app/

# Expose the port for the hardware server
EXPOSE 8080

# Run the server
CMD ["python", "hardware_server.py"]
