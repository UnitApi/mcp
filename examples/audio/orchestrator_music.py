#!/usr/bin/env python3
"""
UnitMCP Audio Example: Orchestrator Music Player

This script provides a convenient way to upload music configuration and files
to a Raspberry Pi and play them using the UnitMCP orchestrator.
"""

import argparse
import logging
import os
import sys
import yaml
import time
import shutil
import tempfile
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Try to import orchestrator module
try:
    from unitmcp.orchestrator.orchestrator import Orchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    logger.warning("UnitMCP orchestrator module not available. Some features may be limited.")


class OrchestratorMusicPlayer:
    """
    Helper class to play music on a Raspberry Pi using the UnitMCP orchestrator.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the orchestrator music player.
        
        Parameters
        ----------
        config_path : str, optional
            Path to the configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.orchestrator = None
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        
        # Initialize orchestrator if available
        if ORCHESTRATOR_AVAILABLE:
            self.orchestrator = Orchestrator()
        else:
            logger.warning("Orchestrator not available. Running in standalone mode.")
    
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
            
            # Log remote settings if available
            remote_config = self.config.get('remote', {})
            if remote_config:
                logger.info(f"Remote host: {remote_config.get('host', 'Not specified')}")
                logger.info(f"Remote port: {remote_config.get('port', 'Not specified')}")
                
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            self.config = {}
    
    def prepare_remote_directory(self, host: str, ssh_username: str, ssh_password: Optional[str] = None, 
                                ssh_key_path: Optional[str] = None) -> bool:
        """
        Prepare remote directory on the Raspberry Pi.
        
        Parameters
        ----------
        host : str
            Hostname or IP address of the Raspberry Pi
        ssh_username : str
            SSH username
        ssh_password : str, optional
            SSH password
        ssh_key_path : str, optional
            Path to SSH key file
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.orchestrator:
            logger.error("Orchestrator not available. Cannot prepare remote directory.")
            return False
        
        try:
            # Create command to make directories
            command = "mkdir -p ~/music_player/music"
            
            # Run command on remote host
            result = self.orchestrator.run_command_on_remote(
                host=host,
                command=command,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                ssh_key_path=ssh_key_path
            )
            
            if result.get("status") == "success":
                logger.info("Remote directory prepared successfully")
                return True
            else:
                logger.error(f"Failed to prepare remote directory: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to prepare remote directory: {e}")
            return False
    
    def upload_config_and_music(self, host: str, ssh_username: str, ssh_password: Optional[str] = None,
                               ssh_key_path: Optional[str] = None) -> bool:
        """
        Upload configuration and music files to the Raspberry Pi.
        
        Parameters
        ----------
        host : str
            Hostname or IP address of the Raspberry Pi
        ssh_username : str
            SSH username
        ssh_password : str, optional
            SSH password
        ssh_key_path : str, optional
            Path to SSH key file
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.orchestrator:
            logger.error("Orchestrator not available. Cannot upload files.")
            return False
        
        if not self.config:
            logger.error("No configuration loaded. Cannot upload files.")
            return False
        
        try:
            # Prepare remote directory
            if not self.prepare_remote_directory(host, ssh_username, ssh_password, ssh_key_path):
                return False
            
            # Upload configuration file
            remote_config_path = f"/home/{ssh_username}/music_player/config.yaml"
            
            # Create a temporary copy of the config with updated paths
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                temp_config_path = temp_file.name
                
                # Copy config but update music_dir to point to the remote location
                temp_config = self.config.copy()
                temp_config['music_dir'] = f"/home/{ssh_username}/music_player/music"
                
                # Write updated config to temp file
                yaml.dump(temp_config, temp_file)
            
            # Upload the temporary config file
            logger.info(f"Uploading configuration to {remote_config_path}")
            result = self.orchestrator.upload_file_to_remote(
                host=host,
                local_path=temp_config_path,
                remote_path=remote_config_path,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                ssh_key_path=ssh_key_path
            )
            
            # Delete the temporary file
            os.unlink(temp_config_path)
            
            if result.get("status") != "success":
                logger.error(f"Failed to upload configuration: {result.get('error')}")
                return False
            
            # Upload music files
            music_dir = self.config.get('music_dir')
            if not music_dir or not os.path.isdir(music_dir):
                logger.warning("Music directory not specified or not found. Skipping music upload.")
                return True
            
            playlist = self.config.get('playlist', [])
            if not playlist:
                logger.warning("No playlist specified. Skipping music upload.")
                return True
            
            # Upload each music file in the playlist
            for track in playlist:
                # Handle absolute paths
                if os.path.isabs(track):
                    local_track_path = track
                # Handle relative paths
                else:
                    local_track_path = os.path.join(music_dir, track)
                
                if not os.path.exists(local_track_path):
                    logger.warning(f"Track not found: {local_track_path}")
                    continue
                
                # Get just the filename for the remote path
                track_filename = os.path.basename(track)
                remote_track_path = f"/home/{ssh_username}/music_player/music/{track_filename}"
                
                logger.info(f"Uploading {track_filename} to {remote_track_path}")
                result = self.orchestrator.upload_file_to_remote(
                    host=host,
                    local_path=local_track_path,
                    remote_path=remote_track_path,
                    ssh_username=ssh_username,
                    ssh_password=ssh_password,
                    ssh_key_path=ssh_key_path
                )
                
                if result.get("status") != "success":
                    logger.warning(f"Failed to upload {track_filename}: {result.get('error')}")
            
            logger.info("Files uploaded successfully")
            return True
                
        except Exception as e:
            logger.error(f"Failed to upload files: {e}")
            return False
    
    def play_music_on_remote(self, host: str, ssh_username: str, ssh_password: Optional[str] = None,
                            ssh_key_path: Optional[str] = None) -> bool:
        """
        Play music on the Raspberry Pi.
        
        Parameters
        ----------
        host : str
            Hostname or IP address of the Raspberry Pi
        ssh_username : str
            SSH username
        ssh_password : str, optional
            SSH password
        ssh_key_path : str, optional
            Path to SSH key file
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.orchestrator:
            logger.error("Orchestrator not available. Cannot play music on remote.")
            return False
        
        try:
            # Remote config path
            remote_config_path = f"/home/{ssh_username}/music_player/config.yaml"
            
            # Get output device from config
            output_device = self.config.get('output_device', 'default')
            
            # Get volume from config
            volume = self.config.get('volume', 0.7)
            
            # Get shuffle and repeat settings
            shuffle = self.config.get('shuffle', False)
            repeat = self.config.get('repeat', False)
            
            # Run music player on remote host
            command = (
                f"cd {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))} && "
                f"python -m examples.audio.music_player "
                f"--config={remote_config_path} "
                f"--output={output_device} "
                f"--volume={volume}"
            )
            
            if shuffle:
                command += " --shuffle"
            if repeat:
                command += " --repeat"
            
            logger.info(f"Running command on remote: {command}")
            
            # Run command on remote host
            result = self.orchestrator.run_command_on_remote(
                host=host,
                command=command,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                ssh_key_path=ssh_key_path
            )
            
            if result.get("status") == "success":
                logger.info("Music player started successfully on remote host")
                return True
            else:
                logger.error(f"Failed to start music player: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to play music on remote: {e}")
            return False
    
    def run_with_orchestrator_shell(self) -> bool:
        """
        Run the music player using the orchestrator shell.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.config:
            logger.error("No configuration loaded. Cannot run with orchestrator shell.")
            return False
        
        # Get remote settings from config
        remote_config = self.config.get('remote', {})
        host = remote_config.get('host')
        port = remote_config.get('port')
        ssh_username = remote_config.get('ssh_username')
        ssh_password = remote_config.get('ssh_password')
        ssh_key_path = remote_config.get('ssh_key_path')
        
        if not host:
            logger.error("Remote host not specified in configuration.")
            return False
        
        if not ssh_username:
            logger.error("SSH username not specified in configuration.")
            return False
        
        # Upload configuration and music files
        if not self.upload_config_and_music(host, ssh_username, ssh_password, ssh_key_path):
            return False
        
        # Play music on remote host
        return self.play_music_on_remote(host, ssh_username, ssh_password, ssh_key_path)
    
    def print_orchestrator_commands(self):
        """Print the commands to run in the orchestrator shell."""
        if not self.config:
            logger.error("No configuration loaded. Cannot print orchestrator commands.")
            return
        
        # Get remote settings from config
        remote_config = self.config.get('remote', {})
        host = remote_config.get('host', '192.168.188.154')
        port = remote_config.get('port', '9515')
        ssh_username = remote_config.get('ssh_username', 'pi')
        ssh_password = remote_config.get('ssh_password', 'raspberry')
        
        # Get output device from config
        output_device = self.config.get('output_device', 'default')
        
        # Get volume from config
        volume = self.config.get('volume', 0.7)
        
        # Get shuffle and repeat settings
        shuffle = self.config.get('shuffle', False)
        repeat = self.config.get('repeat', False)
        
        print("\n" + "=" * 80)
        print("UnitMCP Orchestrator Shell Commands for Music Player")
        print("=" * 80)
        
        print("\n1. Connect to the Raspberry Pi:")
        print(f"   mcp> connect {host} {port}")
        
        print("\n2. Upload configuration and music files:")
        print(f"   mcp> upload {self.config_path} /home/{ssh_username}/music_config.yaml")
        
        # If music directory is specified, print command to upload it
        music_dir = self.config.get('music_dir')
        if music_dir and os.path.isdir(music_dir):
            print(f"   mcp> upload {music_dir} /home/{ssh_username}/music")
        
        print("\n3. Run the music player:")
        command = (
            f"   mcp> run audio --example=music_player "
            f"--config=/home/{ssh_username}/music_config.yaml "
            f"--output={output_device} "
            f"--volume={volume} "
            f"--simulation=false"
        )
        
        if shuffle:
            command += " --shuffle=true"
        if repeat:
            command += " --repeat=true"
        
        print(command)
        
        print("\n4. To stop playback:")
        print("   mcp> stop")
        
        print("\n5. To disconnect:")
        print("   mcp> disconnect")
        
        print("\n" + "=" * 80)
        print("Copy and paste these commands into the orchestrator shell")
        print("=" * 80 + "\n")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Orchestrator Music Player")
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/music_config.yaml",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--print-commands",
        action="store_true",
        help="Print orchestrator shell commands instead of running them"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """
    Main function to run the orchestrator music player.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create orchestrator music player
    player = OrchestratorMusicPlayer(config_path=args.config)
    
    if args.print_commands:
        # Print orchestrator commands
        player.print_orchestrator_commands()
        return 0
    
    try:
        # Run with orchestrator shell
        success = player.run_with_orchestrator_shell()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
