#!/usr/bin/env python3
"""
Raspberry Pi GPIO Helper Script

This script provides a command-line interface for controlling GPIO pins and LEDs
on a Raspberry Pi. It is designed to be used with the simple_remote_shell.py
script for remote control.

Usage:
    python rpi_gpio_helper.py gpio <pin> <mode> [value]
    python rpi_gpio_helper.py led <name> <action> [params]
"""

import sys
import time
import argparse
import json
import os
from pathlib import Path

# Try to import RPi.GPIO, use simulation mode if not available
try:
    import RPi.GPIO as GPIO
    SIMULATION = False
except ImportError:
    SIMULATION = True
    print("WARNING: RPi.GPIO not available. Running in simulation mode.")

# LED configuration storage
LED_CONFIG_FILE = Path.home() / ".led_config.json"

def setup_gpio():
    """Set up GPIO module."""
    if not SIMULATION:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

def load_led_config():
    """Load LED configuration from file."""
    if LED_CONFIG_FILE.exists():
        try:
            with open(LED_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading LED config: {e}")
    return {}

def save_led_config(config):
    """Save LED configuration to file."""
    try:
        with open(LED_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving LED config: {e}")

def handle_gpio(args):
    """Handle GPIO commands."""
    if len(args) < 2:
        print("Usage: gpio <pin> <mode> [value]")
        return 1
    
    pin = int(args[0])
    mode = args[1].lower()
    
    if SIMULATION:
        if mode == "out" and len(args) > 2:
            value = int(args[2])
            print(f"[SIMULATION] Setting GPIO {pin} to OUTPUT with value {value}")
        elif mode == "in":
            print(f"[SIMULATION] Setting GPIO {pin} to INPUT")
        elif mode == "read":
            print(f"[SIMULATION] Reading GPIO {pin}: {'1' if pin % 2 == 0 else '0'}")
        elif mode == "list":
            print("[SIMULATION] Available GPIO pins: 2, 3, 4, 17, 18, 27, 22, 23, 24, 25, 5, 6, 12, 13, 19, 16, 26, 20, 21")
        return 0
    
    setup_gpio()
    
    if mode == "out":
        GPIO.setup(pin, GPIO.OUT)
        if len(args) > 2:
            value = int(args[2])
            GPIO.output(pin, value)
            print(f"Set GPIO {pin} to OUTPUT with value {value}")
        else:
            print(f"Set GPIO {pin} to OUTPUT")
    elif mode == "in":
        GPIO.setup(pin, GPIO.IN)
        print(f"Set GPIO {pin} to INPUT")
    elif mode == "read":
        if GPIO.gpio_function(pin) == GPIO.IN:
            value = GPIO.input(pin)
            print(f"GPIO {pin} value: {value}")
        else:
            GPIO.setup(pin, GPIO.IN)
            value = GPIO.input(pin)
            print(f"GPIO {pin} value: {value}")
    elif mode == "list":
        # List available GPIO pins on Raspberry Pi
        available_pins = [2, 3, 4, 17, 18, 27, 22, 23, 24, 25, 5, 6, 12, 13, 19, 16, 26, 20, 21]
        print(f"Available GPIO pins: {', '.join(map(str, available_pins))}")
    else:
        print(f"Unknown mode: {mode}")
        return 1
    
    return 0

def handle_led(args):
    """Handle LED commands."""
    if len(args) < 2:
        print("Usage: led <name> <action> [params]")
        return 1
    
    name = args[0]
    action = args[1].lower()
    params = args[2:] if len(args) > 2 else []
    
    led_config = load_led_config()
    
    if SIMULATION:
        if action == "setup":
            pin = int(params[0]) if params else 0
            print(f"[SIMULATION] Setting up LED {name} on pin {pin}")
            led_config[name] = {"pin": pin}
            save_led_config(led_config)
        elif action == "on":
            print(f"[SIMULATION] Turning on LED {name}")
        elif action == "off":
            print(f"[SIMULATION] Turning off LED {name}")
        elif action == "blink":
            on_time = float(params[0]) if params else 0.5
            off_time = float(params[1]) if len(params) > 1 else 0.5
            count = int(params[2]) if len(params) > 2 else 5
            print(f"[SIMULATION] Blinking LED {name} {count} times with on_time={on_time}, off_time={off_time}")
            for i in range(count):
                print(f"[SIMULATION] Blink {i+1}/{count}: ON")
                time.sleep(on_time)
                print(f"[SIMULATION] Blink {i+1}/{count}: OFF")
                time.sleep(off_time)
        elif action == "list":
            if led_config:
                print("Configured LEDs:")
                for led_name, config in led_config.items():
                    print(f"  {led_name}: pin {config.get('pin', 'unknown')}")
            else:
                print("No LEDs configured")
        return 0
    
    setup_gpio()
    
    if action == "setup":
        if not params:
            print("Missing pin number for LED setup")
            return 1
        
        pin = int(params[0])
        GPIO.setup(pin, GPIO.OUT)
        led_config[name] = {"pin": pin}
        save_led_config(led_config)
        print(f"LED {name} set up on pin {pin}")
    
    elif action == "on" or action == "off" or action == "blink":
        if name not in led_config:
            print(f"LED {name} not configured. Use 'led {name} setup <pin>' first.")
            return 1
        
        pin = led_config[name]["pin"]
        GPIO.setup(pin, GPIO.OUT)
        
        if action == "on":
            GPIO.output(pin, GPIO.HIGH)
            print(f"LED {name} turned ON")
        
        elif action == "off":
            GPIO.output(pin, GPIO.LOW)
            print(f"LED {name} turned OFF")
        
        elif action == "blink":
            on_time = float(params[0]) if params else 0.5
            off_time = float(params[1]) if len(params) > 1 else 0.5
            count = int(params[2]) if len(params) > 2 else 5
            
            print(f"Blinking LED {name} {count} times with on_time={on_time}, off_time={off_time}")
            for i in range(count):
                print(f"Blink {i+1}/{count}: ON")
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(on_time)
                print(f"Blink {i+1}/{count}: OFF")
                GPIO.output(pin, GPIO.LOW)
                time.sleep(off_time)
    
    elif action == "list":
        if led_config:
            print("Configured LEDs:")
            for led_name, config in led_config.items():
                print(f"  {led_name}: pin {config.get('pin', 'unknown')}")
        else:
            print("No LEDs configured")
    
    else:
        print(f"Unknown action: {action}")
        return 1
    
    return 0

def handle_system(args):
    """Handle system commands."""
    if not args:
        print("Usage: system <action> [params]")
        return 1
    
    action = args[0].lower()
    
    if SIMULATION:
        if action == "info":
            print("[SIMULATION] System Information:")
            print("  CPU: 4-core ARM Cortex-A72")
            print("  Memory: 4GB RAM")
            print("  Disk: 32GB SD Card (16GB used)")
            print("  OS: Raspberry Pi OS Bullseye")
        elif action == "temp":
            print("[SIMULATION] CPU Temperature: 42.5°C")
        return 0
    
    if action == "info":
        try:
            # Get system information
            import platform
            import psutil
            
            print("System Information:")
            print(f"  Hostname: {platform.node()}")
            print(f"  Platform: {platform.platform()}")
            print(f"  CPU: {platform.processor()}")
            
            # Memory information
            mem = psutil.virtual_memory()
            print(f"  Memory: {mem.total / (1024**3):.1f}GB total, {mem.used / (1024**3):.1f}GB used")
            
            # Disk information
            disk = psutil.disk_usage('/')
            print(f"  Disk: {disk.total / (1024**3):.1f}GB total, {disk.used / (1024**3):.1f}GB used")
            
        except ImportError:
            # Fallback if psutil is not available
            print("System Information:")
            print(f"  Hostname: {platform.node()}")
            print(f"  Platform: {platform.platform()}")
            print(f"  CPU: {platform.processor()}")
            
            # Use system commands as fallback
            import subprocess
            try:
                mem_info = subprocess.check_output("free -h", shell=True).decode()
                print(f"  Memory Info:")
                print(f"    {mem_info.split(chr(10))[1]}")
                
                disk_info = subprocess.check_output("df -h /", shell=True).decode()
                print(f"  Disk Info:")
                print(f"    {disk_info.split(chr(10))[1]}")
            except:
                print("  Detailed memory and disk info not available")
    
    elif action == "temp":
        try:
            # Read CPU temperature
            temp_file = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = float(f.read().strip()) / 1000
                print(f"CPU Temperature: {temp:.1f}°C")
            else:
                # Alternative method using vcgencmd
                import subprocess
                temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode()
                print(f"CPU {temp}")
        except Exception as e:
            print(f"Error reading temperature: {e}")
    
    else:
        print(f"Unknown system action: {action}")
        return 1
    
    return 0

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: rpi_gpio_helper.py <command> [args...]")
        print("Commands: gpio, led, system")
        return 1
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if command == "gpio":
        return handle_gpio(args)
    elif command == "led":
        return handle_led(args)
    elif command == "system":
        return handle_system(args)
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
