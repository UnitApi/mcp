#!/usr/bin/env python3
"""
Simple Remote Shell Example

This example demonstrates how to create a simple shell interface for
remote device control without requiring the full UnitMCP installation.
It uses standard Python libraries for network communication.

Features:
- Connect to remote devices over SSH or TCP
- Execute commands on remote devices
- Interactive shell interface
- Simulation mode for testing without hardware

Usage:
    python simple_remote_shell.py [--host HOSTNAME] [--port PORT] [--ssh]
"""

import argparse
import cmd
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# Check if paramiko is installed for SSH support
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    print("SSH support not available. Install paramiko for SSH functionality.")
    print("pip install paramiko")

class RemoteShell(cmd.Cmd):
    """Interactive shell for remote device control."""
    
    intro = "Remote Device Control Shell. Type help or ? to list commands.\n"
    prompt = "(remote) "
    
    def __init__(self, host="localhost", port=22, use_ssh=False, simulation=False):
        """Initialize the remote shell."""
        super().__init__()
        self.host = host
        self.port = port
        self.use_ssh = use_ssh
        self.simulation = simulation
        self.connected = False
        self.ssh_client = None
        self.tcp_socket = None
        self.variables = {}
        
        # Set simulation mode from environment variable if present
        if os.environ.get("SIMULATION") == "1":
            self.simulation = True
            print("Running in simulation mode")
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
    
    def do_connect(self, arg):
        """
        Connect to a remote device.
        Usage: connect [host] [port] [--ssh]
        """
        args = arg.split()
        if len(args) >= 1:
            self.host = args[0]
        if len(args) >= 2:
            try:
                self.port = int(args[1])
            except ValueError:
                print(f"Invalid port: {args[1]}")
                return
        if "--ssh" in args:
            self.use_ssh = True
        
        if self.simulation:
            print(f"[SIMULATION] Connecting to {self.host}:{self.port} via {'SSH' if self.use_ssh else 'TCP'}")
            self.connected = True
            self.prompt = f"({self.host}) "
            return
        
        try:
            if self.use_ssh:
                if not SSH_AVAILABLE:
                    print("SSH support not available. Install paramiko for SSH functionality.")
                    return
                
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"Connecting to {self.host}:{self.port} via SSH...")
                self.ssh_client.connect(self.host, port=self.port, timeout=5)
                self.connected = True
            else:
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.settimeout(5)
                print(f"Connecting to {self.host}:{self.port} via TCP...")
                self.tcp_socket.connect((self.host, self.port))
                self.connected = True
            
            print(f"Connected to {self.host}:{self.port}")
            self.prompt = f"({self.host}) "
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
    
    def do_disconnect(self, arg):
        """Disconnect from the remote device."""
        if self.simulation:
            print("[SIMULATION] Disconnected")
            self.connected = False
            self.prompt = "(remote) "
            return
        
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
        if self.tcp_socket:
            self.tcp_socket.close()
            self.tcp_socket = None
        
        self.connected = False
        self.prompt = "(remote) "
        print("Disconnected")
    
    def do_status(self, arg):
        """Show connection status."""
        if self.connected:
            print(f"Connected to {self.host}:{self.port} via {'SSH' if self.use_ssh else 'TCP'}")
        else:
            print("Not connected")
    
    def do_exec(self, arg):
        """
        Execute a command on the remote device.
        Usage: exec <command>
        """
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        if not arg:
            print("No command specified")
            return
        
        if self.simulation:
            print(f"[SIMULATION] Executing: {arg}")
            time.sleep(0.5)
            print(f"[SIMULATION] Command executed successfully")
            return
        
        try:
            if self.ssh_client:
                stdin, stdout, stderr = self.ssh_client.exec_command(arg)
                output = stdout.read().decode()
                error = stderr.read().decode()
                if output:
                    print(output)
                if error:
                    print(f"Error: {error}")
            elif self.tcp_socket:
                self.tcp_socket.sendall(f"{arg}\n".encode())
                response = self.tcp_socket.recv(4096).decode()
                print(response)
        except Exception as e:
            print(f"Command execution failed: {e}")
    
    def do_gpio(self, arg):
        """
        Control GPIO pins on the remote device.
        Usage: gpio <pin> <mode> [value]
        Examples:
            gpio 17 out 1    # Set pin 17 as output with value 1
            gpio 18 in       # Set pin 18 as input
            gpio 17 read     # Read value of pin 17
        """
        args = arg.split()
        if len(args) < 2:
            print("Usage: gpio <pin> <mode> [value]")
            return
        
        pin = args[0]
        mode = args[1].lower()
        value = args[2] if len(args) > 2 else None
        
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        if self.simulation:
            if mode == "out" and value:
                print(f"[SIMULATION] Setting GPIO {pin} to OUTPUT with value {value}")
            elif mode == "in":
                print(f"[SIMULATION] Setting GPIO {pin} to INPUT")
            elif mode == "read":
                print(f"[SIMULATION] Reading GPIO {pin}: {'1' if int(pin) % 2 == 0 else '0'}")
            return
        
        command = f"gpio {pin} {mode}"
        if value:
            command += f" {value}"
        
        self.do_exec(command)
    
    def do_led(self, arg):
        """
        Control LED devices on the remote device.
        Usage: led <name> <action> [params]
        Examples:
            led led1 setup 17      # Set up LED on pin 17
            led led1 on            # Turn on LED
            led led1 off           # Turn off LED
            led led1 blink 0.5 0.5 # Blink LED with on/off times
        """
        args = arg.split()
        if len(args) < 2:
            print("Usage: led <name> <action> [params]")
            return
        
        name = args[0]
        action = args[1].lower()
        params = args[2:] if len(args) > 2 else []
        
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        if self.simulation:
            if action == "setup":
                print(f"[SIMULATION] Setting up LED {name} on pin {params[0] if params else 'unknown'}")
            elif action == "on":
                print(f"[SIMULATION] Turning on LED {name}")
            elif action == "off":
                print(f"[SIMULATION] Turning off LED {name}")
            elif action == "blink":
                on_time = params[0] if params else "0.5"
                off_time = params[1] if len(params) > 1 else "0.5"
                print(f"[SIMULATION] Blinking LED {name} with on_time={on_time}, off_time={off_time}")
            return
        
        command = f"led {name} {action}"
        if params:
            command += " " + " ".join(params)
        
        self.do_exec(command)
    
    def do_set(self, arg):
        """
        Set a variable.
        Usage: set <name> <value>
        """
        args = arg.split()
        if len(args) < 2:
            print("Usage: set <name> <value>")
            return
        
        name = args[0]
        value = " ".join(args[1:])
        
        self.variables[name] = value
        print(f"Set {name} = {value}")
    
    def do_get(self, arg):
        """
        Get a variable value.
        Usage: get <name>
        """
        if not arg:
            print("Usage: get <name>")
            return
        
        name = arg.strip()
        if name in self.variables:
            print(f"{name} = {self.variables[name]}")
        else:
            print(f"Variable {name} not found")
    
    def do_vars(self, arg):
        """List all variables."""
        if not self.variables:
            print("No variables defined")
            return
        
        for name, value in self.variables.items():
            print(f"{name} = {value}")
    
    def do_sleep(self, arg):
        """
        Sleep for a specified number of seconds.
        Usage: sleep <seconds>
        """
        try:
            seconds = float(arg)
            print(f"Sleeping for {seconds} seconds...")
            time.sleep(seconds)
        except ValueError:
            print(f"Invalid sleep duration: {arg}")
    
    def do_exit(self, arg):
        """Exit the shell."""
        if self.connected:
            self.do_disconnect("")
        print("Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the shell."""
        return self.do_exit(arg)
    
    def do_help(self, arg):
        """Show help message."""
        if arg:
            # Show help for a specific command
            super().do_help(arg)
        else:
            # Show general help
            print("\nRemote Device Control Shell")
            print("==========================")
            print("This shell allows you to control remote devices over SSH or TCP.")
            print("\nConnection Commands:")
            print("  connect [host] [port] [--ssh] - Connect to a remote device")
            print("  disconnect                    - Disconnect from the remote device")
            print("  status                        - Show connection status")
            print("\nDevice Control Commands:")
            print("  gpio <pin> <mode> [value]     - Control GPIO pins")
            print("  led <name> <action> [params]  - Control LED devices")
            print("  exec <command>                - Execute a command on the remote device")
            print("\nVariable Commands:")
            print("  set <name> <value>            - Set a variable")
            print("  get <name>                    - Get a variable value")
            print("  vars                          - List all variables")
            print("\nOther Commands:")
            print("  sleep <seconds>               - Sleep for a specified number of seconds")
            print("  exit, quit                    - Exit the shell")
            print("  help, ?                       - Show this help message")
            print("\nExamples:")
            print("  connect 192.168.1.100 22 --ssh")
            print("  gpio 17 out 1")
            print("  led led1 setup 17")
            print("  led led1 on")
            print("  set pin 17")
            print("  led led1 setup ${pin}")

def main():
    """Main entry point for the remote shell."""
    parser = argparse.ArgumentParser(description="Remote Device Control Shell")
    parser.add_argument("--host", default="localhost", help="Hostname or IP address")
    parser.add_argument("--port", type=int, default=22, help="Port number")
    parser.add_argument("--ssh", action="store_true", help="Use SSH for connection")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    args = parser.parse_args()
    
    # Create and start the shell
    shell = RemoteShell(
        host=args.host,
        port=args.port,
        use_ssh=args.ssh,
        simulation=args.simulation
    )
    shell.cmdloop()

if __name__ == "__main__":
    main()
