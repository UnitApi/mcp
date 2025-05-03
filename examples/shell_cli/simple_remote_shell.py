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
- Process monitoring and management for concurrent operations
- Real-time GPIO streaming from Raspberry Pi to client PC

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
import threading
import json
import select
import signal
from pathlib import Path

# Import the process manager
try:
    from process_manager import get_instance as get_process_manager
    PROCESS_MANAGER_AVAILABLE = True
except ImportError:
    PROCESS_MANAGER_AVAILABLE = False
    print("Process manager not available. Concurrent process monitoring disabled.")
    print("Install process_manager.py in the same directory for enhanced stability.")

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
        
        # Process monitoring
        self.process_manager = get_process_manager() if PROCESS_MANAGER_AVAILABLE else None
        self.monitor_thread = None
        self.monitoring_active = False
        
        # Set simulation mode from environment variable if present
        if os.environ.get("SIMULATION") == "1":
            self.simulation = True
            print("Running in simulation mode")
        
        # Start the anomaly detection thread if process manager is available
        if self.process_manager:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start the process monitoring thread."""
        if self.process_manager and not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_processes,
                daemon=True
            )
            self.monitor_thread.start()
            print("Process monitoring active")
    
    def stop_monitoring(self):
        """Stop the process monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_processes(self):
        """Monitor processes for anomalies."""
        anomaly_count = 0
        last_check_time = time.time()
        
        while self.monitoring_active:
            if self.process_manager:
                current_time = time.time()
                check_interval = 5  # Normal check interval in seconds
                
                # Adjust check interval based on system load
                if anomaly_count > 5:
                    # More frequent checks if we've seen anomalies recently
                    check_interval = 2
                
                # Only check if enough time has passed
                if current_time - last_check_time >= check_interval:
                    last_check_time = current_time
                    
                    # Check for anomalies
                    fixed, remaining = self.process_manager.handle_anomalies(auto_fix=True)
                    
                    # Reset anomaly count if no issues found
                    if not fixed and not remaining:
                        anomaly_count = max(0, anomaly_count - 1)
                    else:
                        anomaly_count += len(fixed) + len(remaining)
                    
                    # Log any fixed anomalies
                    for anomaly in fixed:
                        anomaly_type = anomaly.get('type', 'unknown')
                        if anomaly_type == 'timeout' or anomaly_type == 'long_running':
                            print(f"\nWARNING: Terminated process {anomaly.get('pid')} due to {anomaly_type} condition")
                            # Restore prompt after printing warning
                            print(f"\n{self.prompt}", end='', flush=True)
                        elif anomaly_type == 'resource_contention_fixed':
                            print(f"\nWARNING: Resolved resource contention on {anomaly.get('resource')} by terminating process {anomaly.get('terminated_pid')}")
                            print(f"\n{self.prompt}", end='', flush=True)
                    
                    # Report any remaining anomalies
                    for anomaly in remaining:
                        anomaly_type = anomaly.get('type', 'unknown')
                        if anomaly_type == 'resource_contention':
                            print(f"\nWARNING: Resource contention detected on {anomaly.get('resource')} between processes {anomaly.get('pids')}")
                            print(f"\n{self.prompt}", end='', flush=True)
                        elif anomaly_type == 'zombie_process':
                            # Try to clean up zombie processes
                            pid = anomaly.get('pid')
                            if pid:
                                try:
                                    os.kill(pid, signal.SIGKILL)
                                    print(f"\nWARNING: Terminated zombie process {pid}")
                                    print(f"\n{self.prompt}", end='', flush=True)
                                except OSError:
                                    pass
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
    
    def emptyline(self):
        """Do nothing on empty line."""
        pass
    
    def do_connect(self, arg):
        """
        Connect to a remote device.
        Usage: connect [host] [port] [--ssh] [--username USERNAME] [--key-path KEY_PATH] [--password PASSWORD]
        """
        global SSH_AVAILABLE  # Declare global at the beginning of the function
        args = arg.split()
        password = None
        
        # Parse named arguments first
        named_args = ["--ssh", "--username", "--key-path", "--password", "--port"]
        positional_args = []
        
        i = 0
        while i < len(args):
            if args[i] in named_args:
                if args[i] == "--ssh":
                    self.use_ssh = True
                    i += 1
                elif args[i] == "--username" and i + 1 < len(args):
                    self.username = args[i + 1]
                    i += 2
                elif args[i] == "--key-path" and i + 1 < len(args):
                    self.key_path = args[i + 1]
                    i += 2
                elif args[i] == "--password" and i + 1 < len(args):
                    password = args[i + 1]
                    i += 2
                elif args[i] == "--port" and i + 1 < len(args):
                    try:
                        self.port = int(args[i + 1])
                        i += 2
                    except ValueError:
                        print(f"Invalid port: {args[i + 1]}")
                        return
                else:
                    i += 1
            else:
                positional_args.append(args[i])
                i += 1
        
        # Now handle positional arguments
        if len(positional_args) >= 1:
            self.host = positional_args[0]
        if len(positional_args) >= 2:
            try:
                self.port = int(positional_args[1])
            except ValueError:
                print(f"Invalid port: {positional_args[1]}")
                return
        
        if self.simulation:
            print(f"[SIMULATION] Connecting to {self.host}:{self.port} via {'SSH' if self.use_ssh else 'TCP'}")
            self.connected = True
            self.prompt = f"({self.host}) "
            return
        
        try:
            if self.use_ssh:
                if not SSH_AVAILABLE:
                    print("SSH support not available. Install paramiko for SSH functionality.")
                    
                    # Offer to install paramiko automatically
                    install = input("Would you like to install paramiko now? (y/n): ")
                    if install.lower() == 'y':
                        print("Installing paramiko...")
                        try:
                            subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
                            print("Paramiko installed successfully. Please restart the shell.")
                            
                            # Try to import paramiko again
                            try:
                                import paramiko
                                SSH_AVAILABLE = True
                                print("SSH support is now available!")
                            except ImportError:
                                print("Restart required to use SSH functionality.")
                                return
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to install paramiko: {e}")
                            return
                    else:
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
                        print("RPi.GPIO not found. Installing required libraries...")
                        try:
                            # Install RPi.GPIO and other dependencies
                            install_cmd = "sudo apt-get update && sudo apt-get install -y python3-rpi.gpio python3-pip"
                            print(f"Running: {install_cmd}")
                            stdin, stdout, stderr = self.ssh_client.exec_command(install_cmd)
                            
                            # Wait for completion and show output
                            while not stdout.channel.exit_status_ready():
                                if stdout.channel.recv_ready():
                                    print(stdout.channel.recv(1024).decode(), end='')
                                time.sleep(0.1)
                            
                            exit_status = stdout.channel.recv_exit_status()
                            if exit_status != 0:
                                print(f"Installation failed with exit code {exit_status}")
                                print(stderr.read().decode())
                            else:
                                print("Installation completed successfully")
                        except Exception as e:
                            print(f"Error installing dependencies: {e}")
                    else:
                        print("Required libraries already installed")
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
            print("No command specified.")
            return
        
        # Expand variables in the command
        for var_name, var_value in self.variables.items():
            arg = arg.replace(f"${var_name}", str(var_value))
        
        if self.simulation:
            print(f"[SIMULATION] Executing: {arg}")
            return
        
        try:
            if self.use_ssh:
                # Execute command via SSH
                print(f"Executing: {arg}")
                stdin, stdout, stderr = self.ssh_client.exec_command(arg, timeout=10)
                
                # Track the process if process manager is available
                if self.process_manager and "python" in arg and "&" in arg:
                    # This is likely a background process
                    print("Tracking as background process")
                    # We can't easily get the PID from SSH, so we'll use a timestamp as identifier
                    process_id = int(time.time())
                    self.process_manager.start_process(
                        command=arg,
                        name=f"ssh_bg_{process_id}",
                        resources=[],  # We don't know what resources it uses
                        timeout=3600  # 1 hour default timeout
                    )
                
                # Read and print output
                for line in stdout:
                    print(line.strip())
                
                # Check for errors
                errors = stderr.read().decode().strip()
                if errors:
                    print(f"Errors: {errors}")
            else:
                # Execute command via TCP
                command = f"EXEC {arg}\n"
                self.tcp_socket.sendall(command.encode())
                response = self.tcp_socket.recv(4096).decode()
                print(response)
        except Exception as e:
            print(f"Command execution failed: {e}")
    
    def do_gpio(self, arg):
        """
        Control GPIO pins on the remote device.
        Usage: gpio <pin> <mode> [value]
        Modes: in, out, read, list
        """
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        args = arg.split()
        if not args:
            print("Usage: gpio <pin> <mode> [value]")
            print("Modes: in, out, read, list")
            return
        
        # Check if we need to acquire resources
        resources = []
        if len(args) >= 1 and args[0].isdigit():
            pin = int(args[0])
            resources = [f"gpio_{pin}"]
        
        command = f"python3 /tmp/rpi_gpio_helper.py gpio {arg}"
        
        if self.simulation:
            print(f"[SIMULATION] {command}")
            return
        
        try:
            if self.use_ssh:
                # Use process manager if available to handle resource contention
                if self.process_manager and resources:
                    success, result = self.process_manager.start_process(
                        command=command,
                        name=f"gpio_{arg.replace(' ', '_')}",
                        resources=resources,
                        timeout=10  # GPIO operations should be quick
                    )
                    
                    if not success:
                        print(f"Cannot execute: {result}")
                        return
                    
                    # Execute and wait for completion
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    for line in stdout:
                        print(line.strip())
                    
                    errors = stderr.read().decode().strip()
                    if errors:
                        print(f"Errors: {errors}")
                    
                    # Clean up the process
                    if isinstance(result, int):
                        self.process_manager.cleanup_process(result)
                else:
                    # Execute without process management
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    for line in stdout:
                        print(line.strip())
                    
                    errors = stderr.read().decode().strip()
                    if errors:
                        print(f"Errors: {errors}")
            else:
                # Execute via TCP
                tcp_command = f"EXEC {command}\n"
                self.tcp_socket.sendall(tcp_command.encode())
                response = self.tcp_socket.recv(4096).decode()
                print(response)
        except Exception as e:
            print(f"GPIO command failed: {e}")
    
    def do_led(self, arg):
        """
        Control LEDs on the remote device.
        Usage: led <name> <action> [params]
        Actions: setup, on, off, blink, list
        """
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        args = arg.split()
        if len(args) < 2:
            print("Usage: led <name> <action> [params]")
            print("Actions: setup, on, off, blink, list")
            return
        
        led_name = args[0]
        action = args[1]
        
        # Check if we need to acquire resources
        resources = []
        if action != "list":
            resources = [f"led_{led_name}"]
        
        command = f"python3 /tmp/rpi_gpio_helper.py led {arg}"
        
        if self.simulation:
            print(f"[SIMULATION] {command}")
            return
        
        try:
            if self.use_ssh:
                # Use process manager if available
                if self.process_manager and resources:
                    # For blink operations, we need a longer timeout
                    timeout = 60 if action == "blink" else 10
                    
                    success, result = self.process_manager.start_process(
                        command=command,
                        name=f"led_{led_name}_{action}",
                        resources=resources,
                        timeout=timeout
                    )
                    
                    if not success:
                        print(f"Cannot execute: {result}")
                        return
                    
                    # Execute and wait for completion
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    for line in stdout:
                        print(line.strip())
                    
                    errors = stderr.read().decode().strip()
                    if errors:
                        print(f"Errors: {errors}")
                    
                    # Clean up the process
                    if isinstance(result, int):
                        self.process_manager.cleanup_process(result)
                else:
                    # Execute without process management
                    stdin, stdout, stderr = self.ssh_client.exec_command(command)
                    for line in stdout:
                        print(line.strip())
                    
                    errors = stderr.read().decode().strip()
                    if errors:
                        print(f"Errors: {errors}")
            else:
                # Execute via TCP
                tcp_command = f"EXEC {command}\n"
                self.tcp_socket.sendall(tcp_command.encode())
                response = self.tcp_socket.recv(4096).decode()
                print(response)
        except Exception as e:
            print(f"LED command failed: {e}")
    
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
            print("  stream_gpio <pin1,pin2,...>   - Stream GPIO pin states in real-time")
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
    
    def do_processes(self, arg):
        """
        List and manage running processes.
        Usage: processes [list|kill <pid>|cleanup]
        """
        if not self.process_manager:
            print("Process manager not available.")
            return
        
        args = arg.split()
        action = args[0] if args else "list"
        
        if action == "list":
            processes = self.process_manager.get_running_processes()
            if not processes:
                print("No running processes.")
                return
            
            print("Running processes:")
            for pid, info in processes.items():
                print(f"  PID {pid}: {info.get('name', 'unknown')} - Running for {info.get('runtime_formatted', 'unknown')}")
                print(f"    Command: {info.get('command', 'unknown')}")
                if info.get('resources'):
                    print(f"    Resources: {', '.join(info.get('resources', []))}")
                print()
        
        elif action == "kill" and len(args) > 1:
            try:
                pid = int(args[1])
                if self.process_manager.terminate_process(pid):
                    print(f"Process {pid} terminated.")
                else:
                    print(f"Failed to terminate process {pid}.")
            except ValueError:
                print(f"Invalid PID: {args[1]}")
        
        elif action == "cleanup":
            # Check for anomalies and fix them
            fixed, remaining = self.process_manager.handle_anomalies(auto_fix=True)
            
            if fixed:
                print(f"Fixed {len(fixed)} process anomalies:")
                for anomaly in fixed:
                    print(f"  - {anomaly.get('type')}: {anomaly}")
            
            if remaining:
                print(f"Remaining {len(remaining)} process anomalies:")
                for anomaly in remaining:
                    print(f"  - {anomaly.get('type')}: {anomaly}")
            
            if not fixed and not remaining:
                print("No process anomalies detected.")
        
        else:
            print("Usage: processes [list|kill <pid>|cleanup]")
    
    def do_resources(self, arg):
        """
        Show resource usage status.
        Usage: resources
        """
        if not self.process_manager:
            print("Process manager not available.")
            return
        
        resources = self.process_manager.get_resource_status()
        if not resources:
            print("No resources being tracked.")
            return
        
        print("Resource status:")
        for resource, info in resources.items():
            status = "In use" if info.get('in_use') else "Available"
            pid = info.get('pid', 'N/A')
            print(f"  {resource}: {status} (PID: {pid})")
    
    def do_stream_gpio(self, arg):
        """
        Start real-time GPIO streaming from the remote device.
        Usage: stream_gpio <pin1,pin2,...> [interval] [port]
        Example: stream_gpio 17,18,27 0.1 8765
        """
        if not self.connected:
            print("Not connected. Use 'connect' first.")
            return
        
        args = arg.split()
        if not args:
            print("Usage: stream_gpio <pin1,pin2,...> [interval] [port]")
            print("Example: stream_gpio 17,18,27 0.1 8765")
            return
        
        # Default values
        pins = args[0]
        interval = "0.1"
        port = "8765"
        
        if len(args) > 1:
            interval = args[1]
        if len(args) > 2:
            port = args[2]
        
        if self.simulation:
            print(f"[SIMULATION] Starting GPIO streaming for pins {pins} with interval {interval}s on port {port}")
            return
        
        try:
            if self.use_ssh:
                # Start the streaming server on the remote device
                command = f"python3 /tmp/rpi_gpio_helper.py stream {pins} {interval} {port}"
                
                # Use process manager if available
                if self.process_manager:
                    # Create a list of resources from the pins
                    resources = []
                    for pin in pins.split(','):
                        try:
                            pin_num = int(pin.strip())
                            resources.append(f"gpio_{pin_num}")
                        except ValueError:
                            pass
                    
                    success, result = self.process_manager.start_process(
                        command=command,
                        name=f"gpio_stream_{pins.replace(',', '_')}",
                        resources=resources,
                        timeout=3600  # 1 hour default timeout
                    )
                    
                    if not success:
                        print(f"Cannot start streaming: {result}")
                        return
                    
                    # Start the server in the background
                    print(f"Starting GPIO streaming server on the remote device...")
                    self.ssh_client.exec_command(f"{command} &")
                    
                    # Wait for the server to start
                    time.sleep(2)
                    
                    # Start the client locally
                    print(f"Connecting to GPIO streaming server...")
                    client_thread = threading.Thread(
                        target=self._run_gpio_stream_client,
                        args=(self.host, port),
                        daemon=True
                    )
                    client_thread.start()
                    
                    print(f"GPIO streaming active. Press Ctrl+C to stop.")
                else:
                    # Start without process management
                    print(f"Starting GPIO streaming server on the remote device...")
                    self.ssh_client.exec_command(f"{command} &")
                    
                    # Wait for the server to start
                    time.sleep(2)
                    
                    # Start the client locally
                    print(f"Connecting to GPIO streaming server...")
                    client_thread = threading.Thread(
                        target=self._run_gpio_stream_client,
                        args=(self.host, port),
                        daemon=True
                    )
                    client_thread.start()
                    
                    print(f"GPIO streaming active. Press Ctrl+C to stop.")
            else:
                # Execute via TCP
                tcp_command = f"EXEC python3 /tmp/rpi_gpio_helper.py stream {pins} {interval} {port}\n"
                self.tcp_socket.sendall(tcp_command.encode())
                response = self.tcp_socket.recv(4096).decode()
                print(response)
                
                # Start the client locally
                print(f"Connecting to GPIO streaming server...")
                client_thread = threading.Thread(
                    target=self._run_gpio_stream_client,
                    args=(self.host, port),
                    daemon=True
                )
                client_thread.start()
                
                print(f"GPIO streaming active. Press Ctrl+C to stop.")
        except Exception as e:
            print(f"GPIO streaming failed: {e}")
    
    def _run_gpio_stream_client(self, host, port):
        """Run the GPIO streaming client."""
        try:
            # Connect to the streaming server
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            print(f"Connecting to {host}:{port}...")
            client.connect((host, int(port)))
            client.settimeout(None)
            print("Connected to GPIO streaming server")
            
            # Receive and display updates
            buffer = ""
            while True:
                # Use select to check if data is available (with timeout)
                ready = select.select([client], [], [], 0.1)
                if ready[0]:
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
                                print(f"\nStreaming configuration:")
                                print(f"  Pins: {update['pins']}")
                                print(f"  Interval: {update['interval']}s")
                                if update.get('simulation'):
                                    print("  Mode: SIMULATION")
                                print("\nPin states (1=HIGH, 0=LOW):")
                                # Restore prompt after printing
                                print(f"{self.prompt}", end='', flush=True)
                            
                            # Display pin state updates
                            elif 'states' in update:
                                timestamp = time.strftime('%H:%M:%S', time.localtime(update['timestamp']))
                                states_str = ", ".join([f"GPIO {pin}={state}" for pin, state in update['states'].items()])
                                print(f"\r[{timestamp}] {states_str}")
                                # Restore prompt after printing
                                print(f"{self.prompt}", end='', flush=True)
                        
                        except json.JSONDecodeError:
                            print(f"\nError parsing update: {line}")
                            print(f"{self.prompt}", end='', flush=True)
        
        except Exception as e:
            print(f"\nError in streaming client: {e}")
            print(f"{self.prompt}", end='', flush=True)
        finally:
            try:
                client.close()
                print("\nDisconnected from GPIO streaming server")
                print(f"{self.prompt}", end='', flush=True)
            except:
                pass

def main():
    """Main entry point for the remote shell."""
    parser = argparse.ArgumentParser(description="Simple Remote Shell for UnitMCP")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=22, help="Port to connect to")
    parser.add_argument("--ssh", action="store_true", help="Use SSH instead of TCP")
    parser.add_argument("--username", default="pi", help="Username for SSH connection")
    parser.add_argument("--key-path", help="Path to SSH private key file")
    parser.add_argument("--password", help="Password for SSH connection (not recommended for security reasons)")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    
    args = parser.parse_args()
    
    shell = RemoteShell(
        host=args.host,
        port=args.port,
        use_ssh=args.ssh,
        simulation=args.simulation,
        username=args.username,
        key_path=args.key_path
    )
    
    # If password is provided, connect automatically
    if args.password and args.host != "localhost":
        shell.use_ssh = True  # Force SSH mode when password is provided
        connect_cmd = f"connect {args.host} {args.port} --ssh --username {args.username} --password {args.password}"
        shell.onecmd(connect_cmd)
    
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up
        if shell.connected:
            shell.do_disconnect("")
        
        # Stop monitoring
        shell.stop_monitoring()

if __name__ == "__main__":
    main()
