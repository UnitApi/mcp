#!/usr/bin/env python3
"""
Remote Control Example

This example demonstrates how to use the Orchestrator to connect to a remote server
and control devices.
"""

import sys
import time
import logging
import argparse
from unitmcp.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the remote control example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Remote Control Example")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=8080, help="Port to use")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--simulation", action="store_true", help="Run in simulation mode")
    args = parser.parse_args()
    
    # Create an Orchestrator instance
    orchestrator = Orchestrator()
    
    # Connect to the server
    print(f"\nConnecting to server: {args.host}:{args.port} (SSL: {args.ssl})")
    connection_info = orchestrator.connect_to_server(
        host=args.host,
        port=args.port,
        ssl_enabled=args.ssl
    )
    
    if connection_info.get("status") != "connected":
        logger.error(f"Failed to connect: {connection_info.get('error', 'Unknown error')}")
        sys.exit(1)
    
    print("Connected successfully!")
    client = connection_info.get("client")
    
    # Get device list
    try:
        print("\nGetting device list...")
        response = client.get_devices()
        
        if not response or "devices" not in response:
            logger.error("Failed to get device list")
            sys.exit(1)
        
        devices = response["devices"]
        
        if not devices:
            print("No devices found")
            return
        
        # Print device list
        print("\nAvailable devices:")
        print("=" * 50)
        for device in devices:
            device_id = device.get("id", "unknown")
            device_type = device.get("type", "unknown")
            device_name = device.get("name", device_id)
            device_status = device.get("status", "unknown")
            
            print(f"ID: {device_id}")
            print(f"Name: {device_name}")
            print(f"Type: {device_type}")
            print(f"Status: {device_status}")
            print("-" * 50)
        
        # Control a device if there are any
        if devices:
            device = devices[0]
            device_id = device.get("id")
            device_type = device.get("type")
            
            print(f"\nControlling device: {device_id} ({device_type})")
            
            if device_type == "led":
                # Turn LED on
                print("Turning LED ON")
                client.control_device(device_id, {"state": "on"})
                time.sleep(2)
                
                # Turn LED off
                print("Turning LED OFF")
                client.control_device(device_id, {"state": "off"})
                
            elif device_type == "button":
                print("Monitoring button state for 10 seconds...")
                end_time = time.time() + 10
                
                while time.time() < end_time:
                    response = client.get_device_state(device_id)
                    state = response.get("state", {}).get("pressed", False)
                    print(f"Button state: {'Pressed' if state else 'Released'}")
                    time.sleep(1)
            
            elif device_type == "display":
                print("Sending text to display")
                client.control_device(device_id, {"text": "Hello from Orchestrator!"})
            
            else:
                print(f"No specific control implemented for device type: {device_type}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
    
    finally:
        # Disconnect from the server
        print("\nDisconnecting from server...")
        orchestrator.disconnect_from_server()
        print("Disconnected")

if __name__ == "__main__":
    main()
