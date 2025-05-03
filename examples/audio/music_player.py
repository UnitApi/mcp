#!/usr/bin/env python3
"""
UnitMCP Audio Example: Music Player

This example demonstrates how to play music files on a Raspberry Pi
using a configuration file to specify the playlist and settings.
"""

import argparse
import logging
import os
import sys
import time
import yaml
import random
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MusicPlayer:
    """
    Music player for playing audio files on a Raspberry Pi or other systems.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        music_dir: Optional[str] = None,
        output_device: Optional[str] = None,
        volume: float = 0.7,
        simulation: bool = False
    ):
        """
        Initialize the music player.
        
        Parameters
        ----------
        config_path : str, optional
            Path to the configuration file
        music_dir : str, optional
            Directory containing music files (overrides config)
        output_device : str, optional
            Audio output device name or index (overrides config)
        volume : float
            Volume level (0.0 to 1.0) (overrides config)
        simulation : bool
            Whether to run in simulation mode
        """
        self.simulation = simulation
        self.config = {}
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        
        # Override config with command-line arguments if provided
        if music_dir:
            self.config["music_dir"] = music_dir
        if output_device:
            self.config["output_device"] = output_device
        if volume is not None:
            self.config["volume"] = volume
        
        # Set default values if not specified
        if "music_dir" not in self.config:
            self.config["music_dir"] = "./music"
        if "volume" not in self.config:
            self.config["volume"] = 0.7
        if "shuffle" not in self.config:
            self.config["shuffle"] = False
        if "repeat" not in self.config:
            self.config["repeat"] = False
        if "playlist" not in self.config:
            self.config["playlist"] = []
        
        # Initialize audio player
        self._init_audio_player()
    
    def _init_audio_player(self):
        """Initialize the audio player based on available libraries."""
        self.player_type = None
        
        if self.simulation:
            logger.info("Running in simulation mode, no audio will be played")
            self.player_type = "simulation"
            return
        
        # Try to import pygame for audio playback
        try:
            import pygame
            pygame.mixer.init()
            self.player_type = "pygame"
            logger.info("Using pygame for audio playback")
            
            # Set volume
            pygame.mixer.music.set_volume(self.config["volume"])
            return
        except ImportError:
            logger.warning("pygame not available")
        
        # Try to import sounddevice as alternative
        try:
            import sounddevice as sd
            import soundfile as sf
            self.player_type = "sounddevice"
            logger.info("Using sounddevice for audio playback")
            
            # Set output device if specified
            if "output_device" in self.config:
                device_name = self.config["output_device"]
                devices = sd.query_devices()
                
                for i, device in enumerate(devices):
                    if device_name.lower() in device["name"].lower():
                        sd.default.device = i
                        logger.info(f"Using audio device: {device['name']}")
                        break
                else:
                    logger.warning(f"Audio device '{device_name}' not found, using default")
            
            return
        except ImportError:
            logger.warning("sounddevice not available")
        
        # If no audio library is available, fall back to simulation mode
        logger.warning("No audio library available, falling back to simulation mode")
        self.player_type = "simulation"
    
    def load_config(self, config_path: str):
        """
        Load configuration from a YAML file.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # Log configuration
            logger.info(f"Music directory: {self.config.get('music_dir', 'Not specified')}")
            logger.info(f"Output device: {self.config.get('output_device', 'Default')}")
            logger.info(f"Volume: {self.config.get('volume', 0.7)}")
            logger.info(f"Shuffle: {self.config.get('shuffle', False)}")
            logger.info(f"Repeat: {self.config.get('repeat', False)}")
            
            playlist = self.config.get('playlist', [])
            if playlist:
                logger.info(f"Playlist: {len(playlist)} tracks")
                for i, track in enumerate(playlist[:5]):
                    logger.info(f"  {i+1}. {track}")
                if len(playlist) > 5:
                    logger.info(f"  ... and {len(playlist) - 5} more")
            else:
                logger.info("No playlist specified, will play all files in music directory")
                
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            self.config = {}
    
    def get_playlist(self) -> List[str]:
        """
        Get the list of music files to play.
        
        Returns
        -------
        List[str]
            List of paths to music files
        """
        playlist = []
        
        # If playlist is specified in config, use it
        if self.config.get("playlist"):
            music_dir = self.config.get("music_dir", ".")
            for track in self.config["playlist"]:
                # Handle absolute paths
                if os.path.isabs(track):
                    if os.path.exists(track):
                        playlist.append(track)
                    else:
                        logger.warning(f"Track not found: {track}")
                # Handle relative paths
                else:
                    track_path = os.path.join(music_dir, track)
                    if os.path.exists(track_path):
                        playlist.append(track_path)
                    else:
                        logger.warning(f"Track not found: {track_path}")
        
        # If no playlist or empty playlist, use all files in music directory
        if not playlist and os.path.isdir(self.config["music_dir"]):
            for filename in os.listdir(self.config["music_dir"]):
                if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    playlist.append(os.path.join(self.config["music_dir"], filename))
        
        # Shuffle playlist if enabled
        if self.config.get("shuffle"):
            random.shuffle(playlist)
        
        return playlist
    
    def play_track(self, track_path: str) -> bool:
        """
        Play a single music track.
        
        Parameters
        ----------
        track_path : str
            Path to the music file
        
        Returns
        -------
        bool
            True if playback started successfully, False otherwise
        """
        if not os.path.exists(track_path):
            logger.error(f"Track not found: {track_path}")
            return False
        
        logger.info(f"Playing: {os.path.basename(track_path)}")
        
        if self.simulation:
            logger.info(f"SIMULATION: Playing {os.path.basename(track_path)}")
            # Simulate playback for a few seconds
            time.sleep(3)
            return True
        
        if self.player_type == "pygame":
            try:
                import pygame
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
                return True
            except Exception as e:
                logger.error(f"Failed to play track with pygame: {e}")
                return False
        
        elif self.player_type == "sounddevice":
            try:
                import sounddevice as sd
                import soundfile as sf
                
                data, fs = sf.read(track_path)
                sd.play(data, fs)
                return True
            except Exception as e:
                logger.error(f"Failed to play track with sounddevice: {e}")
                return False
        
        return False
    
    def play_playlist(self):
        """Play all tracks in the playlist."""
        playlist = self.get_playlist()
        
        if not playlist:
            logger.error("No tracks found to play")
            return
        
        logger.info(f"Starting playback of {len(playlist)} tracks")
        
        repeat = self.config.get("repeat", False)
        
        while playlist:
            for track in playlist:
                try:
                    success = self.play_track(track)
                    
                    if success and not self.simulation:
                        # Wait for track to finish
                        if self.player_type == "pygame":
                            import pygame
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.5)
                        elif self.player_type == "sounddevice":
                            import sounddevice as sd
                            sd.wait()
                    
                    # Check if user interrupted playback
                    if hasattr(self, "stop_requested") and self.stop_requested:
                        logger.info("Playback stopped by user")
                        return
                    
                except KeyboardInterrupt:
                    logger.info("Playback interrupted by user")
                    return
                except Exception as e:
                    logger.error(f"Error during playback: {e}")
            
            # Exit loop if repeat is disabled
            if not repeat:
                break
            
            logger.info("Repeating playlist")
    
    def stop(self):
        """Stop playback."""
        self.stop_requested = True
        
        if self.simulation:
            return
        
        if self.player_type == "pygame":
            try:
                import pygame
                pygame.mixer.music.stop()
            except Exception as e:
                logger.error(f"Failed to stop playback: {e}")
        
        elif self.player_type == "sounddevice":
            try:
                import sounddevice as sd
                sd.stop()
            except Exception as e:
                logger.error(f"Failed to stop playback: {e}")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Music Player Example")
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--music-dir",
        type=str,
        help="Directory containing music files (overrides config)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Audio output device name or index (overrides config)"
    )
    
    parser.add_argument(
        "--volume",
        type=float,
        help="Volume level (0.0 to 1.0) (overrides config)"
    )
    
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle playlist (overrides config)"
    )
    
    parser.add_argument(
        "--repeat",
        action="store_true",
        help="Repeat playlist (overrides config)"
    )
    
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit"
    )
    
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="Run in simulation mode without actual audio output"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def list_audio_devices():
    """List available audio output devices."""
    print("Available audio devices:")
    
    # Try pygame
    try:
        import pygame
        pygame.mixer.init()
        print("\nPygame audio devices:")
        print("  Default device")
        return True
    except ImportError:
        pass
    
    # Try sounddevice
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        print("\nSounddevice audio devices:")
        for i, device in enumerate(devices):
            if device["max_output_channels"] > 0:
                print(f"  {i}: {device['name']} (outputs: {device['max_output_channels']})")
        
        return True
    except ImportError:
        pass
    
    print("No audio libraries available")
    return False


def main():
    """
    Main function to run the music player example.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # List audio devices if requested
    if args.list_devices:
        if list_audio_devices():
            return 0
        else:
            return 1
    
    # Create music player
    player = MusicPlayer(
        config_path=args.config,
        music_dir=args.music_dir,
        output_device=args.output,
        volume=args.volume,
        simulation=args.simulation
    )
    
    # Override config with command-line arguments
    if args.shuffle:
        player.config["shuffle"] = True
    if args.repeat:
        player.config["repeat"] = True
    
    try:
        # Play playlist
        player.play_playlist()
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        player.stop()
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
