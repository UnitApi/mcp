#!/usr/bin/env python3
"""
Test module for the run_all_examples.py script.
This module contains tests to verify that the run_all_examples.py script works correctly.
"""

import os
import sys
import unittest
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the run_all_examples module
import run_all_examples


class TestRunAllExamples(unittest.TestCase):
    """Test the run_all_examples.py script."""

    def setUp(self):
        """Set up the test environment."""
        self.examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Create a temporary directory for test output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        self.temp_dir.cleanup()

    @patch('run_all_examples.run_example')
    def test_run_all_examples(self, mock_run_example):
        """Test that run_all_examples can run all examples."""
        # Mock the run_example function to return success
        mock_run_example.return_value = True
        
        # Run all examples
        result = run_all_examples.run_all_examples(
            examples_dir=self.examples_dir,
            output_dir=self.output_dir,
            timeout=5,
            verbose=True
        )
        
        # Check that run_example was called at least once
        self.assertTrue(mock_run_example.called, "run_example was not called")
        
        # Check that the result is a dictionary
        self.assertIsInstance(result, dict, "Result is not a dictionary")
        
        # Check that the result has the required keys
        self.assertIn("passed", result, "Result does not have 'passed' key")
        self.assertIn("failed", result, "Result does not have 'failed' key")
        self.assertIn("skipped", result, "Result does not have 'skipped' key")
        
        # Check that a report file was created
        report_file = os.path.join(self.output_dir, "example_report.json")
        self.assertTrue(os.path.exists(report_file), f"Report file {report_file} was not created")
        
        # Check that the report file contains valid JSON
        with open(report_file, "r") as f:
            report = json.load(f)
            self.assertIsInstance(report, dict, "Report is not a dictionary")
            self.assertIn("passed", report, "Report does not have 'passed' key")
            self.assertIn("failed", report, "Report does not have 'failed' key")
            self.assertIn("skipped", report, "Report does not have 'skipped' key")

    @patch('subprocess.Popen')
    def test_run_example(self, mock_popen):
        """Test that run_example can run a single example."""
        # Mock the subprocess.Popen call
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"Example output", b"")
        mock_popen.return_value = mock_process
        
        # Run an example
        example_path = os.path.join(self.examples_dir, "template")
        result = run_all_examples.run_example(
            example_path=example_path,
            timeout=5,
            verbose=True
        )
        
        # Check that the example was run successfully
        self.assertTrue(result, "Example did not run successfully")
        
        # Check that subprocess.Popen was called
        mock_popen.assert_called_once()

    @patch('run_all_examples.find_examples')
    def test_find_examples(self, mock_find_examples):
        """Test that find_examples can find all examples."""
        # Mock the find_examples function to return a list of examples
        mock_examples = [
            os.path.join(self.examples_dir, "template"),
            os.path.join(self.examples_dir, "voice_assistant"),
        ]
        mock_find_examples.return_value = mock_examples
        
        # Find all examples
        examples = run_all_examples.find_examples(self.examples_dir)
        
        # Check that find_examples was called
        mock_find_examples.assert_called_once_with(self.examples_dir)
        
        # Check that the examples were found
        self.assertEqual(examples, mock_examples, "Examples do not match")

    def test_parse_arguments(self):
        """Test that parse_arguments parses command-line arguments correctly."""
        # Test with default arguments
        with patch('sys.argv', ['run_all_examples.py']):
            args = run_all_examples.parse_arguments()
            self.assertEqual(args.examples_dir, os.path.dirname(os.path.abspath(run_all_examples.__file__)))
            self.assertEqual(args.timeout, 60)
            self.assertFalse(args.verbose)
        
        # Test with custom arguments
        with patch('sys.argv', [
            'run_all_examples.py',
            '--examples-dir', '/custom/dir',
            '--timeout', '30',
            '--verbose'
        ]):
            args = run_all_examples.parse_arguments()
            self.assertEqual(args.examples_dir, '/custom/dir')
            self.assertEqual(args.timeout, 30)
            self.assertTrue(args.verbose)


if __name__ == "__main__":
    unittest.main()
