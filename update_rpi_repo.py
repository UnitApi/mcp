#!/usr/bin/env python3
"""
Update Raspberry Pi MCP Repository

This script connects to a Raspberry Pi via SSH and updates the MCP repository
using git. It can also clone the repository if it doesn't exist.
"""

import os
import sys
import asyncio
import logging
import argparse
import subprocess
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("UpdateRpiRepo")

class RepoUpdater:
    """
    A utility class to update or clone the MCP repository on a Raspberry Pi.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RepoUpdater.
        """
        self.config = config
        self.host = config.get('host', '192.168.188.154')
        self.ssh_username = config.get('ssh_username', 'pi')
        self.ssh_key_path = config.get('ssh_key_path', None)
        self.repo_path = config.get('repo_path', '~/mcp')
        self.repo_url = config.get('repo_url', 'https://github.com/UnitApi/mcp.git')
        self.branch = config.get('branch', 'main')
        self.verbose = config.get('verbose', False)
        
        # Set up logging
        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    
    async def update_repo(self) -> bool:
        """
        Update the MCP repository on the Raspberry Pi.
        
        This method will:
        1. Check if the repository exists
        2. If it exists, update it using git pull
        3. If it doesn't exist, clone it
        
        Returns:
            True if the repository was updated successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Check if the repository exists
            check_cmd = f"test -d {self.repo_path}/.git && echo 'Repo exists' || echo 'Repo does not exist'"
            full_check_cmd = f"{ssh_cmd} '{check_cmd}'"
            
            logger.info(f"Checking if repository exists: {full_check_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode().strip()
            
            if "Repo exists" in output:
                logger.info(f"Repository exists at {self.repo_path}, updating...")
                return await self._update_existing_repo()
            else:
                # Check if directory exists but is not a git repository
                check_dir_cmd = f"test -d {self.repo_path} && echo 'Dir exists' || echo 'Dir does not exist'"
                full_check_dir_cmd = f"{ssh_cmd} '{check_dir_cmd}'"
                
                logger.info(f"Checking if directory exists: {full_check_dir_cmd}")
                process = await asyncio.create_subprocess_shell(
                    full_check_dir_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                dir_output = stdout.decode().strip()
                
                if "Dir exists" in dir_output:
                    logger.info(f"Directory exists at {self.repo_path} but is not a git repository, backing up and cloning...")
                    if not await self._backup_existing_directory():
                        return False
                
                logger.info(f"Cloning repository to {self.repo_path}...")
                return await self._clone_repo()
            
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            return False
    
    async def _update_existing_repo(self) -> bool:
        """
        Update an existing repository using git pull.
        
        Returns:
            True if the repository was updated successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Update the repository
            update_cmd = f"cd {self.repo_path} && git pull origin {self.branch}"
            full_update_cmd = f"{ssh_cmd} '{update_cmd}'"
            
            logger.info(f"Updating repository: {full_update_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_update_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode()
            error = stderr.decode()
            
            if process.returncode != 0:
                logger.error(f"Failed to update repository: {error}")
                return False
            
            logger.info(f"Repository updated successfully: {output}")
            
            # Create virtual environment if it doesn't exist and install dependencies
            venv_cmd = f"cd {self.repo_path} && " \
                      f"if [ ! -d venv ]; then python -m venv venv; fi && " \
                      f"source venv/bin/activate && " \
                      f"if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"
            full_venv_cmd = f"{ssh_cmd} '{venv_cmd}'"
            
            logger.info(f"Setting up virtual environment and installing dependencies: {full_venv_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_venv_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            dep_output = stdout.decode()
            dep_error = stderr.decode()
            
            if process.returncode != 0:
                logger.error(f"Failed to install dependencies: {dep_error}")
                logger.warning(f"Warning during dependency installation: {dep_error}")
            else:
                logger.info(f"Dependencies installed successfully: {dep_output}")
            
            return True
        except Exception as e:
            logger.error(f"Error updating repository: {str(e)}")
            return False
    
    async def _clone_repo(self) -> bool:
        """
        Clone the repository.
        
        Returns:
            True if the repository was cloned successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Clone the repository
            clone_cmd = f"git clone {self.repo_url} {self.repo_path}"
            full_clone_cmd = f"{ssh_cmd} '{clone_cmd}'"
            
            logger.info(f"Cloning repository: {full_clone_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode()
            error = stderr.decode()
            
            if process.returncode != 0:
                logger.error(f"Failed to clone repository: {error}")
                return False
            
            logger.info(f"Repository cloned successfully: {output}")
            
            # Create virtual environment and install dependencies
            venv_cmd = f"cd {self.repo_path} && " \
                      f"python -m venv venv && " \
                      f"source venv/bin/activate && " \
                      f"if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"
            full_venv_cmd = f"{ssh_cmd} '{venv_cmd}'"
            
            logger.info(f"Setting up virtual environment and installing dependencies: {full_venv_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_venv_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            dep_output = stdout.decode()
            dep_error = stderr.decode()
            
            if process.returncode != 0:
                logger.error(f"Failed to install dependencies: {dep_error}")
                logger.warning(f"Warning during dependency installation: {dep_error}")
            else:
                logger.info(f"Dependencies installed successfully: {dep_output}")
            
            return True
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return False
    
    async def _backup_existing_directory(self) -> bool:
        """
        Backup an existing directory by renaming it.
        
        Returns:
            True if the directory was backed up successfully, False otherwise
        """
        try:
            # Build the SSH command
            ssh_cmd = self._build_ssh_command()
            
            # Backup the existing directory
            backup_path = f"{self.repo_path}_backup_{int(asyncio.get_event_loop().time())}"
            backup_cmd = f"mv {self.repo_path} {backup_path}"
            full_backup_cmd = f"{ssh_cmd} '{backup_cmd}'"
            
            logger.info(f"Backing up existing directory: {full_backup_cmd}")
            process = await asyncio.create_subprocess_shell(
                full_backup_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to backup existing directory: {stderr.decode()}")
                return False
            
            logger.info(f"Existing directory backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up existing directory: {e}")
            return False
    
    def _build_ssh_command(self) -> str:
        """
        Build the SSH command to connect to the Raspberry Pi.
        
        Returns:
            The SSH command string
        """
        ssh_cmd = f"ssh"
        
        # Add options
        ssh_cmd += f" -o StrictHostKeyChecking=no -o ConnectTimeout=10"
        
        # Add key file if provided
        if self.ssh_key_path:
            ssh_cmd += f" -i {self.ssh_key_path}"
        
        # Add username and host
        ssh_cmd += f" {self.ssh_username}@{self.host}"
        
        return ssh_cmd

async def main():
    """
    Main entry point for the RepoUpdater.
    """
    parser = argparse.ArgumentParser(description="Update or clone the MCP repository on a Raspberry Pi")
    parser.add_argument("--host", default="192.168.188.154", help="The IP address of the Raspberry Pi")
    parser.add_argument("--ssh-username", default="pi", help="SSH username for the Raspberry Pi")
    parser.add_argument("--ssh-key-path", help="Path to the SSH private key file (optional)")
    parser.add_argument("--repo-path", default="~/mcp", help="Path to the MCP repository on the Raspberry Pi")
    parser.add_argument("--repo-url", default="https://github.com/UnitApi/mcp.git", help="URL of the MCP repository")
    parser.add_argument("--branch", default="main", help="Branch to checkout")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Create the config dictionary
    config = {
        "host": args.host,
        "ssh_username": args.ssh_username,
        "ssh_key_path": args.ssh_key_path,
        "repo_path": args.repo_path,
        "repo_url": args.repo_url,
        "branch": args.branch,
        "verbose": args.verbose
    }
    
    # Create the RepoUpdater
    updater = RepoUpdater(config)
    
    # Update the repository
    if not await updater.update_repo():
        logger.error("Failed to update repository")
        sys.exit(1)
    
    logger.info("Repository updated successfully")

if __name__ == "__main__":
    asyncio.run(main())
