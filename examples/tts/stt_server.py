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
