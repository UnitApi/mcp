#!/usr/bin/env python3
"""
Simple MCP Server for Audio Playback

This is a simplified server that just listens on a port and can receive commands
to play audio files.
"""

import asyncio
import logging
import os
import argparse
import socket
import sys
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class SimpleAudioServer:
    def __init__(self, host='0.0.0.0', port=8081):
        self.host = host
        self.port = port
        self.clients = set()
        self.log_system_info()
        
    def log_system_info(self):
        """Log detailed system information for debugging."""
        logger.info(f"=== SERVER SYSTEM INFORMATION ===")
        logger.info(f"Hostname: {socket.gethostname()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Server binding to: {self.host}:{self.port}")
        
        # Try to get IP addresses
        try:
            hostname = socket.gethostname()
            logger.info(f"IP addresses:")
            for ip in socket.gethostbyname_ex(hostname)[2]:
                logger.info(f"  - {ip}")
        except Exception as e:
            logger.error(f"Error getting IP addresses: {e}")
            
        # Check if aplay is available for audio playback
        try:
            result = subprocess.run(['which', 'aplay'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            if result.returncode == 0:
                logger.info(f"Audio playback available: {result.stdout.decode().strip()}")
            else:
                logger.warning("aplay not found, audio playback may not work")
        except Exception as e:
            logger.warning(f"Error checking audio playback: {e}")
        
        logger.info(f"=== END SYSTEM INFORMATION ===")
        
    async def play_audio(self, audio_file):
        """Play audio file using aplay."""
        logger.info(f"[AUDIO] Attempting to play: {audio_file}")
        
        if not os.path.exists(audio_file):
            logger.error(f"[AUDIO] File not found: {audio_file}")
            return {"status": "error", "message": f"File not found: {audio_file}"}
            
        try:
            logger.info(f"[AUDIO] Starting playback process")
            process = await asyncio.create_subprocess_exec(
                'aplay', audio_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"[AUDIO] Playback completed successfully")
                return {"status": "success", "message": "Playback completed"}
            else:
                logger.error(f"[AUDIO] Playback failed: {stderr.decode()}")
                return {"status": "error", "message": f"Playback failed: {stderr.decode()}"}
        except Exception as e:
            logger.error(f"[AUDIO] Error during playback: {e}")
            return {"status": "error", "message": f"Error during playback: {e}"}
        
    async def handle_client(self, reader, writer):
        """Handle a client connection."""
        addr = writer.get_extra_info('peername')
        client_ip = addr[0] if addr else "Unknown"
        client_port = addr[1] if addr else "Unknown"
        
        logger.info(f"[CONNECTION] New client connected from {client_ip}:{client_port}")
        self.clients.add(writer)
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    logger.info(f"[CONNECTION] Client {client_ip}:{client_port} disconnected (no data)")
                    break
                    
                message = data.decode()
                logger.info(f"[COMMAND] Received from {client_ip}:{client_port}: {message}")
                
                try:
                    command = json.loads(message)
                    if command.get('action') == 'play_audio':
                        audio_file = command.get('file')
                        if audio_file:
                            logger.info(f"[COMMAND] Play audio request: {audio_file}")
                            
                            # Actually play the audio
                            response = await self.play_audio(audio_file)
                        else:
                            logger.warning("[COMMAND] Play audio request missing file parameter")
                            response = {"status": "error", "message": "No audio file specified"}
                    else:
                        logger.warning(f"[COMMAND] Unknown command: {command.get('action')}")
                        response = {"status": "error", "message": "Unknown command"}
                except json.JSONDecodeError:
                    logger.error(f"[COMMAND] Invalid JSON received: {message}")
                    response = {"status": "error", "message": "Invalid JSON"}
                
                logger.info(f"[RESPONSE] Sending to {client_ip}:{client_port}: {response}")
                writer.write(json.dumps(response).encode())
                await writer.drain()
        except Exception as e:
            logger.error(f"[ERROR] Error handling client {client_ip}:{client_port}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.clients.remove(writer)
            logger.info(f"[CONNECTION] Client {client_ip}:{client_port} disconnected")
    
    async def start(self):
        """Start the server."""
        try:
            server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            
            addr = server.sockets[0].getsockname()
            logger.info(f'[SERVER] Listening on {addr[0]}:{addr[1]}')
            
            # Check if the server is actually listening
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                test_host = '127.0.0.1' if self.host == '0.0.0.0' else self.host
                s.connect((test_host, self.port))
                s.close()
                logger.info(f"[SERVER] Successfully verified server is listening on port {self.port}")
            except Exception as e:
                logger.error(f"[SERVER] Failed to verify server is listening: {e}")
                sys.exit(1)
            
            async with server:
                await server.serve_forever()
        except Exception as e:
            logger.error(f"[SERVER] Error starting server: {e}")
            sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Simple Audio Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8081, help='Port to bind to')
    args = parser.parse_args()
    
    logger.info(f"[STARTUP] Starting server on {args.host}:{args.port} at {datetime.now().isoformat()}")
    
    server = SimpleAudioServer(args.host, args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("[SHUTDOWN] Server stopped by user")
    except Exception as e:
        logger.error(f"[SHUTDOWN] Server stopped due to error: {e}")

if __name__ == "__main__":
    main()
