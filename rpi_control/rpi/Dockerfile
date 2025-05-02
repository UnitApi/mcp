FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for Raspberry Pi simulation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    python3-dev \
    libasound2-dev \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ /app/src/
COPY setup.py /app/
COPY requirements.txt /app/
COPY rpi_control/requirements.txt /app/rpi_requirements.txt

# Ensure .env.docker is copied for docker-compose variable substitution (if needed)
COPY rpi_control/.env.docker /app/.env.docker

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r rpi_requirements.txt
RUN pip install --no-cache-dir -e .

# Install additional dependencies for hardware simulation
RUN pip install --no-cache-dir \
    opencv-python-headless \
    pillow \
    pydub \
    simpleaudio \
    numpy

# Set PYTHONPATH so unitmcp is importable
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Copy the hardware server script
COPY rpi_control/rpi/hardware_server.py /app/

# Expose the port for the hardware server
EXPOSE 8080

# Run the server
CMD ["python", "hardware_server.py"]
