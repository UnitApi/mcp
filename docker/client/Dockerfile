FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    portaudio19-dev \
    linux-headers-amd64 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ /app/src/
COPY setup.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Install additional dependencies for LLM client
RUN pip install --no-cache-dir \
    httpx \
    python-dotenv \
    ollama

# Copy the client script
COPY docker/client/llm_client.py /app/

# Set environment variables
ENV HARDWARE_SERVER_HOST=hardware-server
ENV HARDWARE_SERVER_PORT=8080
ENV OLLAMA_HOST=ollama
ENV OLLAMA_PORT=11434

# Run the client
CMD ["python", "llm_client.py"]
