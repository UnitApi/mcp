#!/usr/bin/env python3
"""
UnitMCP Audio Example: Tone Generator

This example demonstrates how to generate and play audio tones with specific
frequencies through different output devices on a Raspberry Pi or other systems.

It can be used to:
- Generate pure sine wave tones with adjustable frequency
- Play tones through headset or speakers
- Control duration, volume, and other audio parameters
- Test audio output devices
"""

import argparse
import logging
import numpy as np
import os
import sys
import time
from typing import Optional, Union, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Try to import sounddevice, with fallback to simulated mode
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    logger.warning("sounddevice module not found. Running in simulation mode.")
    AUDIO_AVAILABLE = False


class ToneGenerator:
    """
    Class for generating and playing audio tones with specific frequencies.
    
    This class provides methods to generate sine wave tones and play them
    through various audio output devices.
    """
    
    def __init__(
        self,
        sample_rate: int = 44100,
        channels: int = 1,
        device: Optional[Union[str, int]] = None,
        simulation: bool = not AUDIO_AVAILABLE
    ):
        """
        Initialize the tone generator.
        
        Parameters
        ----------
        sample_rate : int
            Sample rate in Hz (default: 44100)
        channels : int
            Number of audio channels (default: 1 for mono)
        device : str or int, optional
            Audio output device name or index
        simulation : bool
            Whether to run in simulation mode without actual audio output
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.simulation = simulation
        
        if not self.simulation:
            # Print available audio devices
            self._print_audio_devices()
            
            # Set default device if specified
            if device is not None:
                try:
                    sd.default.device = device
                    logger.info(f"Using audio device: {device}")
                except Exception as e:
                    logger.error(f"Error setting audio device {device}: {e}")
                    logger.info("Using default audio device instead")
    
    def _print_audio_devices(self):
        """Print a list of available audio devices."""
        if not AUDIO_AVAILABLE:
            logger.warning("Audio devices cannot be listed (simulation mode)")
            return
            
        try:
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for i, device in enumerate(devices):
                logger.info(f"  [{i}] {device['name']} (Channels: {device['max_output_channels']})")
        except Exception as e:
            logger.error(f"Error listing audio devices: {e}")
    
    def generate_tone(
        self,
        frequency: float = 1000.0,
        duration: float = 3.0,
        volume: float = 0.5,
        fade_in_out: float = 0.1
    ) -> np.ndarray:
        """
        Generate a sine wave tone with the specified frequency.
        
        Parameters
        ----------
        frequency : float
            Tone frequency in Hz (default: 1000.0)
        duration : float
            Duration of the tone in seconds (default: 3.0)
        volume : float
            Volume level between 0.0 and 1.0 (default: 0.5)
        fade_in_out : float
            Duration of fade in/out in seconds (default: 0.1)
            
        Returns
        -------
        np.ndarray
            NumPy array containing the generated audio data
        """
        # Generate time array
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Generate sine wave
        tone = np.sin(2 * np.pi * frequency * t) * volume
        
        # Apply fade in/out if requested
        if fade_in_out > 0:
            fade_samples = int(fade_in_out * self.sample_rate)
            if fade_samples * 2 < len(tone):  # Ensure we have enough samples
                # Fade in
                fade_in = np.linspace(0, 1, fade_samples)
                tone[:fade_samples] *= fade_in
                
                # Fade out
                fade_out = np.linspace(1, 0, fade_samples)
                tone[-fade_samples:] *= fade_out
        
        # Convert to stereo if needed
        if self.channels == 2:
            tone = np.column_stack((tone, tone))
        
        return tone
    
    def play_tone(
        self,
        frequency: float = 1000.0,
        duration: float = 3.0,
        volume: float = 0.5,
        fade_in_out: float = 0.1,
        blocking: bool = True
    ):
        """
        Generate and play a tone with the specified frequency.
        
        Parameters
        ----------
        frequency : float
            Tone frequency in Hz (default: 1000.0)
        duration : float
            Duration of the tone in seconds (default: 3.0)
        volume : float
            Volume level between 0.0 and 1.0 (default: 0.5)
        fade_in_out : float
            Duration of fade in/out in seconds (default: 0.1)
        blocking : bool
            Whether to block until playback is complete (default: True)
        """
        # Generate the tone
        tone = self.generate_tone(frequency, duration, volume, fade_in_out)
        
        # Play the tone
        if self.simulation:
            logger.info(f"SIMULATION: Playing {frequency}Hz tone for {duration} seconds at volume {volume}")
            if blocking:
                time.sleep(duration)
            logger.info("SIMULATION: Playback complete")
        else:
            try:
                logger.info(f"Playing {frequency}Hz tone for {duration} seconds")
                sd.play(tone, self.sample_rate)
                if blocking:
                    sd.wait()
                    logger.info("Playback complete")
            except Exception as e:
                logger.error(f"Error playing tone: {e}")
    
    def play_sequence(
        self,
        frequencies: List[float],
        durations: Union[List[float], float] = 0.5,
        volume: float = 0.5,
        fade_in_out: float = 0.05,
        gap: float = 0.1
    ):
        """
        Play a sequence of tones with different frequencies.
        
        Parameters
        ----------
        frequencies : List[float]
            List of frequencies in Hz
        durations : List[float] or float
            List of durations in seconds, or a single duration for all tones
        volume : float
            Volume level between 0.0 and 1.0 (default: 0.5)
        fade_in_out : float
            Duration of fade in/out in seconds (default: 0.05)
        gap : float
            Gap between tones in seconds (default: 0.1)
        """
        # Convert single duration to list if needed
        if isinstance(durations, (int, float)):
            durations = [durations] * len(frequencies)
        
        # Ensure durations and frequencies have the same length
        if len(durations) != len(frequencies):
            logger.error("Frequencies and durations must have the same length")
            return
        
        # Play each tone in sequence
        for i, (freq, dur) in enumerate(zip(frequencies, durations)):
            logger.info(f"Playing tone {i+1}/{len(frequencies)}: {freq}Hz for {dur}s")
            self.play_tone(freq, dur, volume, fade_in_out)
            
            # Add gap between tones (except after the last one)
            if i < len(frequencies) - 1 and gap > 0:
                time.sleep(gap)


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate and play audio tones")
    
    parser.add_argument(
        "--frequency", "-f",
        type=float,
        default=1000.0,
        help="Tone frequency in Hz (default: 1000.0)"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=3.0,
        help="Duration of the tone in seconds (default: 3.0)"
    )
    
    parser.add_argument(
        "--volume", "-v",
        type=float,
        default=0.5,
        help="Volume level between 0.0 and 1.0 (default: 0.5)"
    )
    
    parser.add_argument(
        "--sample-rate", "-r",
        type=int,
        default=44100,
        help="Sample rate in Hz (default: 44100)"
    )
    
    parser.add_argument(
        "--channels", "-c",
        type=int,
        choices=[1, 2],
        default=1,
        help="Number of audio channels (1=mono, 2=stereo, default: 1)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Audio output device name or index (default: system default)"
    )
    
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit"
    )
    
    parser.add_argument(
        "--sequence",
        type=str,
        help="Play a sequence of comma-separated frequencies (e.g., '440,880,1320')"
    )
    
    parser.add_argument(
        "--sequence-durations",
        type=str,
        help="Durations for each tone in sequence (e.g., '0.5,0.3,0.7')"
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
    Main function to run the tone generator example.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tone generator
    generator = ToneGenerator(
        sample_rate=args.sample_rate,
        channels=args.channels,
        device=args.output,
        simulation=args.simulation or not AUDIO_AVAILABLE
    )
    
    # List devices and exit if requested
    if args.list_devices:
        return 0
    
    try:
        # Play a sequence of tones if specified
        if args.sequence:
            frequencies = [float(f) for f in args.sequence.split(',')]
            
            if args.sequence_durations:
                durations = [float(d) for d in args.sequence_durations.split(',')]
            else:
                durations = 0.5  # Default duration for sequences
            
            generator.play_sequence(frequencies, durations, args.volume)
        else:
            # Play a single tone
            generator.play_tone(args.frequency, args.duration, args.volume)
        
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
