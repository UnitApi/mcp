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
