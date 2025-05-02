#!/usr/bin/env python3
"""
Unit tests for the file synchronization module.
"""

import os
import sys
import unittest
import asyncio
import tempfile
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.sync.file_sync import FileSync
from unitmcp.remote.connection import RemoteConnection

class TestFileSync(unittest.TestCase):
    """Test cases for the FileSync class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection = AsyncMock(spec=RemoteConnection)
        self.file_sync = FileSync(self.connection)
        
        # Create temporary files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.local_dir = self.temp_dir.name
        self.remote_dir = "/remote/dir"
        
        # Create a local file for testing
        self.local_file = os.path.join(self.local_dir, "test_file.txt")
        with open(self.local_file, "w") as f:
            f.write("Test file content")
        
        self.remote_file = "/remote/dir/test_file.txt"
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
    
    async def async_test_upload_file(self):
        """Test uploading a file to a remote device."""
        # Mock the connection's upload_file method
        self.connection.upload_file.return_value = True
        
        # Upload the file
        result = await self.file_sync.upload_file(self.local_file, self.remote_file)
        
        # Check that the upload was successful
        self.assertTrue(result)
        
        # Check that the upload_file method was called with the correct arguments
        self.connection.upload_file.assert_called_once_with(self.local_file, self.remote_file)
    
    def test_upload_file(self):
        """Test uploading a file to a remote device (synchronous wrapper)."""
        asyncio.run(self.async_test_upload_file())
    
    async def async_test_upload_file_nonexistent(self):
        """Test uploading a nonexistent file."""
        # Try to upload a nonexistent file
        result = await self.file_sync.upload_file("/nonexistent/file", self.remote_file)
        
        # Check that the upload failed
        self.assertFalse(result)
        
        # Check that the upload_file method was not called
        self.connection.upload_file.assert_not_called()
    
    def test_upload_file_nonexistent(self):
        """Test uploading a nonexistent file (synchronous wrapper)."""
        asyncio.run(self.async_test_upload_file_nonexistent())
    
    async def async_test_download_file(self):
        """Test downloading a file from a remote device."""
        # Mock the connection's download_file method
        self.connection.download_file.return_value = True
        
        # Download the file
        result = await self.file_sync.download_file(self.remote_file, self.local_file)
        
        # Check that the download was successful
        self.assertTrue(result)
        
        # Check that the download_file method was called with the correct arguments
        self.connection.download_file.assert_called_once_with(self.remote_file, self.local_file)
    
    def test_download_file(self):
        """Test downloading a file from a remote device (synchronous wrapper)."""
        asyncio.run(self.async_test_download_file())
    
    async def async_test_compare_files_identical(self):
        """Test comparing identical files."""
        # Create a temporary file with the same content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"Test file content")
        
        try:
            # Mock the connection's download_file method to "download" the temp file
            async def mock_download_file(remote_path, local_path):
                with open(temp_path, "rb") as src, open(local_path, "wb") as dst:
                    dst.write(src.read())
                return True
            
            self.connection.download_file.side_effect = mock_download_file
            
            # Compare the files
            result = await self.file_sync.compare_files(self.local_file, self.remote_file)
            
            # Check that the files are identical
            self.assertTrue(result)
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_compare_files_identical(self):
        """Test comparing identical files (synchronous wrapper)."""
        asyncio.run(self.async_test_compare_files_identical())
    
    async def async_test_compare_files_different(self):
        """Test comparing different files."""
        # Create a temporary file with different content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"Different content")
        
        try:
            # Mock the connection's download_file method to "download" the temp file
            async def mock_download_file(remote_path, local_path):
                with open(temp_path, "rb") as src, open(local_path, "wb") as dst:
                    dst.write(src.read())
                return True
            
            self.connection.download_file.side_effect = mock_download_file
            
            # Compare the files
            result = await self.file_sync.compare_files(self.local_file, self.remote_file)
            
            # Check that the files are different
            self.assertFalse(result)
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_compare_files_different(self):
        """Test comparing different files (synchronous wrapper)."""
        asyncio.run(self.async_test_compare_files_different())
    
    async def async_test_compare_files_nonexistent(self):
        """Test comparing a nonexistent local file."""
        # Try to compare a nonexistent file
        result = await self.file_sync.compare_files("/nonexistent/file", self.remote_file)
        
        # Check that the comparison failed
        self.assertFalse(result)
        
        # Check that the download_file method was not called
        self.connection.download_file.assert_not_called()
    
    def test_compare_files_nonexistent(self):
        """Test comparing a nonexistent local file (synchronous wrapper)."""
        asyncio.run(self.async_test_compare_files_nonexistent())
    
    async def async_test_sync_directory(self):
        """Test synchronizing a directory."""
        # Set up the file_sync object with a properly mocked connection
        self.connection = AsyncMock(spec=RemoteConnection)
        
        # Mock the connection's execute_command method to handle all calls
        self.connection.execute_command.return_value = (0, "exists", "")
        
        self.file_sync = FileSync(self.connection)
        
        # Mock the file_sync's _list_local_files method to avoid filesystem access
        def mock_list_local_files(local_dir, exclude=None):
            return [
                "file1.txt",
                "subdir/file2.txt"
            ]
        
        self.file_sync._list_local_files = mock_list_local_files
        
        # Mock the file_sync's _list_remote_files method
        async def mock_list_remote_files(remote_dir, exclude=None):
            return [
                "file1.txt",
                "subdir/file2.txt"
            ]
        
        self.file_sync._list_remote_files = mock_list_remote_files
        
        # Mock the file_sync's compare_files method
        compare_files_calls = []
        
        async def mock_compare_files(local_path, remote_path):
            compare_files_calls.append((local_path, remote_path))
            # Simulate that file1.txt is identical but file2.txt is different
            return os.path.basename(local_path) == "file1.txt"
        
        self.file_sync.compare_files = mock_compare_files
        
        # Mock the file_sync's upload_file method
        upload_file_calls = []
        
        async def mock_upload_file(local_path, remote_path):
            upload_file_calls.append((local_path, remote_path))
            return True
        
        self.file_sync.upload_file = mock_upload_file
        
        # Patch os.path.exists and os.path.isdir to avoid filesystem access
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                # Synchronize the directory
                result = await self.file_sync.sync_directory(self.local_dir, self.remote_dir)
                
                # Check that the synchronization was successful
                self.assertTrue(result)
                
                # Check that the compare_files method was called for both files
                self.assertEqual(len(compare_files_calls), 2)
                self.assertIn((os.path.join(self.local_dir, "file1.txt"), os.path.join(self.remote_dir, "file1.txt")), compare_files_calls)
                self.assertIn((os.path.join(self.local_dir, "subdir/file2.txt"), os.path.join(self.remote_dir, "subdir/file2.txt")), compare_files_calls)
                
                # Check that the upload_file method was called only for the different file
                self.assertEqual(len(upload_file_calls), 1)
                self.assertEqual(upload_file_calls[0], (os.path.join(self.local_dir, "subdir/file2.txt"), os.path.join(self.remote_dir, "subdir/file2.txt")))
    
    def test_sync_directory(self):
        """Test synchronizing a directory (synchronous wrapper)."""
        asyncio.run(self.async_test_sync_directory())
    
    async def async_test_sync_file(self):
        """Test synchronizing a single file."""
        # Mock the connection's execute_command method
        self.connection.execute_command.return_value = (0, "exists", "")  # Check if remote file exists
        
        # Mock the file_sync's compare_files method
        original_compare_files = self.file_sync.compare_files
        
        async def mock_compare_files(local_path, remote_path):
            # Simulate that the files are different
            return False
        
        self.file_sync.compare_files = mock_compare_files
        
        # Mock the file_sync's upload_file method
        original_upload_file = self.file_sync.upload_file
        
        async def mock_upload_file(local_path, remote_path):
            return True
        
        self.file_sync.upload_file = mock_upload_file
        
        try:
            # Synchronize the file
            result = await self.file_sync.sync_file(self.local_file, self.remote_file)
            
            # Check that the synchronization was successful
            self.assertTrue(result)
        finally:
            # Restore original methods
            self.file_sync.compare_files = original_compare_files
            self.file_sync.upload_file = original_upload_file
    
    def test_sync_file(self):
        """Test synchronizing a single file (synchronous wrapper)."""
        asyncio.run(self.async_test_sync_file())
    
    def test_calculate_file_hash(self):
        """Test calculating a file hash."""
        # Calculate the hash of the test file
        hash_value = self.file_sync._calculate_file_hash(self.local_file)
        
        # Calculate the expected hash
        expected_hash = hashlib.sha256(b"Test file content").hexdigest()
        
        # Check that the hash is correct
        self.assertEqual(hash_value, expected_hash)


if __name__ == '__main__':
    unittest.main()
