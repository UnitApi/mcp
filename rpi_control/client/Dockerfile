FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ /app/src/
COPY setup.py /app/
COPY requirements.txt /app/
COPY rpi_control/requirements.txt /app/rpi_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r rpi_requirements.txt
RUN pip install --no-cache-dir -e .

# Install additional dependencies for LLM client
RUN pip install --no-cache-dir \
    mcp \
    httpx \
    python-dotenv \
    ollama

# Copy the client script
COPY rpi_control/client/llm_client.py /app/

# Set environment variables
ENV RPI_HOST=rpi-simulator
ENV RPI_PORT=8080
ENV OLLAMA_HOST=llm-model
ENV OLLAMA_PORT=11434
ENV OLLAMA_MODEL=llama2

# Run the client
CMD ["python", "llm_client.py"]
