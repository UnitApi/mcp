#!/usr/bin/env python3
"""
Unit tests for the remote device discovery module.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.remote.discovery import (
    DeviceDiscovery,
    MDNSDiscovery,
    NetworkScanDiscovery
)

class TestDeviceDiscovery(unittest.TestCase):
    """Test cases for the DeviceDiscovery base class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        discovery = DeviceDiscovery()
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(discovery.discover_devices())


class TestMDNSDiscovery(unittest.TestCase):
    """Test cases for the MDNSDiscovery class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.discovery = MDNSDiscovery(service_types=["_http._tcp.local."])
    
    @patch('unitmcp.remote.discovery.ServiceBrowser')
    @patch('unitmcp.remote.discovery.Zeroconf')
    async def async_test_discover_devices(self, mock_zeroconf_class, mock_browser_class):
        """Test discovering devices using mDNS."""
        # Mock Zeroconf and ServiceBrowser
        mock_zeroconf = MagicMock()
        mock_zeroconf_class.return_value = mock_zeroconf
        
        # Mock the service listener
        def add_service(zc, type_, name):
            # Simulate finding a service
            info = MagicMock()
            info.properties = {b'model': b'raspberry_pi'}
            info.server = "raspberrypi.local."
            info.port = 8080
            info.addresses = [b'\xc0\xa8\x01\x0a']  # 192.168.1.10
            
            # Call the listener's add_service method
            self.discovery._service_listener.add_service(zc, type_, name, info)
        
        # Set up the mock browser to call add_service
        def browser_init(zc, type_, listener):
            self.discovery._service_listener = listener
            # Simulate finding a service
            add_service(zc, "_http._tcp.local.", "Raspberry Pi._http._tcp.local.")
        
        mock_browser_class.side_effect = browser_init
        
        # Discover devices
        devices = await self.discovery.discover_devices()
        
        # Check that the correct device was discovered
        self.assertEqual(len(devices), 1)
        device = devices[0]
        self.assertEqual(device.name, "Raspberry Pi")
        self.assertEqual(device.host, "raspberrypi.local.")
        self.assertEqual(device.ip, "192.168.1.10")
        self.assertEqual(device.port, 8080)
        self.assertEqual(device.device_type, "raspberry_pi")
        
        # Check that Zeroconf was closed
        mock_zeroconf.close.assert_called_once()
    
    def test_discover_devices(self):
        """Test discovering devices using mDNS (synchronous wrapper)."""
        asyncio.run(self.async_test_discover_devices())


class TestNetworkScanDiscovery(unittest.TestCase):
    """Test cases for the NetworkScanDiscovery class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.discovery = NetworkScanDiscovery(
            ip_range="192.168.1.0/24",
            ports=[22, 80, 8080]
        )
    
    @patch('unitmcp.remote.discovery.socket.socket')
    async def async_test_discover_devices(self, mock_socket_class):
        """Test discovering devices using network scanning."""
        # Mock socket
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        # Mock socket.connect_ex to simulate open ports
        def connect_ex(address):
            ip, port = address
            # Simulate open ports for specific IPs
            if ip == "192.168.1.10" and port in [22, 80]:
                return 0  # Success
            elif ip == "192.168.1.20" and port == 8080:
                return 0  # Success
            else:
                return 1  # Failure
        
        mock_socket.connect_ex.side_effect = connect_ex
        
        # Mock socket.gethostbyaddr to simulate hostname resolution
        def gethostbyaddr(ip):
            if ip == "192.168.1.10":
                return ("raspberrypi.local", [], [ip])
            elif ip == "192.168.1.20":
                return ("arduino.local", [], [ip])
            else:
                raise socket.herror("Unknown host")
        
        # Patch socket.gethostbyaddr
        with patch('unitmcp.remote.discovery.socket.gethostbyaddr', side_effect=gethostbyaddr):
            # Patch the IP range to limit the scan to just a few IPs
            with patch.object(self.discovery, '_generate_ip_list', return_value=["192.168.1.10", "192.168.1.20", "192.168.1.30"]):
                # Discover devices
                devices = await self.discovery.discover_devices()
        
        # Check that the correct devices were discovered
        self.assertEqual(len(devices), 2)
        
        # Check the first device
        device1 = next(d for d in devices if d.ip == "192.168.1.10")
        self.assertEqual(device1.name, "raspberrypi.local")
        self.assertEqual(device1.host, "raspberrypi.local")
        self.assertEqual(device1.open_ports, [22, 80])
        
        # Check the second device
        device2 = next(d for d in devices if d.ip == "192.168.1.20")
        self.assertEqual(device2.name, "arduino.local")
        self.assertEqual(device2.host, "arduino.local")
        self.assertEqual(device2.open_ports, [8080])
    
    def test_discover_devices(self):
        """Test discovering devices using network scanning (synchronous wrapper)."""
        asyncio.run(self.async_test_discover_devices())
    
    def test_generate_ip_list(self):
        """Test generating a list of IPs from a CIDR range."""
        # Test with a small CIDR range
        discovery = NetworkScanDiscovery(ip_range="192.168.1.0/30")
        ip_list = discovery._generate_ip_list()
        
        # Check that the correct IPs were generated
        self.assertEqual(ip_list, ["192.168.1.1", "192.168.1.2"])
        
        # Test with a specific IP
        discovery = NetworkScanDiscovery(ip_range="192.168.1.10")
        ip_list = discovery._generate_ip_list()
        
        # Check that the correct IP was generated
        self.assertEqual(ip_list, ["192.168.1.10"])


if __name__ == '__main__':
    unittest.main()
