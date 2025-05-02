#!/bin/bash
# install_minimal_ollama.sh - Installs minimal Ollama setup for UnitMCP testing
# with text-to-speech and speech-to-text functionality

echo "Installing minimal Ollama setup for UnitMCP testing..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
pip install pyttsx3 aiohttp requests SpeechRecognition pyaudio

# Check if Ollama is already installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    # Install Ollama using the official installation script
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Check if installation was successful
    if ! command -v ollama &> /dev/null; then
        echo "Failed to install Ollama. Please install it manually from https://ollama.com"
        exit 1
    fi
else
    echo "Ollama is already installed."
fi

# Pull the smallest possible model for Ollama (tinyllama)
echo "Pulling the tinyllama model for Ollama..."
ollama pull tinyllama

echo "Installation completed successfully!"
echo "Creating necessary Python scripts for UnitMCP testing..."

# Create speech-to-text server script
cat > stt_server.py << 'EOF'
"""
Speech-to-Text Server for UnitMCP: records audio from microphone and converts it to text.
"""
import asyncio
from aiohttp import web
import speech_recognition as sr
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()

async def handle_stt(request):
    """Handle speech-to-text conversion requests"""
    try:
        data = await request.json()
        duration = data.get('duration', 5)  # Default recording duration: 5 seconds
        
        logger.info(f"Recording audio for {duration} seconds...")
        
        # Record audio from microphone
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            logger.info(f"Listening for {duration} seconds...")
            audio = recognizer.listen(source, timeout=duration)
        
        # Convert speech to text
        logger.info("Converting speech to text...")
        try:
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized text: {text}")
            return web.json_response({'status': 'success', 'text': text})
        except sr.UnknownValueError:
            logger.warning("Speech Recognition could not understand audio")
            return web.json_response({'status': 'error', 'message': 'Could not understand audio'}, status=400)
        except sr.RequestError as e:
            logger.error(f"Could not request results from Speech Recognition service; {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error processing STT request: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def handle_stt_to_ollama(request):
    """Handle speech-to-text conversion and send to Ollama"""
    try:
        data = await request.json()
        duration = data.get('duration', 5)  # Default recording duration: 5 seconds
        prompt_prefix = data.get('prompt_prefix', '')  # Optional prefix for the Ollama prompt
        
        logger.info(f"Recording audio for {duration} seconds...")
        
        # Record audio from microphone
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            logger.info(f"Listening for {duration} seconds...")
            audio = recognizer.listen(source, timeout=duration)
        
        # Convert speech to text
        logger.info("Converting speech to text...")
        try:
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized text: {text}")
            
            # Send text to Ollama
            logger.info("Sending text to Ollama...")
            import requests
            
            ollama_url = "http://localhost:11434/api/generate"
            ollama_payload = {
                "model": "tinyllama",
                "prompt": f"{prompt_prefix} {text}".strip(),
                "stream": False
            }
            
            ollama_response = requests.post(ollama_url, json=ollama_payload)
            if ollama_response.status_code == 200:
                ollama_data = ollama_response.json()
                ollama_text = ollama_data.get('response', '').strip()
                logger.info(f"Ollama response: {ollama_text}")
                
                return web.json_response({
                    'status': 'success', 
                    'input_text': text, 
                    'ollama_response': ollama_text
                })
            else:
                logger.error(f"Ollama error: {ollama_response.status_code}")
                return web.json_response({
                    'status': 'error', 
                    'message': f"Ollama error: {ollama_response.status_code}",
                    'input_text': text
                }, status=500)
                
        except sr.UnknownValueError:
            logger.warning("Speech Recognition could not understand audio")
            return web.json_response({'status': 'error', 'message': 'Could not understand audio'}, status=400)
        except sr.RequestError as e:
            logger.error(f"Could not request results from Speech Recognition service; {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error processing STT-to-Ollama request: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

app = web.Application()
app.router.add_post('/stt', handle_stt)
app.router.add_post('/stt_to_ollama', handle_stt_to_ollama)

if __name__ == '__main__':
    print("[STT Server] Listening on http://localhost:8082/stt and http://localhost:8082/stt_to_ollama")
    web.run_app(app, port=8082)
EOF

# Create a combined client script that can use both TTS and STT
cat > unitmcp_client.py << 'EOF'
"""
UnitMCP Client: Demonstrates both text-to-speech and speech-to-text capabilities.
"""
import requests
import json
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def text_to_speech(text):
    """Send text to TTS server to be spoken"""
    url = "http://localhost:8081/tts"
    try:
        resp = requests.post(url, json={"text": text})
        if resp.status_code == 200:
            logger.info("[TTS] Message spoken successfully.")
            return True
        else:
            logger.error(f"TTS error: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending to TTS server: {e}")
        return False

def speech_to_text(duration=5):
    """Record speech and convert to text"""
    url = "http://localhost:8082/stt"
    try:
        resp = requests.post(url, json={"duration": duration})
        if resp.status_code == 200:
            data = resp.json()
            text = data.get('text', '')
            logger.info(f"[STT] Recognized text: {text}")
            return text
        else:
            logger.error(f"STT error: {resp.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error sending to STT server: {e}")
        return None

def speech_to_ollama(duration=5, prompt_prefix=""):
    """Record speech, convert to text, and send to Ollama"""
    url = "http://localhost:8082/stt_to_ollama"
    try:
        resp = requests.post(url, json={"duration": duration, "prompt_prefix": prompt_prefix})
        if resp.status_code == 200:
            data = resp.json()
            input_text = data.get('input_text', '')
            ollama_response = data.get('ollama_response', '')
            logger.info(f"[STT->Ollama] Input: {input_text}")
            logger.info(f"[STT->Ollama] Response: {ollama_response}")
            return input_text, ollama_response
        else:
            logger.error(f"STT->Ollama error: {resp.status_code}")
            return None, None
    except Exception as e:
        logger.error(f"Error sending to STT->Ollama server: {e}")
        return None, None

def get_weather_from_ollama(prompt="Opowiedz o pogodzie w Warszawie na dziś."):
    """Get weather information from Ollama"""
    url = "http://localhost:11434/api/generate"
    try:
        payload = {
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('response', '').strip()
        else:
            logger.error(f"Ollama error: {resp.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error sending to Ollama: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="UnitMCP Client for TTS and STT testing")
    parser.add_argument("--mode", choices=["tts", "stt", "stt-ollama", "weather-tts", "full-loop"], 
                        default="full-loop", help="Mode of operation")
    parser.add_argument("--text", type=str, help="Text to speak (for TTS mode)")
    parser.add_argument("--duration", type=int, default=5, help="Recording duration in seconds (for STT modes)")
    parser.add_argument("--prompt", type=str, default="", help="Prompt prefix for Ollama (for STT-Ollama mode)")
    
    args = parser.parse_args()
    
    # Check if Ollama is running when needed
    if args.mode in ["stt-ollama", "weather-tts", "full-loop"]:
        try:
            requests.get("http://localhost:11434/api/tags")
        except:
            logger.error("Ollama is not running. Please start Ollama first with 'ollama serve'")
            return
    
    if args.mode == "tts":
        if not args.text:
            logger.error("Please provide text to speak with --text")
            return
        text_to_speech(args.text)
    
    elif args.mode == "stt":
        logger.info(f"Recording for {args.duration} seconds...")
        text = speech_to_text(args.duration)
        if text:
            logger.info(f"Recognized: {text}")
    
    elif args.mode == "stt-ollama":
        logger.info(f"Recording for {args.duration} seconds...")
        input_text, ollama_response = speech_to_ollama(args.duration, args.prompt)
        if ollama_response:
            logger.info(f"Ollama response: {ollama_response}")
    
    elif args.mode == "weather-tts":
        weather = get_weather_from_ollama()
        if weather:
            logger.info(f"Weather: {weather}")
            text_to_speech(weather)
    
    elif args.mode == "full-loop":
        # Full demonstration loop
        logger.info("Starting full demonstration loop")
        
        # 1. Speak a welcome message
        welcome = "Witaj w demonstracji UnitMCP. Powiedz coś, a ja przekażę to do modelu Ollama."
        logger.info("Speaking welcome message...")
        text_to_speech(welcome)
        
        # 2. Record speech and send to Ollama
        logger.info(f"Recording for {args.duration} seconds...")
        input_text, ollama_response = speech_to_ollama(args.duration)
        
        # 3. Speak Ollama's response
        if ollama_response:
            logger.info("Speaking Ollama's response...")
            text_to_speech(ollama_response)
        
        logger.info("Demonstration completed!")

if __name__ == "__main__":
    main()
EOF

# Create start scripts for the servers and client
cat > start_tts_server.sh << 'EOF'
#!/bin/bash
# start_tts_server.sh - Starts the TTS server

echo "Starting TTS server on http://localhost:8081/tts"
echo "Press Ctrl+C to stop the server"

# Run the TTS server
python3 server.py
EOF

cat > start_stt_server.sh << 'EOF'
#!/bin/bash
# start_stt_server.sh - Starts the STT server

echo "Starting STT server on http://localhost:8082/stt"
echo "Press Ctrl+C to stop the server"

# Run the STT server
python3 stt_server.py
EOF

cat > start_ollama.sh << 'EOF'
#!/bin/bash
# start_ollama.sh - Starts the Ollama server

echo "Starting Ollama server on http://localhost:11434"
echo "Press Ctrl+C to stop the server"

# Run Ollama
ollama serve
EOF

cat > start_unitmcp_client.sh << 'EOF'
#!/bin/bash
# start_unitmcp_client.sh - Starts the UnitMCP client

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running. Please start Ollama first with ./start_ollama.sh"
    exit 1
fi

# Check if TTS server is running
if ! curl -s http://localhost:8081/tts -d '{"text":"test"}' > /dev/null; then
    echo "Warning: TTS server might not be running. Make sure to start it with ./start_tts_server.sh"
    echo "Continuing anyway..."
fi

# Check if STT server is running
if ! curl -s http://localhost:8082/stt -d '{"duration":1}' > /dev/null; then
    echo "Warning: STT server might not be running. Make sure to start it with ./start_stt_server.sh"
    echo "Continuing anyway..."
fi

echo "Starting UnitMCP client..."
python3 unitmcp_client.py "$@"
EOF

# Make the scripts executable
chmod +x start_tts_server.sh
chmod +x start_stt_server.sh
chmod +x start_ollama.sh
chmod +x start_unitmcp_client.sh

echo "Installation and setup completed!"
echo ""
echo "To test the UnitMCP protocol with TTS and STT:"
echo "1. Start Ollama server:        ./start_ollama.sh"
echo "2. Start TTS server:           ./start_tts_server.sh"
echo "3. Start STT server:           ./start_stt_server.sh"
echo "4. Run the UnitMCP client:     ./start_unitmcp_client.sh"
echo ""
echo "Available client modes:"
echo "- Full demonstration loop:     ./start_unitmcp_client.sh --mode full-loop"
echo "- Text-to-speech:              ./start_unitmcp_client.sh --mode tts --text \"Hello world\""
echo "- Speech-to-text:              ./start_unitmcp_client.sh --mode stt --duration 5"
echo "- Speech-to-Ollama:            ./start_unitmcp_client.sh --mode stt-ollama --duration 5"
echo "- Weather forecast to speech:  ./start_unitmcp_client.sh --mode weather-tts"
echo ""
echo "Note: You need to run each server in a separate terminal window."
