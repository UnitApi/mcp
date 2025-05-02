#!/usr/bin/env python3
"""
Package Manager Module for UnitMCP

This module provides functionality for managing packages and dependencies
on remote devices. It supports various package managers including apt, pip,
npm, and others.
"""

import os
import sys
import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Set

from ..remote.connection import RemoteConnection

logger = logging.getLogger(__name__)

class PackageManager:
    """
    Base class for package managers.
    
    This class defines the interface that all package manager implementations must follow.
    """
    
    def __init__(self, connection: RemoteConnection):
        """
        Initialize a package manager.
        
        Args:
            connection: Remote connection to use for package management
        """
        self.connection = connection
    
    async def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a package on the remote device.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement install_package()")
    
    async def uninstall_package(self, package_name: str) -> bool:
        """
        Uninstall a package from the remote device.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement uninstall_package()")
    
    async def update_package(self, package_name: str) -> bool:
        """
        Update a package on the remote device.
        
        Args:
            package_name: Name of the package to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement update_package()")
    
    async def list_installed_packages(self) -> Dict[str, str]:
        """
        List all installed packages on the remote device.
        
        Returns:
            Dict[str, str]: Dictionary of package names and versions
        """
        raise NotImplementedError("Subclasses must implement list_installed_packages()")
    
    async def check_if_installed(self, package_name: str) -> Optional[str]:
        """
        Check if a package is installed on the remote device.
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            Optional[str]: Version of the installed package, or None if not installed
        """
        installed_packages = await self.list_installed_packages()
        return installed_packages.get(package_name)

class APTPackageManager(PackageManager):
    """
    APT package manager implementation.
    
    This class provides functionality for managing packages using APT on Debian-based systems.
    """
    
    async def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a package using APT.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        logger.info(f"Installing package '{package_name}' using APT...")
        
        # Build install command
        cmd = "sudo apt-get install -y"
        
        if version:
            cmd += f" {package_name}={version}"
        else:
            cmd += f" {package_name}"
        
        # Run install command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to install package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully installed package '{package_name}'")
        return True
    
    async def uninstall_package(self, package_name: str) -> bool:
        """
        Uninstall a package using APT.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        logger.info(f"Uninstalling package '{package_name}' using APT...")
        
        # Run uninstall command
        cmd = f"sudo apt-get remove -y {package_name}"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to uninstall package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully uninstalled package '{package_name}'")
        return True
    
    async def update_package(self, package_name: str) -> bool:
        """
        Update a package using APT.
        
        Args:
            package_name: Name of the package to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating package '{package_name}' using APT...")
        
        # Update package lists
        returncode, stdout, stderr = await self.connection.execute_command("sudo apt-get update")
        if returncode != 0:
            logger.error(f"Failed to update package lists: {stderr}")
            return False
        
        # Upgrade package
        cmd = f"sudo apt-get install --only-upgrade -y {package_name}"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to update package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully updated package '{package_name}'")
        return True
    
    async def list_installed_packages(self) -> Dict[str, str]:
        """
        List all installed packages using APT.
        
        Returns:
            Dict[str, str]: Dictionary of package names and versions
        """
        logger.info("Listing installed packages using APT...")
        
        # Run list command
        cmd = "dpkg-query -W -f='${Package} ${Version}\\n'"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to list installed packages: {stderr}")
            return {}
        
        # Parse output
        packages = {}
        for line in stdout.splitlines():
            if not line:
                continue
            
            parts = line.split(" ", 1)
            if len(parts) == 2:
                package_name, version = parts
                packages[package_name] = version
        
        return packages

class PIPPackageManager(PackageManager):
    """
    PIP package manager implementation.
    
    This class provides functionality for managing Python packages using PIP.
    """
    
    def __init__(self, connection: RemoteConnection, python_executable: str = "python3"):
        """
        Initialize a PIP package manager.
        
        Args:
            connection: Remote connection to use for package management
            python_executable: Python executable to use (default: "python3")
        """
        super().__init__(connection)
        self.python_executable = python_executable
    
    async def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a package using PIP.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        logger.info(f"Installing package '{package_name}' using PIP...")
        
        # Build install command
        cmd = f"sudo {self.python_executable} -m pip install"
        
        if version:
            cmd += f" {package_name}=={version}"
        else:
            cmd += f" {package_name}"
        
        # Run install command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to install package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully installed package '{package_name}'")
        return True
    
    async def uninstall_package(self, package_name: str) -> bool:
        """
        Uninstall a package using PIP.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        logger.info(f"Uninstalling package '{package_name}' using PIP...")
        
        # Run uninstall command
        cmd = f"sudo {self.python_executable} -m pip uninstall -y {package_name}"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to uninstall package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully uninstalled package '{package_name}'")
        return True
    
    async def update_package(self, package_name: str) -> bool:
        """
        Update a package using PIP.
        
        Args:
            package_name: Name of the package to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating package '{package_name}' using PIP...")
        
        # Run update command
        cmd = f"sudo {self.python_executable} -m pip install --upgrade {package_name}"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to update package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully updated package '{package_name}'")
        return True
    
    async def list_installed_packages(self) -> Dict[str, str]:
        """
        List all installed packages using PIP.
        
        Returns:
            Dict[str, str]: Dictionary of package names and versions
        """
        logger.info("Listing installed packages using PIP...")
        
        # Run list command
        cmd = f"{self.python_executable} -m pip list --format=json"
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to list installed packages: {stderr}")
            return {}
        
        # Parse output
        try:
            packages_json = json.loads(stdout)
            return {pkg["name"]: pkg["version"] for pkg in packages_json}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse PIP output: {stdout}")
            return {}

class NPMPackageManager(PackageManager):
    """
    NPM package manager implementation.
    
    This class provides functionality for managing Node.js packages using NPM.
    """
    
    def __init__(self, connection: RemoteConnection, global_packages: bool = True):
        """
        Initialize an NPM package manager.
        
        Args:
            connection: Remote connection to use for package management
            global_packages: Whether to manage global packages (default: True)
        """
        super().__init__(connection)
        self.global_packages = global_packages
    
    async def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a package using NPM.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        logger.info(f"Installing package '{package_name}' using NPM...")
        
        # Build install command
        cmd = "npm install"
        
        if self.global_packages:
            cmd += " -g"
        
        if version:
            cmd += f" {package_name}@{version}"
        else:
            cmd += f" {package_name}"
        
        # Run install command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to install package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully installed package '{package_name}'")
        return True
    
    async def uninstall_package(self, package_name: str) -> bool:
        """
        Uninstall a package using NPM.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        logger.info(f"Uninstalling package '{package_name}' using NPM...")
        
        # Run uninstall command
        cmd = f"npm uninstall"
        
        if self.global_packages:
            cmd += " -g"
        
        cmd += f" {package_name}"
        
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to uninstall package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully uninstalled package '{package_name}'")
        return True
    
    async def update_package(self, package_name: str) -> bool:
        """
        Update a package using NPM.
        
        Args:
            package_name: Name of the package to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating package '{package_name}' using NPM...")
        
        # Run update command
        cmd = f"npm update"
        
        if self.global_packages:
            cmd += " -g"
        
        cmd += f" {package_name}"
        
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to update package '{package_name}': {stderr}")
            return False
        
        logger.info(f"Successfully updated package '{package_name}'")
        return True
    
    async def list_installed_packages(self) -> Dict[str, str]:
        """
        List all installed packages using NPM.
        
        Returns:
            Dict[str, str]: Dictionary of package names and versions
        """
        logger.info("Listing installed packages using NPM...")
        
        # Run list command
        cmd = "npm list --json"
        
        if self.global_packages:
            cmd += " -g"
        
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0 and returncode != 1:  # npm returns 1 for warnings
            logger.error(f"Failed to list installed packages: {stderr}")
            return {}
        
        # Parse output
        try:
            npm_output = json.loads(stdout)
            dependencies = npm_output.get("dependencies", {})
            return {name: info.get("version", "") for name, info in dependencies.items()}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse NPM output: {stdout}")
            return {}

class PackageManagerFactory:
    """
    Factory class for creating package managers.
    
    This class provides functionality for creating the appropriate package manager
    based on the package manager type and the remote device's operating system.
    """
    
    @staticmethod
    async def create_package_manager(connection: RemoteConnection, 
                                    package_manager_type: Optional[str] = None) -> PackageManager:
        """
        Create a package manager for the specified type.
        
        Args:
            connection: Remote connection to use for package management
            package_manager_type: Type of package manager to create
                                 (apt, pip, npm, or None to auto-detect)
            
        Returns:
            PackageManager: An instance of the appropriate package manager class
            
        Raises:
            ValueError: If the package manager type is not supported or cannot be detected
        """
        if package_manager_type is None:
            # Auto-detect package manager
            return await PackageManagerFactory._detect_package_manager(connection)
        
        package_manager_type = package_manager_type.lower()
        
        if package_manager_type == "apt":
            return APTPackageManager(connection)
        elif package_manager_type == "pip":
            return PIPPackageManager(connection)
        elif package_manager_type == "npm":
            return NPMPackageManager(connection)
        else:
            raise ValueError(f"Unsupported package manager type: {package_manager_type}")
    
    @staticmethod
    async def _detect_package_manager(connection: RemoteConnection) -> PackageManager:
        """
        Detect the appropriate package manager for the remote device.
        
        Args:
            connection: Remote connection to use for package management
            
        Returns:
            PackageManager: An instance of the appropriate package manager class
            
        Raises:
            ValueError: If no supported package manager can be detected
        """
        # Check for APT
        returncode, stdout, stderr = await connection.execute_command("which apt-get")
        if returncode == 0:
            logger.info("Detected APT package manager")
            return APTPackageManager(connection)
        
        # Check for PIP
        returncode, stdout, stderr = await connection.execute_command("which pip3 || which pip")
        if returncode == 0:
            logger.info("Detected PIP package manager")
            return PIPPackageManager(connection)
        
        # Check for NPM
        returncode, stdout, stderr = await connection.execute_command("which npm")
        if returncode == 0:
            logger.info("Detected NPM package manager")
            return NPMPackageManager(connection)
        
        raise ValueError("No supported package manager detected on the remote device")
