FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Expose Ollama API port
EXPOSE 11434

# Set up a directory for models
RUN mkdir -p /root/.ollama/models

# Set the default command
CMD ["ollama", "serve"]
