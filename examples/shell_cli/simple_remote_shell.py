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
    
    def __init__(self, host="localhost", port=22, use_ssh=False, simulation=False, username="pi", key_path=None):
        """Initialize the remote shell."""
        super().__init__()
        self.host = host
        self.port = port
        self.use_ssh = use_ssh
        self.simulation = simulation
        self.username = username
        self.key_path = key_path
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
        Usage: connect [host] [port] [--ssh] [--username USERNAME] [--key-path KEY_PATH] [--password PASSWORD]
        """
        args = arg.split()
        password = None
        
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
            
        # Check for username parameter
        if "--username" in args:
            username_index = args.index("--username")
            if username_index + 1 < len(args):
                self.username = args[username_index + 1]
                
        # Check for key-path parameter
        if "--key-path" in args:
            key_path_index = args.index("--key-path")
            if key_path_index + 1 < len(args):
                self.key_path = args[key_path_index + 1]
        
        # Check for password parameter
        if "--password" in args:
            password_index = args.index("--password")
            if password_index + 1 < len(args):
                password = args[password_index + 1]
        
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
                print(f"Connecting to {self.host}:{self.port} via SSH with username '{self.username}'...")
                
                # Connect with the appropriate authentication method
                if self.key_path:
                    self.ssh_client.connect(self.host, port=self.port, username=self.username, key_filename=self.key_path, timeout=5)
                elif password:
                    self.ssh_client.connect(self.host, port=self.port, username=self.username, password=password, timeout=5)
                else:
                    self.ssh_client.connect(self.host, port=self.port, username=self.username, timeout=5)
                
                # Upload the helper script to the remote device
                sftp = self.ssh_client.open_sftp()
                local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rpi_gpio_helper.py")
                remote_path = "/tmp/rpi_gpio_helper.py"
                
                try:
                    sftp.put(local_path, remote_path)
                    sftp.chmod(remote_path, 0o755)  # Make executable
                    print(f"Uploaded GPIO helper script to {remote_path}")
                    
                    # Check if RPi.GPIO is installed and install if needed
                    print("Checking for required libraries...")
                    stdin, stdout, stderr = self.ssh_client.exec_command("python3 -c 'import RPi.GPIO' 2>/dev/null || echo 'NOT_INSTALLED'")
                    if 'NOT_INSTALLED' in stdout.read().decode():
                        print("RPi.GPIO not found. Installing...")
                        stdin, stdout, stderr = self.ssh_client.exec_command("sudo apt-get update && sudo apt-get install -y python3-rpi.gpio")
                        while not stdout.channel.exit_status_ready():
                            if stdout.channel.recv_ready():
                                data = stdout.channel.recv(1024).decode('utf-8')
                                print(data, end='')
                        print("Installation complete.")
                    else:
                        print("RPi.GPIO is already installed.")
                except Exception as e:
                    print(f"Warning: Could not upload GPIO helper script or install libraries: {e}")
                finally:
                    sftp.close()
                
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
        
        # Use the helper script for GPIO control
        if value:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_gpio; handle_gpio(['{pin}', '{mode}', '{value}'])\""
        else:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_gpio; handle_gpio(['{pin}', '{mode}'])\""
        
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
        
        # Use the helper script for LED control
        params_str = ", ".join([f"'{p}'" for p in params])
        if params_str:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_led; handle_led(['{name}', '{action}', {params_str}])\""
        else:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_led; handle_led(['{name}', '{action}'])\""
        
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
            print("  connect [host] [port] [--ssh] [--username USERNAME] [--key-path KEY_PATH] [--password PASSWORD] - Connect to a remote device")
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
            print("  connect 192.168.1.100 22 --ssh --username pi --key-path /path/to/key")
            print("  gpio 17 out 1")
            print("  led led1 setup 17")
            print("  led led1 on")
            print("  set pin 17")
            print("  led led1 setup ${pin}")
    
    def do_system(self, arg):
        """
        Execute system commands on the remote device.
        Usage: system <action> [params]
        Examples:
            system info    # Show system information
            system temp    # Show CPU temperature
        """
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        if not arg:
            print("Usage: system <action> [params]")
            return
        
        args = arg.split()
        action = args[0].lower()
        params = args[1:] if len(args) > 1 else []
        
        if self.simulation:
            if action == "info":
                print("[SIMULATION] System Information:")
                print("  CPU: 4-core ARM Cortex-A72")
                print("  Memory: 4GB RAM")
                print("  Disk: 32GB SD Card (16GB used)")
                print("  OS: Raspberry Pi OS Bullseye")
            elif action == "temp":
                print("[SIMULATION] CPU Temperature: 42.5°C")
            return
        
        # Use the helper script for system commands
        params_str = ", ".join([f"'{p}'" for p in params])
        if params_str:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_system; handle_system(['{action}', {params_str}])\""
        else:
            command = f"python3 -c \"import sys; sys.path.append('/tmp'); from rpi_gpio_helper import handle_system; handle_system(['{action}'])\""
        
        self.do_exec(command)

def main():
    """Main entry point for the remote shell."""
    parser = argparse.ArgumentParser(description="Remote Device Control Shell")
    parser.add_argument("--host", default="localhost", help="Hostname or IP address")
    parser.add_argument("--port", type=int, default=22, help="Port number")
    parser.add_argument("--ssh", action="store_true", help="Use SSH for connection")
    parser.add_argument("--username", default="pi", help="Username for SSH connection")
    parser.add_argument("--key-path", help="Path to SSH private key file")
    parser.add_argument("--password", help="Password for SSH connection")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    args = parser.parse_args()
    
    # Create and start the shell
    shell = RemoteShell(
        host=args.host,
        port=args.port,
        use_ssh=args.ssh,
        simulation=args.simulation,
        username=args.username,
        key_path=args.key_path
    )
    shell.cmdloop()

if __name__ == "__main__":
    main()
