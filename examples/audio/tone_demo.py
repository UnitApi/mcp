#!/usr/bin/env python3
"""
UnitMCP Audio Example: Tone Generator Demo

This script demonstrates how to use the ToneGenerator class to play
various tones and sound patterns on a Raspberry Pi or other systems.
"""

import argparse
import logging
import sys
import time
from tone_generator import ToneGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def play_single_tone(generator, args):
    """Play a single tone with the specified parameters."""
    logger.info(f"Playing a {args.frequency}Hz tone for {args.duration} seconds")
    generator.play_tone(
        frequency=args.frequency,
        duration=args.duration,
        volume=args.volume,
        fade_in_out=args.fade
    )


def play_scale(generator, args):
    """Play a musical scale."""
    # C major scale frequencies
    c_major = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    
    logger.info("Playing C major scale")
    generator.play_sequence(
        frequencies=c_major,
        durations=0.3,
        volume=args.volume,
        fade_in_out=0.05,
        gap=0.1
    )


def play_alarm(generator, args):
    """Play an alarm pattern."""
    # Alternating high and low frequencies
    alarm_pattern = [880, 660] * 5
    
    logger.info("Playing alarm pattern")
    generator.play_sequence(
        frequencies=alarm_pattern,
        durations=0.3,
        volume=args.volume,
        fade_in_out=0.05,
        gap=0.1
    )


def play_siren(generator, args):
    """Play a siren pattern with frequency sweeps."""
    logger.info("Playing siren pattern")
    
    # Create a frequency sweep (500Hz to 1500Hz and back)
    duration = 5.0
    sample_rate = generator.sample_rate
    t = 0
    dt = 1.0 / sample_rate
    
    # Simulate the sweep in simulation mode
    if generator.simulation:
        logger.info(f"SIMULATION: Playing siren pattern for {duration} seconds")
        time.sleep(duration)
        return
    
    try:
        import numpy as np
        import sounddevice as sd
        
        # Generate time array
        t_array = np.linspace(0, duration, int(duration * sample_rate), False)
        
        # Generate frequency sweep (triangular wave between 500Hz and 1500Hz)
        freq_mod = 500 + 1000 * np.abs(np.sin(2 * np.pi * 0.5 * t_array))
        
        # Generate phase by integrating frequency
        phase = np.cumsum(freq_mod) * 2 * np.pi / sample_rate
        
        # Generate sine wave with modulated frequency
        siren = np.sin(phase) * args.volume
        
        # Apply fade in/out
        fade_samples = int(0.1 * sample_rate)
        if fade_samples * 2 < len(siren):
            fade_in = np.linspace(0, 1, fade_samples)
            siren[:fade_samples] *= fade_in
            
            fade_out = np.linspace(1, 0, fade_samples)
            siren[-fade_samples:] *= fade_out
        
        # Convert to stereo if needed
        if generator.channels == 2:
            siren = np.column_stack((siren, siren))
        
        # Play the siren
        logger.info(f"Playing siren pattern for {duration} seconds")
        sd.play(siren, sample_rate)
        sd.wait()
        logger.info("Siren playback complete")
        
    except Exception as e:
        logger.error(f"Error playing siren: {e}")


def play_beeps(generator, args):
    """Play a series of beeps."""
    # Series of beeps at the same frequency
    beep_count = 5
    beep_freq = args.frequency
    beep_duration = 0.2
    beep_gap = 0.2
    
    logger.info(f"Playing {beep_count} beeps at {beep_freq}Hz")
    
    for i in range(beep_count):
        logger.info(f"Beep {i+1}/{beep_count}")
        generator.play_tone(
            frequency=beep_freq,
            duration=beep_duration,
            volume=args.volume,
            fade_in_out=0.02
        )
        time.sleep(beep_gap)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Tone Generator Demo")
    
    parser.add_argument(
        "--demo", "-d",
        type=str,
        choices=["tone", "scale", "alarm", "siren", "beeps"],
        default="tone",
        help="Demo to run (default: tone)"
    )
    
    parser.add_argument(
        "--frequency", "-f",
        type=float,
        default=1000.0,
        help="Tone frequency in Hz (default: 1000.0)"
    )
    
    parser.add_argument(
        "--duration",
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
        "--fade",
        type=float,
        default=0.1,
        help="Fade in/out duration in seconds (default: 0.1)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Audio output device (default: system default)"
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
    """Main function to run the demo."""
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tone generator
    generator = ToneGenerator(
        sample_rate=args.sample_rate,
        channels=args.channels,
        device=args.output,
        simulation=args.simulation
    )
    
    # Run the selected demo
    try:
        if args.demo == "tone":
            play_single_tone(generator, args)
        elif args.demo == "scale":
            play_scale(generator, args)
        elif args.demo == "alarm":
            play_alarm(generator, args)
        elif args.demo == "siren":
            play_siren(generator, args)
        elif args.demo == "beeps":
            play_beeps(generator, args)
        else:
            logger.error(f"Unknown demo: {args.demo}")
            return 1
        
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
