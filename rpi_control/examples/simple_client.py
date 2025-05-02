#!/usr/bin/env python3
"""
Simple Client for Audio Playback

This is a simplified client that connects to the simple server and sends commands
to play audio files.
"""

import argparse
import json
import socket
import sys
import os
import logging
import subprocess
import platform
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def log_system_info():
    """Log detailed system information for debugging."""
    logger.info(f"=== CLIENT SYSTEM INFORMATION ===")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
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

def play_audio_locally(audio_file):
    """Play audio file locally using aplay."""
    try:
        logger.info(f"[LOCAL_AUDIO] Playing audio file locally: {audio_file}")
        
        if not os.path.exists(audio_file):
            logger.error(f"[LOCAL_AUDIO] File not found: {audio_file}")
            return False
            
        result = subprocess.run(['aplay', audio_file], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info("[LOCAL_AUDIO] Audio playback completed successfully")
            return True
        else:
            stderr = result.stderr.decode()
            logger.error(f"[LOCAL_AUDIO] Audio playback failed: {stderr}")
            return False
    except Exception as e:
        logger.error(f"[LOCAL_AUDIO] Error playing audio: {e}")
        return False

def send_play_command(host, port, audio_file, remote=False):
    """Send a command to play an audio file to the server."""
    if not remote:
        # Play locally
        return play_audio_locally(audio_file)
    
    try:
        # Check if file exists before sending
        if not os.path.exists(audio_file):
            logger.error(f"[REMOTE_AUDIO] File not found: {audio_file}")
            return False
            
        # Connect to the server
        logger.info(f"[CONNECTION] Connecting to server at {host}:{port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                logger.info(f"[CONNECTION] Successfully connected to {host}:{port}")
            except ConnectionRefusedError:
                logger.error(f"[CONNECTION] Connection refused to {host}:{port} - Is the server running?")
                return False
            except socket.gaierror:
                logger.error(f"[CONNECTION] Address resolution error for {host}:{port}")
                return False
            except Exception as e:
                logger.error(f"[CONNECTION] Connection error: {e}")
                return False
            
            # Create the command
            command = {
                "action": "play_audio",
                "file": audio_file,
                "client_hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the command
            logger.info(f"[COMMAND] Sending command: {json.dumps(command)}")
            s.sendall(json.dumps(command).encode())
            
            # Wait for response with timeout
            s.settimeout(30)  # 30 second timeout
            try:
                response_data = s.recv(1024).decode()
                logger.info(f"[RESPONSE] Received response: {response_data}")
                
                try:
                    response = json.loads(response_data)
                    if response.get("status") == "success":
                        logger.info("[RESULT] Command executed successfully")
                        return True
                    else:
                        logger.error(f"[RESULT] Command failed: {response.get('message')}")
                        return False
                except json.JSONDecodeError:
                    logger.error(f"[RESPONSE] Invalid JSON response from server: {response_data}")
                    return False
            except socket.timeout:
                logger.error("[RESPONSE] Timeout waiting for server response")
                return False
                
    except Exception as e:
        logger.error(f"[ERROR] Error communicating with server: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Simple Audio Client")
    parser.add_argument('--host', default='127.0.0.1', help='Server hostname or IP')
    parser.add_argument('--port', type=int, default=8081, help='Server port')
    parser.add_argument('--file', required=True, help='Audio file to play')
    parser.add_argument('--remote', action='store_true', help='Play on remote server')
    args = parser.parse_args()
    
    logger.info(f"[STARTUP] Simple Audio Client starting at {datetime.now().isoformat()}")
    logger.info(f"[CONFIG] Host: {args.host}, Port: {args.port}, File: {args.file}, Remote: {args.remote}")
    
    # Log system information
    log_system_info()
    
    # Check if file exists
    audio_file = args.file
    if not os.path.isfile(audio_file):
        # Try relative to current directory
        audio_file = os.path.join(os.path.dirname(__file__), audio_file)
        if not os.path.isfile(audio_file):
            logger.error(f"[ERROR] Audio file not found: {args.file}")
            sys.exit(1)
    
    logger.info(f"[FILE] Using audio file: {audio_file} ({os.path.getsize(audio_file)} bytes)")
    
    # Send the play command
    logger.info(f"[ACTION] {'Sending remote playback request' if args.remote else 'Playing locally'}")
    success = send_play_command(args.host, args.port, audio_file, args.remote)
    
    # Exit with appropriate status
    if success:
        logger.info("[RESULT] Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("[RESULT] Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
