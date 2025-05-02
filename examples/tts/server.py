"""
TTS Server for MCP: receives text and plays it on local speakers using pyttsx3.
"""
import asyncio
from aiohttp import web
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)

async def handle_tts(request):
    data = await request.json()
    text = data.get('text', '')
    if not text:
        return web.json_response({'error': 'No text provided'}, status=400)
    engine.say(text)
    engine.runAndWait()
    return web.json_response({'status': 'spoken', 'text': text})

app = web.Application()
app.router.add_post('/tts', handle_tts)

if __name__ == '__main__':
    print("[TTS Server] Listening on http://localhost:8081/tts")
    web.run_app(app, port=8081)
