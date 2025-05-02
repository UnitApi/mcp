#!/usr/bin/env python3
"""
Unit tests for the repository manager module.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.sync.repo_manager import (
    RepoManager,
    GitRepoManager,
    MercurialRepoManager,
    SVNRepoManager,
    RepoManagerFactory
)
from unitmcp.remote.connection import RemoteConnection

class TestRepoManager(unittest.TestCase):
    """Test cases for the RepoManager base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.repo_manager = RepoManager(self.connection)
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.repo_manager.clone_repo("repo_url", "target_dir"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.repo_manager.update_repo("repo_dir"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.repo_manager.get_repo_status("repo_dir"))
        
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.repo_manager.check_if_repo_exists("repo_dir"))


class TestGitRepoManager(unittest.TestCase):
    """Test cases for the GitRepoManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.repo_manager = GitRepoManager(self.connection)
    
    async def async_test_clone_repo(self):
        """Test cloning a Git repository."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # Directory doesn't exist
            (0, "", ""),  # mkdir -p
            (0, "Cloning into 'target_dir'...", "")  # git clone
        ]
        
        # Clone a repository
        result = await self.repo_manager.clone_repo("https://github.com/user/repo.git", "/path/to/target_dir")
        
        # Check that the cloning was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_any_call("test -d '/path/to/target_dir' && echo 'exists'")
        self.connection.execute_command.assert_any_call("mkdir -p '/path/to'")
        self.connection.execute_command.assert_any_call("git clone https://github.com/user/repo.git '/path/to/target_dir'")
    
    def test_clone_repo(self):
        """Test cloning a Git repository (synchronous wrapper)."""
        asyncio.run(self.async_test_clone_repo())
    
    async def async_test_clone_repo_with_branch(self):
        """Test cloning a Git repository with a specific branch."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # Directory doesn't exist
            (0, "", ""),  # mkdir -p
            (0, "Cloning into 'target_dir'...", "")  # git clone
        ]
        
        # Clone a repository with a specific branch
        result = await self.repo_manager.clone_repo(
            "https://github.com/user/repo.git",
            "/path/to/target_dir",
            branch="develop"
        )
        
        # Check that the cloning was successful
        self.assertTrue(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_any_call("git clone -b develop https://github.com/user/repo.git '/path/to/target_dir'")
    
    def test_clone_repo_with_branch(self):
        """Test cloning a Git repository with a specific branch (synchronous wrapper)."""
        asyncio.run(self.async_test_clone_repo_with_branch())
    
    async def async_test_update_repo(self):
        """Test updating a Git repository."""
        # Mock the check_if_repo_exists method
        original_check_if_repo_exists = self.repo_manager.check_if_repo_exists
        
        async def mock_check_if_repo_exists(repo_dir):
            return True
        
        self.repo_manager.check_if_repo_exists = mock_check_if_repo_exists
        
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "", ""),  # git fetch
            (0, "", "")   # git pull
        ]
        
        try:
            # Update a repository
            result = await self.repo_manager.update_repo("/path/to/repo")
            
            # Check that the update was successful
            self.assertTrue(result)
            
            # Check that the execute_command method was called with the correct arguments
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git fetch")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git pull")
        finally:
            # Restore original method
            self.repo_manager.check_if_repo_exists = original_check_if_repo_exists
    
    def test_update_repo(self):
        """Test updating a Git repository (synchronous wrapper)."""
        asyncio.run(self.async_test_update_repo())
    
    async def async_test_update_repo_with_branch(self):
        """Test updating a Git repository with a specific branch."""
        # Mock the check_if_repo_exists method
        original_check_if_repo_exists = self.repo_manager.check_if_repo_exists
        
        async def mock_check_if_repo_exists(repo_dir):
            return True
        
        self.repo_manager.check_if_repo_exists = mock_check_if_repo_exists
        
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "", ""),  # git fetch
            (0, "", ""),  # git checkout
            (0, "", "")   # git pull
        ]
        
        try:
            # Update a repository with a specific branch
            result = await self.repo_manager.update_repo("/path/to/repo", branch="develop")
            
            # Check that the update was successful
            self.assertTrue(result)
            
            # Check that the execute_command method was called with the correct arguments
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git fetch")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git checkout develop")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git pull")
        finally:
            # Restore original method
            self.repo_manager.check_if_repo_exists = original_check_if_repo_exists
    
    def test_update_repo_with_branch(self):
        """Test updating a Git repository with a specific branch (synchronous wrapper)."""
        asyncio.run(self.async_test_update_repo_with_branch())
    
    async def async_test_get_repo_status(self):
        """Test getting the status of a Git repository."""
        # Mock the check_if_repo_exists method
        original_check_if_repo_exists = self.repo_manager.check_if_repo_exists
        
        async def mock_check_if_repo_exists(repo_dir):
            return True
        
        self.repo_manager.check_if_repo_exists = mock_check_if_repo_exists
        
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "main", ""),                                # git branch --show-current
            (0, "abcdef1234567890", ""),                    # git rev-parse HEAD
            (0, "https://github.com/user/repo.git", ""),    # git config --get remote.origin.url
            (0, "M file1.txt\n?? file2.txt", ""),           # git status --porcelain
            (0, "abcdef commit message", "")                # git log origin/main..HEAD --oneline
        ]
        
        try:
            # Get repository status
            status = await self.repo_manager.get_repo_status("/path/to/repo")
            
            # Check that the status was retrieved correctly
            self.assertEqual(status["branch"], "main")
            self.assertEqual(status["commit"], "abcdef1234567890")
            self.assertEqual(status["remote_url"], "https://github.com/user/repo.git")
            self.assertTrue(status["has_changes"])
            self.assertTrue(status["has_unpushed_commits"])
            
            # Check that the execute_command method was called with the correct arguments
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git branch --show-current")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git rev-parse HEAD")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git config --get remote.origin.url")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git status --porcelain")
            self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git log origin/main..HEAD --oneline")
        finally:
            # Restore original method
            self.repo_manager.check_if_repo_exists = original_check_if_repo_exists
    
    def test_get_repo_status(self):
        """Test getting the status of a Git repository (synchronous wrapper)."""
        asyncio.run(self.async_test_get_repo_status())
    
    async def async_test_check_if_repo_exists(self):
        """Test checking if a directory is a Git repository."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "true", ""),   # Valid repository
            (1, "", "")        # Invalid repository
        ]
        
        # Check if a directory is a Git repository
        result = await self.repo_manager.check_if_repo_exists("/path/to/repo")
        
        # Check that the result is correct
        self.assertTrue(result)
        
        # Check if a directory is not a Git repository
        result = await self.repo_manager.check_if_repo_exists("/path/to/not_repo")
        
        # Check that the result is correct
        self.assertFalse(result)
        
        # Check that the execute_command method was called with the correct arguments
        self.connection.execute_command.assert_any_call("cd '/path/to/repo' && git rev-parse --is-inside-work-tree")
        self.connection.execute_command.assert_any_call("cd '/path/to/not_repo' && git rev-parse --is-inside-work-tree")
    
    def test_check_if_repo_exists(self):
        """Test checking if a directory is a Git repository (synchronous wrapper)."""
        asyncio.run(self.async_test_check_if_repo_exists())


class TestRepoManagerFactory(unittest.TestCase):
    """Test cases for the RepoManagerFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
    
    async def async_test_create_git_repo_manager(self):
        """Test creating a Git repository manager."""
        # Create a Git repository manager
        repo_manager = await RepoManagerFactory.create_repo_manager(self.connection, "git")
        
        # Check that the correct type of repository manager was created
        self.assertIsInstance(repo_manager, GitRepoManager)
    
    def test_create_git_repo_manager(self):
        """Test creating a Git repository manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_git_repo_manager())
    
    async def async_test_create_mercurial_repo_manager(self):
        """Test creating a Mercurial repository manager."""
        # Create a Mercurial repository manager
        repo_manager = await RepoManagerFactory.create_repo_manager(self.connection, "hg")
        
        # Check that the correct type of repository manager was created
        self.assertIsInstance(repo_manager, MercurialRepoManager)
        
        # Create a Mercurial repository manager using the full name
        repo_manager = await RepoManagerFactory.create_repo_manager(self.connection, "mercurial")
        
        # Check that the correct type of repository manager was created
        self.assertIsInstance(repo_manager, MercurialRepoManager)
    
    def test_create_mercurial_repo_manager(self):
        """Test creating a Mercurial repository manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_mercurial_repo_manager())
    
    async def async_test_create_svn_repo_manager(self):
        """Test creating an SVN repository manager."""
        # Create an SVN repository manager
        repo_manager = await RepoManagerFactory.create_repo_manager(self.connection, "svn")
        
        # Check that the correct type of repository manager was created
        self.assertIsInstance(repo_manager, SVNRepoManager)
    
    def test_create_svn_repo_manager(self):
        """Test creating an SVN repository manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_svn_repo_manager())
    
    async def async_test_create_invalid_repo_manager(self):
        """Test creating an invalid repository manager."""
        # Try to create an invalid repository manager
        with self.assertRaises(ValueError):
            await RepoManagerFactory.create_repo_manager(self.connection, "invalid")
    
    def test_create_invalid_repo_manager(self):
        """Test creating an invalid repository manager (synchronous wrapper)."""
        asyncio.run(self.async_test_create_invalid_repo_manager())
    
    async def async_test_detect_repo_type(self):
        """Test auto-detecting a repository type."""
        # Mock the connection's execute_command method
        self.connection.execute_command.side_effect = [
            (0, "true", ""),  # git rev-parse
        ]
        
        # Auto-detect a repository type
        repo_manager = await RepoManagerFactory.create_repo_manager(
            self.connection, repo_dir="/path/to/repo"
        )
        
        # Check that the correct type of repository manager was detected
        self.assertIsInstance(repo_manager, GitRepoManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # git rev-parse
            (0, "/path/to/repo", ""),  # hg root
        ]
        
        # Auto-detect a repository type
        repo_manager = await RepoManagerFactory.create_repo_manager(
            self.connection, repo_dir="/path/to/repo"
        )
        
        # Check that the correct type of repository manager was detected
        self.assertIsInstance(repo_manager, MercurialRepoManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # git rev-parse
            (1, "", ""),  # hg root
            (0, "Repository info", ""),  # svn info
        ]
        
        # Auto-detect a repository type
        repo_manager = await RepoManagerFactory.create_repo_manager(
            self.connection, repo_dir="/path/to/repo"
        )
        
        # Check that the correct type of repository manager was detected
        self.assertIsInstance(repo_manager, SVNRepoManager)
        
        # Reset the mock
        self.connection.execute_command.reset_mock()
        self.connection.execute_command.side_effect = [
            (1, "", ""),  # git rev-parse
            (1, "", ""),  # hg root
            (1, "", ""),  # svn info
        ]
        
        # Try to auto-detect a repository type when none are available
        with self.assertRaises(ValueError):
            await RepoManagerFactory.create_repo_manager(
                self.connection, repo_dir="/path/to/repo"
            )
    
    def test_detect_repo_type(self):
        """Test auto-detecting a repository type (synchronous wrapper)."""
        asyncio.run(self.async_test_detect_repo_type())


if __name__ == '__main__':
    unittest.main()
