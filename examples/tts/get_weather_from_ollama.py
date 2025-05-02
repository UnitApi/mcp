"""
TTS Client: gets weather info from Ollama and sends it to MCP TTS server.
"""
import requests
import json

def get_weather_from_ollama(prompt="Opowiedz o pogodzie w Warszawie na dziś."):
    # Zakładamy lokalny endpoint Ollama (możesz dostosować)
    url = "http://localhost:11434/api/generate"
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
        print(f"Ollama error: {resp.status_code}")
        return None

def send_to_tts(text):
    url = "http://localhost:8081/tts"
    resp = requests.post(url, json={"text": text})
    if resp.status_code == 200:
        print("[TTS] Wiadomość odczytana na głos.")
    else:
        print(f"TTS error: {resp.status_code}")

if __name__ == "__main__":
    weather = get_weather_from_ollama()
    if weather:
        print("Ollama:", weather)
        send_to_tts(weather)
    else:
        print("Nie udało się pobrać informacji o pogodzie.")
