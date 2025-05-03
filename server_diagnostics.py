#!/usr/bin/env python3
"""
MCP Server Diagnostics Tool

This standalone script helps diagnose connection issues with MCP servers by:
1. Checking if the server is reachable
2. Scanning for open ports
3. Testing connections to common MCP ports
4. Providing detailed error information and suggestions

Usage:
  python server_diagnostics.py <host> [--port-range=start-end] [--timeout=seconds]

Example:
  python server_diagnostics.py 192.168.188.154 --port-range=8000-10000 --timeout=0.5
"""

import argparse
import asyncio
import concurrent.futures
import socket
import subprocess
import sys
import time
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

def print_section(text):
    """Print a formatted section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}[{text}]{Colors.ENDC}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}{text}{Colors.ENDC}")

def print_info(text):
    """Print an info message."""
    print(f"{Colors.BLUE}{text}{Colors.ENDC}")

def check_host_reachable(host):
    """Check if a host is reachable via ping."""
    print_section("Checking if host is reachable")
    
    try:
        # Use ping to check if host is reachable
        ping_cmd = f"ping -c 4 -W 2 {host}"
        print(f"Running: {ping_cmd}")
        
        result = subprocess.run(
            ping_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print_success(f"Host {host} is reachable (ping successful)")
            # Extract ping statistics
            stats_lines = [line for line in result.stdout.splitlines() if "packets transmitted" in line or "min/avg/max" in line]
            for line in stats_lines:
                print(f"Ping statistics: {line}")
            return True
        else:
            print_error(f"Host {host} is not responding to ping")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error(f"Ping command timed out")
        return False
    except Exception as e:
        print_error(f"Error checking host reachability: {e}")
        return False

def check_port(host, port, timeout=1.0):
    """Check if a specific port is open on the host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    sock.close()
    return port, result

def scan_ports(host, port_ranges=None, timeout=0.5):
    """Scan for open ports on the host."""
    print_section(f"Scanning for open ports on {host}")
    
    if port_ranges is None:
        # Default port ranges to check
        port_ranges = [(8000, 8100), (9500, 9600), (5000, 5100)]
    
    print_info(f"Scanning port ranges: {', '.join([f'{start}-{end}' for start, end in port_ranges])}")
    print_info(f"Timeout per port: {timeout}s")
    
    open_ports = []
    total_ports = sum(end - start + 1 for start, end in port_ranges)
    checked_ports = 0
    
    start_time = time.time()
    
    for start_port, end_port in port_ranges:
        print_info(f"Scanning range {start_port}-{end_port}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_port, host, port, timeout) for port in range(start_port, end_port + 1)]
            
            for future in concurrent.futures.as_completed(futures):
                port, result = future.result()
                checked_ports += 1
                
                # Print progress every 100 ports or at the end
                if checked_ports % 100 == 0 or checked_ports == total_ports:
                    progress = (checked_ports / total_ports) * 100
                    elapsed = time.time() - start_time
                    print(f"\rProgress: {checked_ports}/{total_ports} ports checked ({progress:.1f}%) - Elapsed: {elapsed:.1f}s", end="")
                
                if result == 0:
                    print(f"\n{Colors.GREEN}Found open port: {port}{Colors.ENDC}")
                    open_ports.append(port)
    
    print("\n")
    elapsed = time.time() - start_time
    
    if open_ports:
        print_success(f"Scan complete in {elapsed:.1f}s. Found {len(open_ports)} open ports on {host}:")
        
        # Sort open ports
        open_ports.sort()
        
        # Group consecutive ports for display
        groups = []
        current_group = [open_ports[0]]
        
        for i in range(1, len(open_ports)):
            if open_ports[i] == open_ports[i-1] + 1:
                current_group.append(open_ports[i])
            else:
                groups.append(current_group)
                current_group = [open_ports[i]]
        
        groups.append(current_group)
        
        # Display grouped ports
        for group in groups:
            if len(group) == 1:
                print(f"  • Port {group[0]}")
            else:
                print(f"  • Ports {group[0]}-{group[-1]} ({len(group)} ports)")
    else:
        print_warning(f"Scan complete in {elapsed:.1f}s. No open ports found on {host} in the specified ranges.")
    
    return open_ports

def test_mcp_ports(host, ports, timeout=1.0):
    """Test specific ports that are commonly used by MCP servers."""
    print_section(f"Testing common MCP server ports on {host}")
    
    common_mcp_ports = [8000, 8080, 9515, 9517, 9518]
    if ports:
        test_ports = ports
    else:
        test_ports = common_mcp_ports
    
    print_info(f"Testing ports: {', '.join(map(str, test_ports))}")
    
    results = []
    for port in test_ports:
        print(f"Testing port {port}... ", end="", flush=True)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print_success("OPEN")
            results.append((port, True, None))
        else:
            error_message = get_socket_error_message(result)
            print_error(f"CLOSED ({error_message})")
            results.append((port, False, error_message))
    
    return results

def get_socket_error_message(error_code):
    """Convert a socket error code to a human-readable message."""
    error_messages = {
        0: "Success",
        1: "Operation not permitted",
        2: "No such file or directory",
        3: "No such process",
        4: "Interrupted system call",
        5: "Input/output error",
        6: "No such device or address",
        7: "Argument list too long",
        8: "Exec format error",
        9: "Bad file descriptor",
        10: "No child processes",
        11: "Resource temporarily unavailable",
        12: "Cannot allocate memory",
        13: "Permission denied",
        14: "Bad address",
        22: "Invalid argument",
        35: "Resource temporarily unavailable",
        36: "Operation now in progress",
        37: "Operation already in progress",
        38: "Socket operation on non-socket",
        39: "Destination address required",
        40: "Message too long",
        41: "Protocol wrong type for socket",
        42: "Protocol not available",
        43: "Protocol not supported",
        44: "Socket type not supported",
        45: "Operation not supported",
        46: "Protocol family not supported",
        47: "Address family not supported by protocol",
        48: "Address already in use",
        49: "Cannot assign requested address",
        50: "Network is down",
        51: "Network is unreachable",
        52: "Network dropped connection on reset",
        53: "Software caused connection abort",
        54: "Connection reset by peer",
        55: "No buffer space available",
        56: "Socket is already connected",
        57: "Socket is not connected",
        58: "Cannot send after socket shutdown",
        59: "Too many references",
        60: "Connection timed out",
        61: "Connection refused",
        62: "Too many levels of symbolic links",
        63: "File name too long",
        64: "Host is down",
        65: "No route to host",
        66: "Directory not empty",
        67: "Too many processes",
        68: "Too many users",
        69: "Disk quota exceeded",
        70: "Stale file handle",
        71: "Too many levels of remote in path",
        111: "Connection refused - No service is running on the requested port"
    }
    
    return error_messages.get(error_code, f"Unknown error (code: {error_code})")

def check_dns_resolution(host):
    """Check if the hostname can be resolved to an IP address."""
    print_section(f"Checking DNS resolution for {host}")
    
    try:
        # Check if the host is already an IP address
        try:
            socket.inet_aton(host)
            print_info(f"{host} is already an IP address, no DNS resolution needed")
            return True
        except socket.error:
            pass
        
        # Try to resolve the hostname
        ip = socket.gethostbyname(host)
        print_success(f"Successfully resolved {host} to IP: {ip}")
        return True
    except socket.gaierror as e:
        print_error(f"DNS resolution failed: {e}")
        return False
    except Exception as e:
        print_error(f"Error during DNS resolution: {e}")
        return False

def provide_recommendations(host, port_results):
    """Provide recommendations based on the test results."""
    print_section("Recommendations")
    
    open_ports = [port for port, is_open, _ in port_results if is_open]
    
    if open_ports:
        print_success(f"Found {len(open_ports)} open ports on {host}.")
        print_info("Try connecting to one of these ports with the MCP client:")
        
        for port in open_ports:
            print(f"  connect {host} {port}")
        
        print_info("\nIf you're still having connection issues:")
        print("1. Check that the MCP server is actually running on these ports")
        print("2. Verify that the server is configured correctly")
        print("3. Check for any firewall rules that might be blocking the connection")
    else:
        print_warning(f"No open ports found on {host}.")
        print_info("This could mean:")
        print("1. The server is not running")
        print("2. The server is running on a different port range")
        print("3. A firewall is blocking the connections")
        
        print_info("\nTry the following:")
        print(f"1. Make sure the MCP server is running on {host}")
        print("2. Check the server configuration to verify the correct port")
        print("3. Scan a wider range of ports: --port-range=1-65535 (warning: this will take a long time)")
        print("4. Check firewall settings on both the client and server")

def main():
    """Main function to run the diagnostics."""
    parser = argparse.ArgumentParser(description="MCP Server Diagnostics Tool")
    parser.add_argument("host", help="The hostname or IP address to check")
    parser.add_argument("--port-range", help="Port range to scan (e.g., 8000-10000,5000-6000)")
    parser.add_argument("--timeout", type=float, default=0.5, help="Timeout for port scanning in seconds")
    parser.add_argument("--ports", help="Specific ports to test (e.g., 8000,9515,9517,9518)")
    
    args = parser.parse_args()
    
    print_header(f"MCP Server Diagnostics for {args.host}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse port ranges
    port_ranges = None
    if args.port_range:
        try:
            port_ranges = []
            for range_str in args.port_range.split(','):
                start, end = map(int, range_str.split('-'))
                port_ranges.append((start, end))
        except ValueError:
            print_error(f"Invalid port range format: {args.port_range}")
            print_info("Format should be start-end (e.g., 8000-10000) or multiple ranges separated by commas")
            sys.exit(1)
    
    # Parse specific ports
    specific_ports = None
    if args.ports:
        try:
            specific_ports = [int(p) for p in args.ports.split(',')]
        except ValueError:
            print_error(f"Invalid ports format: {args.ports}")
            print_info("Format should be comma-separated port numbers (e.g., 8000,9515,9517)")
            sys.exit(1)
    
    # Run diagnostics
    host_reachable = check_host_reachable(args.host)
    dns_resolved = check_dns_resolution(args.host)
    
    if host_reachable and dns_resolved:
        # Test specific ports first if provided
        if specific_ports:
            port_results = test_mcp_ports(args.host, specific_ports, args.timeout)
        else:
            port_results = test_mcp_ports(args.host, None, args.timeout)
        
        # Scan for open ports
        open_ports = scan_ports(args.host, port_ranges, args.timeout)
        
        # Provide recommendations
        provide_recommendations(args.host, port_results)
    else:
        print_error(f"Cannot proceed with port scanning because {args.host} is not reachable.")
        print_info("Please check your network connection and the server's availability.")
    
    print_header("Diagnostics Complete")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
