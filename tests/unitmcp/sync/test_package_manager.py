#!/usr/bin/env python3
"""
Unit tests for the package manager module.
"""

import os
import sys
import unittest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.sync.package_manager import (
    PackageManager,
    APTPackageManager,
    PIPPackageManager,
    NPMPackageManager,
    PackageManagerFactory
)
from unitmcp.remote.connection import RemoteConnection

class TestPackageManager(unittest.TestCase):
    """Test cases for the PackageManager base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.package_manager = PackageManager(self.connection)
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.package_manager.install_package("test-package"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.package_manager.uninstall_package("test-package"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.package_manager.update_package("test-package"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.package_manager.list_installed_packages())
    
    async def async_test_check_if_installed(self):
        """Test checking if a package is installed."""
        # Mock the list_installed_packages method
        async def mock_list_installed_packages():
            return {"test-package": "1.0.0", "other-package": "2.0.0"}
        
        self.package_manager.list_installed_packages = mock_list_installed_packages
        
        # Check if packages are installed
        version = await self.package_manager.check_if_installed("test-package")
        self.assertEqual(version, "1.0.0")
        
        version = await self.package_manager.check_if_installed("other-package")
        self.assertEqual(version, "2.0.0")
        
        version = await self.package_manager.check_if_installed("nonexistent-package")
        self.assertIsNone(version)
    
    def test_check_if_installed(self):
        """Test checking if a package is installed (synchronous wrapper)."""
        asyncio.run(self.async_test_check_if_installed())


class TestAPTPackageManager(unittest.TestCase):
    """Test cases for the APTPackageManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.package_manager = APTPackageManager(self.connection)
    
    async def async_test_install_package(self):
        """Test installing a package using APT."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package
        result = await self.package_manager.install_package("test-package")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo apt-get install -y test-package")
    
    def test_install_package(self):
        """Test installing a package using APT (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package())
    
    async def async_test_install_package_with_version(self):
        """Test installing a specific version of a package using APT."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package with a specific version
        result = await self.package_manager.install_package("test-package", "1.0.0")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo apt-get install -y test-package=1.0.0")
    
    def test_install_package_with_version(self):
        """Test installing a specific version of a package using APT (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package_with_version())
    
    async def async_test_install_package_failure(self):
        """Test handling installation failures with APT."""
        # Mock the connection's execute_command method to simulate a failure
        self.connection.execute_command.return_value = (1, "", "Failed to install package")
        
        # Try to install a package
        result = await self.package_manager.install_package("test-package")
        
        # Check that the installation failed
        self.assertFalse(result)
    
    def test_install_package_failure(self):
        """Test handling installation failures with APT (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package_failure())
    
    async def async_test_uninstall_package(self):
        """Test uninstalling a package using APT."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package removed", "")
        
        # Uninstall a package
        result = await self.package_manager.uninstall_package("test-package")
        
        # Check that the uninstallation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo apt-get remove -y test-package")
    
    def test_uninstall_package(self):
        """Test uninstalling a package using APT (synchronous wrapper)."""
        asyncio.run(self.async_test_uninstall_package())
    
    async def async_test_update_package(self):
        """Test updating a package using APT."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "Package lists updated", ""),  # apt-get update
            (0, "Package upgraded", "")  # apt-get install --only-upgrade
        ]
        
        # Update a package
        result = await self.package_manager.update_package("test-package")
        
        # Check that the update was successful
        self.assertTrue(result)
        
        # Check that the execute_command methods were called with the correct arguments
        self.connection.execute_command.assert_any_call("sudo apt-get update")
        self.connection.execute_command.assert_any_call("sudo apt-get install --only-upgrade -y test-package")
    
    def test_update_package(self):
        """Test updating a package using APT (synchronous wrapper)."""
        asyncio.run(self.async_test_update_package())
    
    async def async_test_list_installed_packages(self):
        """Test listing installed packages using APT."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "package1 1.0.0\npackage2 2.0.0", "")
        
        # List installed packages
        packages = await self.package_manager.list_installed_packages()
        
        # Check that the correct packages were listed
        self.assertEqual(packages, {"package1": "1.0.0", "package2": "2.0.0"})
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("dpkg-query -W -f='${Package} ${Version}\\n'")
    
    def test_list_installed_packages(self):
        """Test listing installed packages using APT (synchronous wrapper)."""
        asyncio.run(self.async_test_list_installed_packages())


class TestPIPPackageManager(unittest.TestCase):
    """Test cases for the PIPPackageManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.package_manager = PIPPackageManager(self.connection)
    
    async def async_test_install_package(self):
        """Test installing a package using PIP."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package
        result = await self.package_manager.install_package("test-package")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo python3 -m pip install test-package")
    
    def test_install_package(self):
        """Test installing a package using PIP (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package())
    
    async def async_test_install_package_with_version(self):
        """Test installing a specific version of a package using PIP."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package with a specific version
        result = await self.package_manager.install_package("test-package", "1.0.0")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo python3 -m pip install test-package==1.0.0")
    
    def test_install_package_with_version(self):
        """Test installing a specific version of a package using PIP (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package_with_version())
    
    async def async_test_uninstall_package(self):
        """Test uninstalling a package using PIP."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package uninstalled", "")
        
        # Uninstall a package
        result = await self.package_manager.uninstall_package("test-package")
        
        # Check that the uninstallation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo python3 -m pip uninstall -y test-package")
    
    def test_uninstall_package(self):
        """Test uninstalling a package using PIP (synchronous wrapper)."""
        asyncio.run(self.async_test_uninstall_package())
    
    async def async_test_update_package(self):
        """Test updating a package using PIP."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package updated", "")
        
        # Update a package
        result = await self.package_manager.update_package("test-package")
        
        # Check that the update was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("sudo python3 -m pip install --upgrade test-package")
    
    def test_update_package(self):
        """Test updating a package using PIP (synchronous wrapper)."""
        asyncio.run(self.async_test_update_package())
    
    async def async_test_list_installed_packages(self):
        """Test listing installed packages using PIP."""
        # Mock the connection's execute_command method
        pip_output = json.dumps([
            {"name": "package1", "version": "1.0.0"},
            {"name": "package2", "version": "2.0.0"}
        ])
        self.connection.execute_command.return_value = (0, pip_output, "")
        
        # List installed packages
        packages = await self.package_manager.list_installed_packages()
        
        # Check that the correct packages were listed
        self.assertEqual(packages, {"package1": "1.0.0", "package2": "2.0.0"})
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("python3 -m pip list --format=json")
    
    def test_list_installed_packages(self):
        """Test listing installed packages using PIP (synchronous wrapper)."""
        asyncio.run(self.async_test_list_installed_packages())


class TestNPMPackageManager(unittest.TestCase):
    """Test cases for the NPMPackageManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.package_manager = NPMPackageManager(self.connection)
    
    async def async_test_install_package(self):
        """Test installing a package using NPM."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package
        result = await self.package_manager.install_package("test-package")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("npm install -g test-package")
    
    def test_install_package(self):
        """Test installing a package using NPM (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package())
    
    async def async_test_install_package_with_version(self):
        """Test installing a specific version of a package using NPM."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package installed", "")
        
        # Install a package with a specific version
        result = await self.package_manager.install_package("test-package", "1.0.0")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("npm install -g test-package@1.0.0")
    
    def test_install_package_with_version(self):
        """Test installing a specific version of a package using NPM (synchronous wrapper)."""
        asyncio.run(self.async_test_install_package_with_version())
    
    async def async_test_uninstall_package(self):
        """Test uninstalling a package using NPM."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package uninstalled", "")
        
        # Uninstall a package
        result = await self.package_manager.uninstall_package("test-package")
        
        # Check that the uninstallation was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("npm uninstall -g test-package")
    
    def test_uninstall_package(self):
        """Test uninstalling a package using NPM (synchronous wrapper)."""
        asyncio.run(self.async_test_uninstall_package())
    
    async def async_test_update_package(self):
        """Test updating a package using NPM."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "Package updated", "")
        
        # Update a package
        result = await self.package_manager.update_package("test-package")
        
        # Check that the update was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("npm update -g test-package")
    
    def test_update_package(self):
        """Test updating a package using NPM (synchronous wrapper)."""
        asyncio.run(self.async_test_update_package())
    
    async def async_test_list_installed_packages(self):
        """Test listing installed packages using NPM."""
        # Mock the connection's execute_command method
        npm_output = json.dumps({
            "dependencies": {
                "package1": {"version": "1.0.0"},
                "package2": {"version": "2.0.0"}
            }
        })
        self.connection.execute_command.return_value = (0, npm_output, "")
        
        # List installed packages
        packages = await self.package_manager.list_installed_packages()
        
        # Check that the correct packages were listed
        self.assertEqual(packages, {"package1": "1.0.0", "package2": "2.0.0"})
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_called_once_with("npm list --json -g")
    
    def test_list_installed_packages(self):
        """Test listing installed packages using NPM (synchronous wrapper)."""
        asyncio.run(self.async_test_list_installed_packages())


class TestPackageManagerFactory(unittest.TestCase):
    """Test cases for the PackageManagerFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
    
    async def async_test_create_apt_package_manager(self):
        """Test creating an APT package manager."""
        # Create an APT package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection, "apt")
        
        # Check that the correct type of package manager was created
        self.assertIsInstance(package_manager, APTPackageManager)
    
    def test_create_apt_package_manager(self):
        """Test creating an APT package manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_apt_package_manager())
    
    async def async_test_create_pip_package_manager(self):
        """Test creating a PIP package manager."""
        # Create a PIP package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection, "pip")
        
        # Check that the correct type of package manager was created
        self.assertIsInstance(package_manager, PIPPackageManager)
    
    def test_create_pip_package_manager(self):
        """Test creating a PIP package manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_pip_package_manager())
    
    async def async_test_create_npm_package_manager(self):
        """Test creating an NPM package manager."""
        # Create an NPM package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection, "npm")
        
        # Check that the correct type of package manager was created
        self.assertIsInstance(package_manager, NPMPackageManager)
    
    def test_create_npm_package_manager(self):
        """Test creating an NPM package manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_npm_package_manager())
    
    async def async_test_create_invalid_package_manager(self):
        """Test creating an invalid package manager."""
        # Try to create an invalid package manager
        with self.assertRaises(ValueError):
            await PackageManagerFactory.create_package_manager(self.connection, "invalid")
    
    def test_create_invalid_package_manager(self):
        """Test creating an invalid package manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_invalid_package_manager())
    
    async def async_test_detect_package_manager(self):
        """Test auto-detecting a package manager."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "/usr/bin/apt-get", ""),  # which apt-get
        ]
        
        # Auto-detect a package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection)
        
        # Check that the correct type of package manager was detected
        self.assertIsInstance(package_manager, APTPackageManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # which apt-get
            (0, "/usr/bin/pip3", ""),  # which pip3
        ]
        
        # Auto-detect a package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection)
        
        # Check that the correct type of package manager was detected
        self.assertIsInstance(package_manager, PIPPackageManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # which apt-get
            (1, "", ""),  # which pip3
            (0, "/usr/bin/npm", ""),  # which npm
        ]
        
        # Auto-detect a package manager
        package_manager = await PackageManagerFactory.create_package_manager(self.connection)
        
        # Check that the correct type of package manager was detected
        self.assertIsInstance(package_manager, NPMPackageManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # which apt-get
            (1, "", ""),  # which pip3
            (1, "", ""),  # which npm
        ]
        
        # Try to auto-detect a package manager when none are available
        with self.assertRaises(ValueError):
            await PackageManagerFactory.create_package_manager(self.connection)
    
    def test_detect_package_manager(self):
        """Test auto-detecting a package manager (synchronous wrapper)."""
        asyncio.run(self.async_test_detect_package_manager())


if __name__ == '__main__':
    unittest.main()
