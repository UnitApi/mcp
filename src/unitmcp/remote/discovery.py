#!/usr/bin/env python3
"""
Device Discovery Module for UnitMCP

This module provides functionality for discovering embedded devices on the network.
It supports various discovery methods including mDNS/Avahi, UPnP, and network scanning.
"""

import os
import sys
import asyncio
import logging
import socket
import ipaddress
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

logger = logging.getLogger(__name__)

# Optional imports that will be loaded on demand
_zeroconf_available = False
_upnp_available = False
_nmap_available = False

class DeviceDiscovery:
    """Base class for device discovery methods."""
    
    def __init__(self):
        """Initialize the device discovery."""
        self.devices = {}
    
    async def discover(self, timeout: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Discover devices on the network.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of discovered devices
        """
        raise NotImplementedError("Subclasses must implement discover()")

class MDNSDiscovery(DeviceDiscovery):
    """
    mDNS/Avahi-based device discovery.
    
    This class discovers devices that advertise themselves using mDNS/Avahi.
    """
    
    def __init__(self, service_types: Optional[List[str]] = None):
        """
        Initialize mDNS discovery.
        
        Args:
            service_types: List of service types to discover (e.g., ["_http._tcp.local."])
        """
        super().__init__()
        self._load_zeroconf()
        self.service_types = service_types or [
            "_http._tcp.local.",
            "_ssh._tcp.local.",
            "_mqtt._tcp.local.",
            "_workstation._tcp.local.",
            "_device-info._tcp.local.",
            "_esphomelib._tcp.local.",  # ESPHome devices
            "_arduino._tcp.local.",     # Arduino devices
            "_rpi._tcp.local."          # Raspberry Pi devices
        ]
    
    def _load_zeroconf(self):
        """Load the zeroconf module if available."""
        global _zeroconf_available
        if not _zeroconf_available:
            try:
                import zeroconf
                _zeroconf_available = True
                self._zeroconf = zeroconf
            except ImportError:
                logger.error("Zeroconf is not installed. mDNS discovery will not be available.")
                logger.error("Install it with: pip install zeroconf")
                raise ImportError("Zeroconf is required for mDNS discovery")
    
    async def discover(self, timeout: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Discover devices using mDNS/Avahi.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of discovered devices
        """
        self.devices = {}
        
        # Create a zeroconf instance
        zc = self._zeroconf.Zeroconf()
        
        # Create a listener for service info
        class ServiceListener(self._zeroconf.ServiceListener):
            def __init__(self, parent):
                self.parent = parent
            
            def add_service(self, zc, type, name):
                info = zc.get_service_info(type, name)
                if info:
                    # Extract device information
                    addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                    device_info = {
                        "name": name,
                        "type": type,
                        "addresses": addresses,
                        "port": info.port,
                        "server": info.server,
                        "properties": {k.decode('utf-8'): v.decode('utf-8') 
                                      for k, v in info.properties.items()}
                    }
                    
                    # Add device to the list
                    self.parent.devices[name] = device_info
            
            def remove_service(self, zc, type, name):
                if name in self.parent.devices:
                    del self.parent.devices[name]
            
            def update_service(self, zc, type, name):
                self.add_service(zc, type, name)
        
        # Create a listener for each service type
        listeners = []
        for service_type in self.service_types:
            listener = ServiceListener(self)
            listeners.append(listener)
            self._zeroconf.ServiceBrowser(zc, service_type, listener)
        
        # Wait for the specified timeout
        await asyncio.sleep(timeout)
        
        # Close the zeroconf instance
        zc.close()
        
        return self.devices

class NetworkScanner(DeviceDiscovery):
    """
    Network scanner for device discovery.
    
    This class discovers devices by scanning the network using ping or port scanning.
    """
    
    def __init__(self, network: str = "192.168.1.0/24", ports: Optional[List[int]] = None):
        """
        Initialize network scanner.
        
        Args:
            network: Network to scan in CIDR notation (e.g., "192.168.1.0/24")
            ports: List of ports to scan (e.g., [22, 80, 443])
        """
        super().__init__()
        self.network = network
        self.ports = ports or [22, 80, 443, 1883, 8883, 8080, 8266]
    
    async def discover(self, timeout: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Discover devices by scanning the network.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of discovered devices
        """
        self.devices = {}
        
        # Parse network CIDR
        try:
            network = ipaddress.ip_network(self.network)
        except ValueError as e:
            logger.error(f"Invalid network CIDR: {self.network}")
            return self.devices
        
        # Create a list of hosts to scan
        hosts = list(network.hosts())
        
        # Limit the number of hosts to scan based on timeout
        max_hosts = min(len(hosts), timeout * 10)  # Assume 10 hosts per second
        hosts = hosts[:max_hosts]
        
        # Create tasks for scanning each host
        tasks = []
        for host in hosts:
            tasks.append(self._scan_host(str(host)))
        
        # Run tasks with a timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Network scan timed out after {timeout} seconds")
        
        return self.devices
    
    async def _scan_host(self, host: str):
        """
        Scan a single host for open ports.
        
        Args:
            host: Host IP address
        """
        # Check if the host is reachable with a ping
        ping_result = await self._ping_host(host)
        if not ping_result:
            return
        
        # Check for open ports
        open_ports = []
        for port in self.ports:
            is_open = await self._check_port(host, port)
            if is_open:
                open_ports.append(port)
        
        if open_ports:
            # Try to get hostname
            try:
                hostname = socket.gethostbyaddr(host)[0]
            except socket.herror:
                hostname = host
            
            # Add device to the list
            self.devices[host] = {
                "ip": host,
                "hostname": hostname,
                "open_ports": open_ports,
                "type": self._guess_device_type(open_ports)
            }
    
    async def _ping_host(self, host: str) -> bool:
        """
        Check if a host is reachable with a ping.
        
        Args:
            host: Host IP address
            
        Returns:
            bool: True if the host is reachable, False otherwise
        """
        # Use asyncio subprocess to run ping
        if os.name == "nt":  # Windows
            ping_cmd = ["ping", "-n", "1", "-w", "500", host]
        else:  # Linux/Mac
            ping_cmd = ["ping", "-c", "1", "-W", "1", host]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *ping_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            logger.debug(f"Error pinging {host}: {str(e)}")
            return False
    
    async def _check_port(self, host: str, port: int) -> bool:
        """
        Check if a port is open on a host.
        
        Args:
            host: Host IP address
            port: Port number
            
        Returns:
            bool: True if the port is open, False otherwise
        """
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            return False
    
    def _guess_device_type(self, open_ports: List[int]) -> str:
        """
        Guess the device type based on open ports.
        
        Args:
            open_ports: List of open ports
            
        Returns:
            str: Guessed device type
        """
        if 22 in open_ports:
            if 8080 in open_ports or 80 in open_ports:
                return "raspberry_pi"
            else:
                return "linux_device"
        
        if 8266 in open_ports:
            return "esp8266"
        
        if 1883 in open_ports or 8883 in open_ports:
            return "mqtt_broker"
        
        if 80 in open_ports or 443 in open_ports:
            return "web_server"
        
        return "unknown"

class NetworkScanDiscovery(DeviceDiscovery):
    """
    Network scan-based device discovery.
    
    This class discovers devices by scanning the network using the NetworkScanner.
    It provides a simplified interface for the NetworkScanner.
    """
    
    def __init__(self, network: str = "192.168.1.0/24", ports: Optional[List[int]] = None):
        """
        Initialize network scan discovery.
        
        Args:
            network: Network to scan in CIDR notation (e.g., "192.168.1.0/24")
            ports: List of ports to scan (e.g., [22, 80, 443])
        """
        super().__init__()
        self.scanner = NetworkScanner(network, ports)
    
    async def discover(self, timeout: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Discover devices by scanning the network.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of discovered devices
        """
        return await self.scanner.discover(timeout)

class DeviceDiscoveryManager:
    """
    Device discovery manager.
    
    This class manages multiple device discovery methods and combines their results.
    """
    
    def __init__(self):
        """Initialize the device discovery manager."""
        self.discovery_methods = []
        self.devices = {}
    
    def add_discovery_method(self, method: DeviceDiscovery):
        """
        Add a discovery method.
        
        Args:
            method: Device discovery method to add
        """
        self.discovery_methods.append(method)
    
    async def discover(self, timeout: int = 10) -> Dict[str, Dict[str, Any]]:
        """
        Discover devices using all registered discovery methods.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of discovered devices
        """
        self.devices = {}
        
        # Create tasks for each discovery method
        tasks = []
        for method in self.discovery_methods:
            tasks.append(method.discover(timeout))
        
        # Run all discovery methods concurrently
        results = await asyncio.gather(*tasks)
        
        # Combine results
        for result in results:
            self.devices.update(result)
        
        return self.devices

# Factory function to create a discovery manager with default methods
def create_discovery_manager() -> DeviceDiscoveryManager:
    """
    Create a device discovery manager with default discovery methods.
    
    Returns:
        DeviceDiscoveryManager: Device discovery manager
    """
    manager = DeviceDiscoveryManager()
    
    # Add mDNS discovery if available
    try:
        manager.add_discovery_method(MDNSDiscovery())
    except ImportError:
        pass
    
    # Add network scanner
    manager.add_discovery_method(NetworkScanner())
    
    return manager
