#!/usr/bin/env python3
"""
Raspberry Pi GPIO Helper Script

This script provides a command-line interface for controlling GPIO pins and LEDs
on a Raspberry Pi. It is designed to be used with the simple_remote_shell.py
script for remote control.

Features:
- GPIO pin control (input/output, read/write)
- LED control (setup, on, off, blink)
- System information retrieval
- Real-time GPIO streaming

Usage:
    python rpi_gpio_helper.py gpio <pin> <mode> [value]
    python rpi_gpio_helper.py led <name> <action> [params]
    python rpi_gpio_helper.py stream <pin1,pin2,...> [interval]
"""

import sys
import time
import argparse
import json
import os
import threading
import socket
import signal
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

# Streaming configuration
DEFAULT_STREAM_PORT = 8765
DEFAULT_STREAM_INTERVAL = 0.1  # seconds

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

def handle_stream(args):
    """
    Handle GPIO streaming.
    
    This function sets up a streaming server that continuously monitors
    the specified GPIO pins and sends updates to connected clients.
    """
    if not args:
        print("Usage: stream <pin1,pin2,...> [interval] [port]")
        return 1
    
    # Parse pins
    try:
        pins = [int(pin.strip()) for pin in args[0].split(',')]
    except ValueError:
        print("Invalid pin format. Use comma-separated numbers (e.g., 17,18,27)")
        return 1
    
    # Parse interval
    interval = DEFAULT_STREAM_INTERVAL
    if len(args) > 1:
        try:
            interval = float(args[1])
            if interval < 0.01:
                print("Warning: Very short intervals may cause high CPU usage")
                interval = 0.01
        except ValueError:
            print(f"Invalid interval: {args[1]}. Using default: {DEFAULT_STREAM_INTERVAL}s")
    
    # Parse port
    port = DEFAULT_STREAM_PORT
    if len(args) > 2:
        try:
            port = int(args[2])
        except ValueError:
            print(f"Invalid port: {args[2]}. Using default: {DEFAULT_STREAM_PORT}")
    
    if SIMULATION:
        print(f"[SIMULATION] Starting GPIO streaming server for pins {pins} with interval {interval}s on port {port}")
        try:
            # Create a simulation streaming server
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', port))
            server.listen(5)
            print(f"[SIMULATION] Streaming server started on port {port}")
            
            # Set up signal handler for clean shutdown
            def signal_handler(sig, frame):
                print("\n[SIMULATION] Stopping streaming server...")
                server.close()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            # Accept connections and handle them
            while True:
                client, addr = server.accept()
                print(f"[SIMULATION] Client connected: {addr}")
                
                # Start a thread to handle this client
                threading.Thread(
                    target=handle_simulation_client,
                    args=(client, addr, pins, interval),
                    daemon=True
                ).start()
        
        except Exception as e:
            print(f"[SIMULATION] Error in streaming server: {e}")
            return 1
        
        return 0
    
    # Real GPIO streaming
    setup_gpio()
    
    # Set up pins for input
    for pin in pins:
        try:
            GPIO.setup(pin, GPIO.IN)
            print(f"Set up GPIO {pin} for streaming")
        except Exception as e:
            print(f"Error setting up GPIO {pin}: {e}")
            return 1
    
    try:
        # Create a streaming server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen(5)
        print(f"GPIO streaming server started on port {port}")
        
        # Set up signal handler for clean shutdown
        def signal_handler(sig, frame):
            print("\nStopping streaming server...")
            server.close()
            GPIO.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Accept connections and handle them
        while True:
            client, addr = server.accept()
            print(f"Client connected: {addr}")
            
            # Start a thread to handle this client
            threading.Thread(
                target=handle_client,
                args=(client, addr, pins, interval),
                daemon=True
            ).start()
    
    except Exception as e:
        print(f"Error in streaming server: {e}")
        return 1
    
    return 0

def handle_client(client, addr, pins, interval):
    """Handle a client connection for GPIO streaming."""
    try:
        # Send initial configuration
        config = {
            'pins': pins,
            'interval': interval,
            'timestamp': time.time()
        }
        client.send((json.dumps(config) + '\n').encode())
        
        # Track previous states to only send updates on changes
        prev_states = {pin: None for pin in pins}
        
        while True:
            # Read current pin states
            states = {}
            changed = False
            
            for pin in pins:
                try:
                    state = GPIO.input(pin)
                    states[pin] = state
                    
                    # Check if state changed
                    if prev_states[pin] != state:
                        changed = True
                        prev_states[pin] = state
                except Exception as e:
                    states[pin] = "error"
                    print(f"Error reading GPIO {pin}: {e}")
            
            # Send update if any state changed or periodically
            if changed or time.time() % 1 < interval:
                update = {
                    'timestamp': time.time(),
                    'states': states
                }
                try:
                    client.send((json.dumps(update) + '\n').encode())
                except:
                    # Client disconnected
                    break
            
            time.sleep(interval)
    
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        try:
            client.close()
            print(f"Client disconnected: {addr}")
        except:
            pass

def handle_simulation_client(client, addr, pins, interval):
    """Handle a client connection for simulated GPIO streaming."""
    try:
        # Send initial configuration
        config = {
            'pins': pins,
            'interval': interval,
            'timestamp': time.time(),
            'simulation': True
        }
        client.send((json.dumps(config) + '\n').encode())
        
        # Generate simulated pin states
        import random
        
        # Start with random states
        states = {pin: random.randint(0, 1) for pin in pins}
        
        # Periodically update and send states
        while True:
            # Randomly change some states (20% chance per pin)
            for pin in pins:
                if random.random() < 0.2:
                    states[pin] = 1 - states[pin]  # Toggle between 0 and 1
            
            # Send update
            update = {
                'timestamp': time.time(),
                'states': states,
                'simulation': True
            }
            try:
                client.send((json.dumps(update) + '\n').encode())
            except:
                # Client disconnected
                break
            
            time.sleep(interval)
    
    except Exception as e:
        print(f"[SIMULATION] Error handling client {addr}: {e}")
    finally:
        try:
            client.close()
            print(f"[SIMULATION] Client disconnected: {addr}")
        except:
            pass

def handle_stream_client(args):
    """
    Connect to a GPIO streaming server as a client.
    
    This function connects to a remote GPIO streaming server and
    displays real-time updates of GPIO pin states.
    """
    if len(args) < 1:
        print("Usage: stream_client <host> [port]")
        return 1
    
    host = args[0]
    port = DEFAULT_STREAM_PORT
    
    if len(args) > 1:
        try:
            port = int(args[1])
        except ValueError:
            print(f"Invalid port: {args[1]}. Using default: {DEFAULT_STREAM_PORT}")
    
    try:
        # Connect to the streaming server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {host}:{port}...")
        client.connect((host, port))
        print("Connected to GPIO streaming server")
        
        # Set up signal handler for clean shutdown
        def signal_handler(sig, frame):
            print("\nDisconnecting from streaming server...")
            client.close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Receive and display updates
        buffer = ""
        while True:
            data = client.recv(4096).decode()
            if not data:
                break
            
            buffer += data
            
            # Process complete JSON objects
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    update = json.loads(line)
                    
                    # Display initial configuration
                    if 'pins' in update:
                        print(f"Streaming configuration:")
                        print(f"  Pins: {update['pins']}")
                        print(f"  Interval: {update['interval']}s")
                        if update.get('simulation'):
                            print("  Mode: SIMULATION")
                        print("\nPin states (1=HIGH, 0=LOW):")
                    
                    # Display pin state updates
                    elif 'states' in update:
                        timestamp = time.strftime('%H:%M:%S', time.localtime(update['timestamp']))
                        states_str = ", ".join([f"GPIO {pin}={state}" for pin, state in update['states'].items()])
                        print(f"[{timestamp}] {states_str}")
                
                except json.JSONDecodeError:
                    print(f"Error parsing update: {line}")
    
    except Exception as e:
        print(f"Error in streaming client: {e}")
        return 1
    
    return 0

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: rpi_gpio_helper.py <command> [args...]")
        print("Commands: gpio, led, system, stream, stream_client")
        return 1
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if command == "gpio":
        return handle_gpio(args)
    elif command == "led":
        return handle_led(args)
    elif command == "system":
        return handle_system(args)
    elif command == "stream":
        return handle_stream(args)
    elif command == "stream_client":
        return handle_stream_client(args)
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
