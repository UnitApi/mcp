#!/usr/bin/env python3
"""
UnitMCP Audio Example: Connection Beep

This example demonstrates how to play a beep sound after successfully
connecting to a Raspberry Pi or other remote device. It can be used
to provide audible feedback when a connection is established.
"""

import argparse
import logging
import os
import socket
import sys
import time
from typing import Optional, Tuple

# Import the ToneGenerator class
try:
    from tone_generator import ToneGenerator
    TONE_GENERATOR_AVAILABLE = True
except ImportError:
    TONE_GENERATOR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ConnectionMonitor:
    """
    Monitor and verify connections to remote devices, playing a beep sound
    when a connection is successfully established.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9515,
        beep_frequency: float = 1000.0,
        beep_duration: float = 0.5,
        beep_volume: float = 0.7,
        output_device: Optional[str] = None,
        simulation: bool = False
    ):
        """
        Initialize the connection monitor.
        
        Parameters
        ----------
        host : str
            Hostname or IP address to connect to
        port : int
            Port number to connect to
        beep_frequency : float
            Frequency of the beep sound in Hz
        beep_duration : float
            Duration of the beep sound in seconds
        beep_volume : float
            Volume of the beep sound (0.0 to 1.0)
        output_device : str, optional
            Audio output device name or index
        simulation : bool
            Whether to run in simulation mode
        """
        self.host = host
        self.port = port
        self.beep_frequency = beep_frequency
        self.beep_duration = beep_duration
        self.beep_volume = beep_volume
        self.output_device = output_device
        self.simulation = simulation
        
        # Initialize tone generator if available
        self.tone_generator = None
        if TONE_GENERATOR_AVAILABLE:
            self.tone_generator = ToneGenerator(
                device=output_device,
                simulation=simulation
            )
        else:
            logger.warning("ToneGenerator not available. No beep sounds will be played.")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the remote host.
        
        Returns
        -------
        Tuple[bool, str]
            A tuple containing a boolean indicating success and a message
        """
        try:
            # Create a socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # 5 second timeout
            
            # Attempt to connect
            logger.info(f"Connecting to {self.host}:{self.port}...")
            s.connect((self.host, self.port))
            
            # Close the socket
            s.close()
            
            return True, f"Connected successfully to {self.host}:{self.port}"
        except socket.timeout:
            return False, f"Connection to {self.host}:{self.port} timed out"
        except ConnectionRefusedError:
            return False, f"Connection to {self.host}:{self.port} refused"
        except Exception as e:
            return False, f"Error connecting to {self.host}:{self.port}: {e}"
    
    def play_connection_beep(self):
        """Play a beep sound to indicate a successful connection."""
        if not self.tone_generator:
            logger.warning("ToneGenerator not available. Cannot play beep sound.")
            return
        
        logger.info(f"Playing connection beep ({self.beep_frequency}Hz)")
        self.tone_generator.play_tone(
            frequency=self.beep_frequency,
            duration=self.beep_duration,
            volume=self.beep_volume,
            fade_in_out=0.05
        )
    
    def play_error_beep(self):
        """Play an error beep sound to indicate a failed connection."""
        if not self.tone_generator:
            logger.warning("ToneGenerator not available. Cannot play error beep sound.")
            return
        
        logger.info("Playing error beep")
        # Play two lower frequency beeps
        self.tone_generator.play_sequence(
            frequencies=[440, 330],
            durations=0.2,
            volume=self.beep_volume,
            fade_in_out=0.05,
            gap=0.1
        )
    
    def monitor_and_beep(self, retry_interval: int = 5, max_retries: int = 0):
        """
        Monitor the connection and play a beep when connected.
        
        Parameters
        ----------
        retry_interval : int
            Interval between connection attempts in seconds
        max_retries : int
            Maximum number of retries (0 for infinite)
        """
        retries = 0
        connected = False
        
        while not connected and (max_retries == 0 or retries < max_retries):
            if retries > 0:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            
            connected, message = self.test_connection()
            logger.info(message)
            
            if connected:
                # Play success beep
                self.play_connection_beep()
                
                # Print connection banner
                print("\n" + "=" * 60)
                print(f"Connected successfully!")
                print(f"mcp ({self.host}:{self.port})> ")
                print("=" * 60 + "\n")
                
                return True
            else:
                # Play error beep
                self.play_error_beep()
                retries += 1
        
        if not connected:
            logger.error("Failed to connect after maximum retries")
            return False


def play_connection_beep(
    frequency: float = 1000.0,
    duration: float = 0.5,
    volume: float = 0.7,
    output_device: Optional[str] = None,
    simulation: bool = False
):
    """
    Play a connection beep sound.
    
    This function can be imported and used by other modules to play a beep
    when a connection is established.
    
    Parameters
    ----------
    frequency : float
        Frequency of the beep sound in Hz
    duration : float
        Duration of the beep sound in seconds
    volume : float
        Volume of the beep sound (0.0 to 1.0)
    output_device : str, optional
        Audio output device name or index
    simulation : bool
        Whether to run in simulation mode
    """
    try:
        if TONE_GENERATOR_AVAILABLE:
            tone_gen = ToneGenerator(
                device=output_device,
                simulation=simulation
            )
            tone_gen.play_tone(
                frequency=frequency,
                duration=duration,
                volume=volume,
                fade_in_out=0.05
            )
            logger.info(f"Played connection beep at {frequency}Hz")
        else:
            logger.warning("ToneGenerator not available. No beep sound played.")
    except Exception as e:
        logger.error(f"Failed to play connection beep: {e}")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Connection Beep Example")
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Hostname or IP address to connect to (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=9515,
        help="Port number to connect to (default: 9515)"
    )
    
    parser.add_argument(
        "--beep-frequency",
        type=float,
        default=1000.0,
        help="Frequency of the beep sound in Hz (default: 1000.0)"
    )
    
    parser.add_argument(
        "--beep-duration",
        type=float,
        default=0.5,
        help="Duration of the beep sound in seconds (default: 0.5)"
    )
    
    parser.add_argument(
        "--beep-volume",
        type=float,
        default=0.7,
        help="Volume of the beep sound (0.0 to 1.0, default: 0.7)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Audio output device name or index (default: system default)"
    )
    
    parser.add_argument(
        "--retry-interval",
        type=int,
        default=5,
        help="Interval between connection attempts in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries (0 for infinite, default: 3)"
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


def main():
    """
    Main function to run the connection beep example.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create connection monitor
    monitor = ConnectionMonitor(
        host=args.host,
        port=args.port,
        beep_frequency=args.beep_frequency,
        beep_duration=args.beep_duration,
        beep_volume=args.beep_volume,
        output_device=args.output,
        simulation=args.simulation
    )
    
    try:
        # Monitor connection and play beep when connected
        success = monitor.monitor_and_beep(
            retry_interval=args.retry_interval,
            max_retries=args.max_retries
        )
        
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
