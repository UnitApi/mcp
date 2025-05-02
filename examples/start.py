#!/usr/bin/env python3
import os
import sys
import subprocess
import importlib
import yaml
from pathlib import Path

def clean_directories():
    """Remove all files from correct and error directories and temporary wrapper files."""
    import shutil
    # Clean output directories
    for directory in ['correct', 'error']:
        if os.path.exists(directory):
            shutil.rmtree(directory)

def setup_directories():
    """Create and clean correct and error directories."""
    clean_directories()
    Path('correct').mkdir(exist_ok=True)
    Path('error').mkdir(exist_ok=True)

def check_unitmcp_installed():
    """Check if unitmcp package is installed."""
    try:
        import unitmcp
        return True
    except ImportError:
        return False

def install_unitmcp():
    """Install unitmcp package in development mode."""
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-e', '.'],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install unitmcp: {e.stderr}")
        return False

def find_python_files(directory):
    """Recursively find all .py files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    return python_files

def run_example(python_file):
    """Run a Python file and capture its output."""
    try:
        # Prepare command and arguments
        cmd = [sys.executable, python_file]
        
        # Add specific arguments for certain examples
        base_name = os.path.basename(python_file)
        if base_name == "microphone_recording.py":
            cmd.extend(["--output", "recording.wav"])
        elif base_name == "face_detection.py":
            # Create a temporary pipeline config file
            config = {
                "input": {
                    "source": "0",
                    "resolution": "1280x720",
                    "fps": 30
                },
                "processing": [{
                    "type": "face_detection",
                    "confidence": 0.5
                }],
                "output": [{
                    "type": "rtsp",
                    "port": 8554
                }]
            }
            config_path = "pipeline_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            cmd.extend(["--config", config_path])
        elif base_name == "audio_processing.py":
            # Create a temporary audio config file
            config = {
                "input": {
                    "device": "0",
                    "rate": 44100,
                    "channels": 2
                },
                "filters": [{
                    "name": "noise_reduction",
                    "strength": 0.5
                }, {
                    "name": "equalizer",
                    "bands": [0.8, 1.0, 1.2]
                }],
                "analysis": [{
                    "type": "feature_extraction",
                    "window": 1024
                }, {
                    "type": "classification",
                    "model": "default"
                }]
            }
            config_path = "audio_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            cmd.extend(["--config", config_path])
        elif base_name == "https_server.py":
            # Create a temporary server config file
            config = {
                "server": {
                    "host": "localhost",
                    "port": 8443,
                    "ssl": {
                        "cert": "cert.pem",
                        "key": "key.pem"
                    },
                    "cors": {
                        "origins": ["*"],
                        "methods": ["*"]
                    }
                },
                "auth": {
                    "secret": "your-secret-key"
                }
            }
            config_path = "server_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            cmd.extend(["--config", config_path])
        
        # Run the Python file and capture output/errors
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Set timeout to 30 seconds
        )
        
        # Get the base filename without path
        base_name = os.path.basename(python_file)
        
        if result.returncode == 0:
            # Success case - write to correct/
            output_file = os.path.join('correct', f"{base_name}.log")
            output_content = f"=== Successfully ran {base_name} ===\n\nSTDOUT:\n{result.stdout}\n"
            if result.stderr:
                output_content += f"\nSTDERR:\n{result.stderr}"
        else:
            # Error case - write to error/
            output_file = os.path.join('error', f"{base_name}.log")
            output_content = f"=== Error running {base_name} ===\n\nExit code: {result.returncode}\n"
            if result.stdout:
                output_content += f"\nSTDOUT:\n{result.stdout}"
            output_content += f"\nSTDERR:\n{result.stderr}"
        
        # Write the output to appropriate file
        with open(output_file, 'w') as f:
            f.write(output_content)
            
        return result.returncode == 0
            
    except subprocess.TimeoutExpired:
        # Handle timeout case
        output_file = os.path.join('error', f"{os.path.basename(python_file)}.log")
        with open(output_file, 'w') as f:
            f.write(f"=== Timeout running {os.path.basename(python_file)} ===\nExecution exceeded 30 seconds timeout.")
        return False
    except Exception as e:
        # Handle any other exceptions
        output_file = os.path.join('error', f"{os.path.basename(python_file)}.log")
        with open(output_file, 'w') as f:
            f.write(f"=== Error running {os.path.basename(python_file)} ===\nException: {str(e)}")
        return False

def main():
    # Setup output directories
    setup_directories()
    
    # Check if unitmcp is installed
    if not check_unitmcp_installed():
        print("unitmcp package not found. Installing in development mode...")
        if not install_unitmcp():
            print("Failed to install unitmcp package. Examples may not work correctly.")
    
    # Find all Python files in examples directory
    python_files = find_python_files('examples')
    
    # Statistics
    total = len(python_files)
    successful = 0
    failed = 0
    
    print(f"Found {total} Python files to run\n")
    print("Note: Some examples may require additional services to be running (e.g. web server, MQTT broker)")
    print("      Check the error logs for specific requirements.\n")
    
    # Run each example
    for python_file in python_files:
        print(f"Running {python_file}...", end=' ')
        if run_example(python_file):
            print("SUCCESS")
            successful += 1
        else:
            print("FAILED")
            failed += 1
    
    # Print summary
    print(f"\nExecution complete!")
    print(f"Total files: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"\nCheck 'correct/' and 'error/' directories for detailed logs.")
    
    if failed > 0:
        print("\nNote: Failures may be due to:")
        print("1. Missing dependencies")
        print("2. Required services not running (web server, MQTT broker, etc.)")
        print("3. Hardware requirements (camera, microphone, etc.)")
        print("4. Configuration files not set up")
        print("\nCheck the error logs for specific details about each failure.")

if __name__ == '__main__':
    main()
