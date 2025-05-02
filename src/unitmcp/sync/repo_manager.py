#!/usr/bin/env python3
"""
Repository Manager Module for UnitMCP

This module provides functionality for managing code repositories on remote devices.
It supports Git, Mercurial, and SVN repositories, with features for cloning,
updating, and synchronizing repositories.
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

class RepoManager:
    """
    Base class for repository managers.
    
    This class defines the interface that all repository manager implementations must follow.
    """
    
    def __init__(self, connection: RemoteConnection):
        """
        Initialize a repository manager.
        
        Args:
            connection: Remote connection to use for repository management
        """
        self.connection = connection
    
    async def clone_repo(self, repo_url: str, target_dir: str, branch: Optional[str] = None) -> bool:
        """
        Clone a repository to the remote device.
        
        Args:
            repo_url: URL of the repository to clone
            target_dir: Directory where the repository should be cloned
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if cloning was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement clone_repo()")
    
    async def update_repo(self, repo_dir: str, branch: Optional[str] = None) -> bool:
        """
        Update a repository on the remote device.
        
        Args:
            repo_dir: Directory of the repository
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement update_repo()")
    
    async def get_repo_status(self, repo_dir: str) -> Dict[str, Any]:
        """
        Get the status of a repository on the remote device.
        
        Args:
            repo_dir: Directory of the repository
            
        Returns:
            Dict[str, Any]: Repository status information
        """
        raise NotImplementedError("Subclasses must implement get_repo_status()")
    
    async def check_if_repo_exists(self, repo_dir: str) -> bool:
        """
        Check if a repository exists on the remote device.
        
        Args:
            repo_dir: Directory to check
            
        Returns:
            bool: True if the directory is a valid repository, False otherwise
        """
        raise NotImplementedError("Subclasses must implement check_if_repo_exists()")

class GitRepoManager(RepoManager):
    """
    Git repository manager implementation.
    
    This class provides functionality for managing Git repositories on remote devices.
    """
    
    async def clone_repo(self, repo_url: str, target_dir: str, branch: Optional[str] = None) -> bool:
        """
        Clone a Git repository to the remote device.
        
        Args:
            repo_url: URL of the Git repository to clone
            target_dir: Directory where the repository should be cloned
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if cloning was successful, False otherwise
        """
        logger.info(f"Cloning Git repository '{repo_url}' to '{target_dir}'...")
        
        # Check if target directory exists
        returncode, stdout, stderr = await self.connection.execute_command(f"test -d '{target_dir}' && echo 'exists'")
        target_dir_exists = returncode == 0 and "exists" in stdout
        
        if target_dir_exists:
            # Check if it's already a Git repository
            is_repo = await self.check_if_repo_exists(target_dir)
            if is_repo:
                logger.info(f"Directory '{target_dir}' is already a Git repository")
                return await self.update_repo(target_dir, branch)
            else:
                logger.error(f"Directory '{target_dir}' already exists but is not a Git repository")
                return False
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(target_dir)
        if parent_dir:
            returncode, stdout, stderr = await self.connection.execute_command(f"mkdir -p '{parent_dir}'")
            if returncode != 0:
                logger.error(f"Failed to create parent directory '{parent_dir}': {stderr}")
                return False
        
        # Build clone command
        cmd = f"git clone"
        
        if branch:
            cmd += f" -b {branch}"
        
        cmd += f" {repo_url} '{target_dir}'"
        
        # Run clone command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to clone Git repository: {stderr}")
            return False
        
        logger.info(f"Successfully cloned Git repository to '{target_dir}'")
        return True
    
    async def update_repo(self, repo_dir: str, branch: Optional[str] = None) -> bool:
        """
        Update a Git repository on the remote device.
        
        Args:
            repo_dir: Directory of the Git repository
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating Git repository in '{repo_dir}'...")
        
        # Check if it's a Git repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not a Git repository")
            return False
        
        # Fetch updates
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git fetch")
        if returncode != 0:
            logger.error(f"Failed to fetch updates: {stderr}")
            return False
        
        # Checkout branch if specified
        if branch:
            returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git checkout {branch}")
            if returncode != 0:
                logger.error(f"Failed to checkout branch '{branch}': {stderr}")
                return False
        
        # Pull updates
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git pull")
        if returncode != 0:
            logger.error(f"Failed to pull updates: {stderr}")
            return False
        
        logger.info(f"Successfully updated Git repository in '{repo_dir}'")
        return True
    
    async def get_repo_status(self, repo_dir: str) -> Dict[str, Any]:
        """
        Get the status of a Git repository on the remote device.
        
        Args:
            repo_dir: Directory of the Git repository
            
        Returns:
            Dict[str, Any]: Repository status information
        """
        logger.info(f"Getting status of Git repository in '{repo_dir}'...")
        
        # Check if it's a Git repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not a Git repository")
            return {}
        
        status = {}
        
        # Get current branch
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git branch --show-current")
        if returncode == 0:
            status["branch"] = stdout.strip()
        
        # Get current commit
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git rev-parse HEAD")
        if returncode == 0:
            status["commit"] = stdout.strip()
        
        # Get remote URL
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git config --get remote.origin.url")
        if returncode == 0:
            status["remote_url"] = stdout.strip()
        
        # Check for uncommitted changes
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git status --porcelain")
        status["has_changes"] = returncode == 0 and bool(stdout.strip())
        
        # Check for unpushed commits
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git log origin/{status.get('branch', 'HEAD')}..HEAD --oneline")
        status["has_unpushed_commits"] = returncode == 0 and bool(stdout.strip())
        
        return status
    
    async def check_if_repo_exists(self, repo_dir: str) -> bool:
        """
        Check if a directory is a valid Git repository on the remote device.
        
        Args:
            repo_dir: Directory to check
            
        Returns:
            bool: True if the directory is a valid Git repository, False otherwise
        """
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && git rev-parse --is-inside-work-tree")
        return returncode == 0 and "true" in stdout.lower()

class MercurialRepoManager(RepoManager):
    """
    Mercurial repository manager implementation.
    
    This class provides functionality for managing Mercurial repositories on remote devices.
    """
    
    async def clone_repo(self, repo_url: str, target_dir: str, branch: Optional[str] = None) -> bool:
        """
        Clone a Mercurial repository to the remote device.
        
        Args:
            repo_url: URL of the Mercurial repository to clone
            target_dir: Directory where the repository should be cloned
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if cloning was successful, False otherwise
        """
        logger.info(f"Cloning Mercurial repository '{repo_url}' to '{target_dir}'...")
        
        # Check if target directory exists
        returncode, stdout, stderr = await self.connection.execute_command(f"test -d '{target_dir}' && echo 'exists'")
        target_dir_exists = returncode == 0 and "exists" in stdout
        
        if target_dir_exists:
            # Check if it's already a Mercurial repository
            is_repo = await self.check_if_repo_exists(target_dir)
            if is_repo:
                logger.info(f"Directory '{target_dir}' is already a Mercurial repository")
                return await self.update_repo(target_dir, branch)
            else:
                logger.error(f"Directory '{target_dir}' already exists but is not a Mercurial repository")
                return False
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(target_dir)
        if parent_dir:
            returncode, stdout, stderr = await self.connection.execute_command(f"mkdir -p '{parent_dir}'")
            if returncode != 0:
                logger.error(f"Failed to create parent directory '{parent_dir}': {stderr}")
                return False
        
        # Build clone command
        cmd = f"hg clone"
        
        if branch:
            cmd += f" -r {branch}"
        
        cmd += f" {repo_url} '{target_dir}'"
        
        # Run clone command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to clone Mercurial repository: {stderr}")
            return False
        
        logger.info(f"Successfully cloned Mercurial repository to '{target_dir}'")
        return True
    
    async def update_repo(self, repo_dir: str, branch: Optional[str] = None) -> bool:
        """
        Update a Mercurial repository on the remote device.
        
        Args:
            repo_dir: Directory of the Mercurial repository
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating Mercurial repository in '{repo_dir}'...")
        
        # Check if it's a Mercurial repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not a Mercurial repository")
            return False
        
        # Pull updates
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg pull")
        if returncode != 0:
            logger.error(f"Failed to pull updates: {stderr}")
            return False
        
        # Update to branch if specified
        update_cmd = f"cd '{repo_dir}' && hg update"
        if branch:
            update_cmd += f" -r {branch}"
        
        returncode, stdout, stderr = await self.connection.execute_command(update_cmd)
        if returncode != 0:
            logger.error(f"Failed to update repository: {stderr}")
            return False
        
        logger.info(f"Successfully updated Mercurial repository in '{repo_dir}'")
        return True
    
    async def get_repo_status(self, repo_dir: str) -> Dict[str, Any]:
        """
        Get the status of a Mercurial repository on the remote device.
        
        Args:
            repo_dir: Directory of the Mercurial repository
            
        Returns:
            Dict[str, Any]: Repository status information
        """
        logger.info(f"Getting status of Mercurial repository in '{repo_dir}'...")
        
        # Check if it's a Mercurial repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not a Mercurial repository")
            return {}
        
        status = {}
        
        # Get current branch
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg branch")
        if returncode == 0:
            status["branch"] = stdout.strip()
        
        # Get current revision
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg id -i")
        if returncode == 0:
            status["revision"] = stdout.strip()
        
        # Get remote URL
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg paths default")
        if returncode == 0:
            status["remote_url"] = stdout.strip()
        
        # Check for uncommitted changes
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg status")
        status["has_changes"] = returncode == 0 and bool(stdout.strip())
        
        # Check for unpushed commits
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg outgoing --quiet")
        status["has_unpushed_commits"] = returncode == 1  # hg returns 1 if there are outgoing changes
        
        return status
    
    async def check_if_repo_exists(self, repo_dir: str) -> bool:
        """
        Check if a directory is a valid Mercurial repository on the remote device.
        
        Args:
            repo_dir: Directory to check
            
        Returns:
            bool: True if the directory is a valid Mercurial repository, False otherwise
        """
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && hg root")
        return returncode == 0

class SVNRepoManager(RepoManager):
    """
    SVN repository manager implementation.
    
    This class provides functionality for managing SVN repositories on remote devices.
    """
    
    async def clone_repo(self, repo_url: str, target_dir: str, branch: Optional[str] = None) -> bool:
        """
        Checkout an SVN repository to the remote device.
        
        Args:
            repo_url: URL of the SVN repository to checkout
            target_dir: Directory where the repository should be checked out
            branch: Branch to checkout (optional)
            
        Returns:
            bool: True if checkout was successful, False otherwise
        """
        logger.info(f"Checking out SVN repository '{repo_url}' to '{target_dir}'...")
        
        # Check if target directory exists
        returncode, stdout, stderr = await self.connection.execute_command(f"test -d '{target_dir}' && echo 'exists'")
        target_dir_exists = returncode == 0 and "exists" in stdout
        
        if target_dir_exists:
            # Check if it's already an SVN repository
            is_repo = await self.check_if_repo_exists(target_dir)
            if is_repo:
                logger.info(f"Directory '{target_dir}' is already an SVN repository")
                return await self.update_repo(target_dir)
            else:
                logger.error(f"Directory '{target_dir}' already exists but is not an SVN repository")
                return False
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(target_dir)
        if parent_dir:
            returncode, stdout, stderr = await self.connection.execute_command(f"mkdir -p '{parent_dir}'")
            if returncode != 0:
                logger.error(f"Failed to create parent directory '{parent_dir}': {stderr}")
                return False
        
        # Build checkout command
        cmd = f"svn checkout"
        
        # Append branch/tag path if specified
        if branch:
            if "branches" not in repo_url and "tags" not in repo_url:
                if repo_url.endswith("/"):
                    repo_url = f"{repo_url}branches/{branch}"
                else:
                    repo_url = f"{repo_url}/branches/{branch}"
        
        cmd += f" {repo_url} '{target_dir}'"
        
        # Run checkout command
        returncode, stdout, stderr = await self.connection.execute_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to checkout SVN repository: {stderr}")
            return False
        
        logger.info(f"Successfully checked out SVN repository to '{target_dir}'")
        return True
    
    async def update_repo(self, repo_dir: str, branch: Optional[str] = None) -> bool:
        """
        Update an SVN repository on the remote device.
        
        Args:
            repo_dir: Directory of the SVN repository
            branch: Branch to switch to (optional)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating SVN repository in '{repo_dir}'...")
        
        # Check if it's an SVN repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not an SVN repository")
            return False
        
        # Switch to branch if specified
        if branch:
            # Get repository URL
            returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn info --show-item url")
            if returncode != 0:
                logger.error(f"Failed to get repository URL: {stderr}")
                return False
            
            repo_url = stdout.strip()
            
            # Extract base URL (remove branches/tags/trunk)
            base_url = re.sub(r"/(branches|tags|trunk).*$", "", repo_url)
            
            # Build switch command
            switch_url = f"{base_url}/branches/{branch}"
            switch_cmd = f"cd '{repo_dir}' && svn switch {switch_url}"
            
            returncode, stdout, stderr = await self.connection.execute_command(switch_cmd)
            if returncode != 0:
                logger.error(f"Failed to switch to branch '{branch}': {stderr}")
                return False
        
        # Update repository
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn update")
        if returncode != 0:
            logger.error(f"Failed to update repository: {stderr}")
            return False
        
        logger.info(f"Successfully updated SVN repository in '{repo_dir}'")
        return True
    
    async def get_repo_status(self, repo_dir: str) -> Dict[str, Any]:
        """
        Get the status of an SVN repository on the remote device.
        
        Args:
            repo_dir: Directory of the SVN repository
            
        Returns:
            Dict[str, Any]: Repository status information
        """
        logger.info(f"Getting status of SVN repository in '{repo_dir}'...")
        
        # Check if it's an SVN repository
        is_repo = await self.check_if_repo_exists(repo_dir)
        if not is_repo:
            logger.error(f"Directory '{repo_dir}' is not an SVN repository")
            return {}
        
        status = {}
        
        # Get repository URL
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn info --show-item url")
        if returncode == 0:
            status["url"] = stdout.strip()
            
            # Extract branch/tag information
            branch_match = re.search(r"/(branches|tags|trunk)/([^/]+)?", status["url"])
            if branch_match:
                status["branch_type"] = branch_match.group(1)
                if branch_match.group(2):
                    status["branch"] = branch_match.group(2)
                else:
                    status["branch"] = "trunk"
        
        # Get revision
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn info --show-item revision")
        if returncode == 0:
            status["revision"] = stdout.strip()
        
        # Check for uncommitted changes
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn status")
        status["has_changes"] = returncode == 0 and bool(stdout.strip())
        
        return status
    
    async def check_if_repo_exists(self, repo_dir: str) -> bool:
        """
        Check if a directory is a valid SVN repository on the remote device.
        
        Args:
            repo_dir: Directory to check
            
        Returns:
            bool: True if the directory is a valid SVN repository, False otherwise
        """
        returncode, stdout, stderr = await self.connection.execute_command(f"cd '{repo_dir}' && svn info")
        return returncode == 0

class RepoManagerFactory:
    """
    Factory class for creating repository managers.
    
    This class provides functionality for creating the appropriate repository manager
    based on the repository type or by detecting the repository type.
    """
    
    @staticmethod
    async def create_repo_manager(connection: RemoteConnection, 
                                 repo_type: Optional[str] = None,
                                 repo_dir: Optional[str] = None) -> RepoManager:
        """
        Create a repository manager for the specified type.
        
        Args:
            connection: Remote connection to use for repository management
            repo_type: Type of repository manager to create
                      (git, hg, svn, or None to auto-detect)
            repo_dir: Directory of the repository (required for auto-detection)
            
        Returns:
            RepoManager: An instance of the appropriate repository manager class
            
        Raises:
            ValueError: If the repository type is not supported or cannot be detected
        """
        if repo_type is None:
            if repo_dir is None:
                raise ValueError("Repository directory must be specified for auto-detection")
            
            # Auto-detect repository type
            return await RepoManagerFactory._detect_repo_type(connection, repo_dir)
        
        repo_type = repo_type.lower()
        
        if repo_type == "git":
            return GitRepoManager(connection)
        elif repo_type in ["hg", "mercurial"]:
            return MercurialRepoManager(connection)
        elif repo_type == "svn":
            return SVNRepoManager(connection)
        else:
            raise ValueError(f"Unsupported repository type: {repo_type}")
    
    @staticmethod
    async def _detect_repo_type(connection: RemoteConnection, repo_dir: str) -> RepoManager:
        """
        Detect the type of repository in the specified directory.
        
        Args:
            connection: Remote connection to use for repository management
            repo_dir: Directory of the repository
            
        Returns:
            RepoManager: An instance of the appropriate repository manager class
            
        Raises:
            ValueError: If the repository type cannot be detected
        """
        # Check if it's a Git repository
        returncode, stdout, stderr = await connection.execute_command(f"cd '{repo_dir}' && git rev-parse --is-inside-work-tree")
        if returncode == 0 and "true" in stdout.lower():
            logger.info(f"Detected Git repository in '{repo_dir}'")
            return GitRepoManager(connection)
        
        # Check if it's a Mercurial repository
        returncode, stdout, stderr = await connection.execute_command(f"cd '{repo_dir}' && hg root")
        if returncode == 0:
            logger.info(f"Detected Mercurial repository in '{repo_dir}'")
            return MercurialRepoManager(connection)
        
        # Check if it's an SVN repository
        returncode, stdout, stderr = await connection.execute_command(f"cd '{repo_dir}' && svn info")
        if returncode == 0:
            logger.info(f"Detected SVN repository in '{repo_dir}'")
            return SVNRepoManager(connection)
        
        raise ValueError(f"Could not detect repository type in '{repo_dir}'")
