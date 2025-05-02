#!/usr/bin/env python3
"""
File Synchronization Module for UnitMCP

This module provides functionality for synchronizing files between the host system
and remote devices. It supports bidirectional synchronization, file transfer, and
file comparison.
"""

import os
import sys
import asyncio
import logging
import hashlib
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Set

from ..remote.connection import RemoteConnection

logger = logging.getLogger(__name__)

class FileSync:
    """
    File synchronization class.
    
    This class provides functionality for synchronizing files between the host system
    and remote devices.
    """
    
    def __init__(self, connection: RemoteConnection):
        """
        Initialize file synchronization.
        
        Args:
            connection: Remote connection to use for file transfer
        """
        self.connection = connection
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file to the remote device.
        
        Args:
            local_path: Path to the local file
            remote_path: Path where the file should be stored on the remote device
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
        
        return await self.connection.upload_file(local_path, remote_path)
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the remote device.
        
        Args:
            remote_path: Path to the file on the remote device
            local_path: Path where the file should be stored locally
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        # Create local directory if it doesn't exist
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        return await self.connection.download_file(remote_path, local_path)
    
    async def compare_files(self, local_path: str, remote_path: str) -> bool:
        """
        Compare a local file with a remote file.
        
        Args:
            local_path: Path to the local file
            remote_path: Path to the file on the remote device
            
        Returns:
            bool: True if files are identical, False otherwise
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
        
        # Calculate local file hash
        local_hash = self._calculate_file_hash(local_path)
        
        # Download remote file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            if not await self.download_file(remote_path, temp_path):
                logger.error(f"Failed to download remote file: {remote_path}")
                return False
            
            # Calculate remote file hash
            remote_hash = self._calculate_file_hash(temp_path)
            
            # Compare hashes
            return local_hash == remote_hash
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate the SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read and update hash in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        
        return sha256.hexdigest()
    
    async def sync_directory(self, local_dir: str, remote_dir: str, 
                            direction: str = "upload", delete: bool = False,
                            exclude: Optional[List[str]] = None) -> bool:
        """
        Synchronize a directory between the local system and the remote device.
        
        Args:
            local_dir: Path to the local directory
            remote_dir: Path to the directory on the remote device
            direction: Synchronization direction ("upload", "download", or "both")
            delete: Whether to delete files that don't exist in the source
            exclude: List of file/directory patterns to exclude
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        if direction not in ["upload", "download", "both"]:
            logger.error(f"Invalid synchronization direction: {direction}")
            return False
        
        if not os.path.isdir(local_dir):
            logger.error(f"Local directory does not exist: {local_dir}")
            return False
        
        exclude = exclude or []
        
        # Check if remote directory exists
        returncode, stdout, stderr = await self.connection.execute_command(f"test -d '{remote_dir}' && echo 'exists'")
        remote_dir_exists = returncode == 0 and "exists" in stdout
        
        if not remote_dir_exists:
            # Create remote directory
            returncode, stdout, stderr = await self.connection.execute_command(f"mkdir -p '{remote_dir}'")
            if returncode != 0:
                logger.error(f"Failed to create remote directory: {remote_dir}")
                return False
        
        # Get list of files in local directory
        local_files = self._list_local_files(local_dir, exclude)
        
        # Get list of files in remote directory
        remote_files = await self._list_remote_files(remote_dir, exclude)
        
        success = True
        
        # Upload files
        if direction in ["upload", "both"]:
            for rel_path in local_files:
                local_path = os.path.join(local_dir, rel_path)
                remote_path = os.path.join(remote_dir, rel_path)
                
                # Check if file needs to be uploaded
                needs_upload = True
                if rel_path in remote_files:
                    # Compare files
                    if await self.compare_files(local_path, remote_path):
                        needs_upload = False
                
                if needs_upload:
                    logger.info(f"Uploading file: {rel_path}")
                    if not await self.upload_file(local_path, remote_path):
                        logger.error(f"Failed to upload file: {rel_path}")
                        success = False
            
            # Delete remote files that don't exist locally
            if delete:
                for rel_path in remote_files:
                    if rel_path not in local_files:
                        logger.info(f"Deleting remote file: {rel_path}")
                        returncode, stdout, stderr = await self.connection.execute_command(f"rm '{os.path.join(remote_dir, rel_path)}'")
                        if returncode != 0:
                            logger.error(f"Failed to delete remote file: {rel_path}")
                            success = False
        
        # Download files
        if direction in ["download", "both"]:
            for rel_path in remote_files:
                local_path = os.path.join(local_dir, rel_path)
                remote_path = os.path.join(remote_dir, rel_path)
                
                # Check if file needs to be downloaded
                needs_download = True
                if rel_path in local_files:
                    # Compare files
                    if await self.compare_files(local_path, remote_path):
                        needs_download = False
                
                if needs_download:
                    logger.info(f"Downloading file: {rel_path}")
                    if not await self.download_file(remote_path, local_path):
                        logger.error(f"Failed to download file: {rel_path}")
                        success = False
            
            # Delete local files that don't exist remotely
            if delete:
                for rel_path in local_files:
                    if rel_path not in remote_files:
                        logger.info(f"Deleting local file: {rel_path}")
                        os.unlink(os.path.join(local_dir, rel_path))
        
        return success
    
    def _list_local_files(self, directory: str, exclude: List[str]) -> Set[str]:
        """
        List all files in a local directory recursively.
        
        Args:
            directory: Path to the directory
            exclude: List of file/directory patterns to exclude
            
        Returns:
            Set[str]: Set of relative file paths
        """
        files = set()
        
        for root, dirs, filenames in os.walk(directory):
            # Apply exclusions to directories
            dirs[:] = [d for d in dirs if not any(e in os.path.join(root, d) for e in exclude)]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                # Skip excluded files
                if any(e in file_path for e in exclude):
                    continue
                
                # Get relative path
                rel_path = os.path.relpath(file_path, directory)
                files.add(rel_path)
        
        return files
    
    async def _list_remote_files(self, directory: str, exclude: List[str]) -> Set[str]:
        """
        List all files in a remote directory recursively.
        
        Args:
            directory: Path to the directory on the remote device
            exclude: List of file/directory patterns to exclude
            
        Returns:
            Set[str]: Set of relative file paths
        """
        files = set()
        
        # Use find command to list all files
        find_cmd = f"find '{directory}' -type f"
        
        # Add exclusions
        for pattern in exclude:
            find_cmd += f" -not -path '*{pattern}*'"
        
        returncode, stdout, stderr = await self.connection.execute_command(find_cmd)
        
        if returncode != 0:
            logger.error(f"Failed to list remote files: {stderr}")
            return files
        
        # Process output
        for line in stdout.splitlines():
            if not line:
                continue
            
            # Get relative path
            rel_path = os.path.relpath(line, directory)
            files.add(rel_path)
        
        return files
    
    async def sync_file(self, local_path: str, remote_path: str, direction: str = "upload") -> bool:
        """
        Synchronize a single file between the local system and the remote device.
        
        Args:
            local_path: Path to the local file
            remote_path: Path to the file on the remote device
            direction: Synchronization direction ("upload", "download", or "both")
            
        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        if direction not in ["upload", "download", "both"]:
            logger.error(f"Invalid synchronization direction: {direction}")
            return False
        
        if direction in ["upload", "both"]:
            if not os.path.exists(local_path):
                logger.error(f"Local file does not exist: {local_path}")
                return False
            
            # Check if file needs to be uploaded
            needs_upload = True
            
            # Check if remote file exists
            returncode, stdout, stderr = await self.connection.execute_command(f"test -f '{remote_path}' && echo 'exists'")
            remote_file_exists = returncode == 0 and "exists" in stdout
            
            if remote_file_exists:
                # Compare files
                if await self.compare_files(local_path, remote_path):
                    needs_upload = False
            
            if needs_upload:
                logger.info(f"Uploading file: {local_path} -> {remote_path}")
                if not await self.upload_file(local_path, remote_path):
                    logger.error(f"Failed to upload file: {local_path}")
                    return False
        
        if direction in ["download", "both"]:
            # Check if remote file exists
            returncode, stdout, stderr = await self.connection.execute_command(f"test -f '{remote_path}' && echo 'exists'")
            remote_file_exists = returncode == 0 and "exists" in stdout
            
            if not remote_file_exists:
                logger.error(f"Remote file does not exist: {remote_path}")
                return False
            
            # Check if file needs to be downloaded
            needs_download = True
            
            if os.path.exists(local_path):
                # Compare files
                if await self.compare_files(local_path, remote_path):
                    needs_download = False
            
            if needs_download:
                logger.info(f"Downloading file: {remote_path} -> {local_path}")
                if not await self.download_file(remote_path, local_path):
                    logger.error(f"Failed to download file: {remote_path}")
                    return False
        
        return True
