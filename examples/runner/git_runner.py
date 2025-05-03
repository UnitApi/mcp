#!/usr/bin/env python3
"""
UnitMCP Git Runner

A specialized runner that can clone, configure, and run applications from Git repositories.
Supports various application types including shell scripts, Node.js, Python, PHP, and static HTML.
"""

import os
import sys
import asyncio
import argparse
import logging
import yaml
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

# Add parent directory to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, project_root)

# Import the base runner
from examples.runner.base_runner import BaseRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitRunner:
    """
    Git Runner for UnitMCP that can clone, configure, and run applications from Git repositories.
    
    This class provides functionality to:
    - Clone Git repositories
    - Detect application type (shell, Node.js, Python, PHP, static HTML)
    - Install dependencies
    - Configure environment variables
    - Run applications
    - Monitor logs and provide intelligent suggestions
    """
    
    # Application type detection patterns
    APP_TYPE_PATTERNS = {
        "nodejs": {
            "files": ["package.json", "yarn.lock", "npm-shrinkwrap.json"],
            "dirs": ["node_modules"],
            "extensions": [".js", ".ts", ".jsx", ".tsx"]
        },
        "python": {
            "files": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "dirs": ["venv", ".venv", "env", ".env"],
            "extensions": [".py"]
        },
        "php": {
            "files": ["composer.json", "composer.lock"],
            "dirs": ["vendor"],
            "extensions": [".php"]
        },
        "shell": {
            "files": [],
            "dirs": [],
            "extensions": [".sh", ".bash"]
        },
        "static_html": {
            "files": ["index.html"],
            "dirs": [],
            "extensions": [".html", ".htm"]
        }
    }
    
    # CI/CD configuration files
    CI_CONFIG_PATTERNS = {
        "github": ["/.github/workflows/", ".github/actions/"],
        "gitlab": [".gitlab-ci.yml"],
        "jenkins": ["Jenkinsfile"],
        "travis": [".travis.yml"],
        "circle": [".circleci/config.yml"]
    }
    
    def __init__(self, git_url: str, target_dir: Optional[str] = None, 
                 branch: Optional[str] = None, interactive: bool = True,
                 auto_start: bool = True, log_level: str = "INFO"):
        """
        Initialize the Git Runner.
        
        Parameters
        ----------
        git_url : str
            URL of the Git repository to clone
        target_dir : Optional[str]
            Directory to clone the repository into (default: temporary directory)
        branch : Optional[str]
            Branch to checkout (default: default branch)
        interactive : bool
            Whether to prompt for user input when needed (default: True)
        auto_start : bool
            Whether to automatically start the application after setup (default: True)
        log_level : str
            Logging level (default: INFO)
        """
        self.git_url = git_url
        self.branch = branch
        self.interactive = interactive
        self.auto_start = auto_start
        
        # Set up logging
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logging.getLogger().setLevel(numeric_level)
        
        # Set target directory
        if target_dir:
            self.target_dir = os.path.abspath(target_dir)
        else:
            # Create a temporary directory
            self.temp_dir = tempfile.TemporaryDirectory()
            self.target_dir = self.temp_dir.name
        
        # Initialize state variables
        self.app_type = None
        self.app_config = {}
        self.env_vars = {}
        self.processes = []
        self.log_files = []
        self.ci_system = None
    
    def __del__(self):
        """Clean up resources."""
        # Stop any running processes
        self.stop_all_processes()
        
        # Clean up temporary directory if used
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
    
    async def run(self) -> int:
        """
        Run the Git Runner workflow.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Clone the repository
            if not await self.clone_repository():
                return 1
            
            # Detect application type
            self.app_type = self.detect_app_type()
            if not self.app_type:
                logger.error("Could not detect application type")
                return 1
            
            logger.info(f"Detected application type: {self.app_type}")
            
            # Detect CI/CD system
            self.ci_system = self.detect_ci_system()
            if self.ci_system:
                logger.info(f"Detected CI/CD system: {self.ci_system}")
            
            # Load environment variables
            if not await self.load_env_vars():
                return 1
            
            # Install dependencies
            if not await self.install_dependencies():
                return 1
            
            # Start the application
            if self.auto_start:
                if not await self.start_application():
                    return 1
                
                # Monitor logs
                await self.monitor_logs()
            
            return 0
        
        except Exception as e:
            logger.exception(f"Error running Git Runner: {e}")
            return 1
    
    async def clone_repository(self) -> bool:
        """
        Clone the Git repository.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            logger.info(f"Cloning repository {self.git_url} to {self.target_dir}...")
            
            # Check if git is installed
            try:
                subprocess.run(["git", "--version"], check=True, capture_output=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("Git is not installed or not in PATH")
                return False
            
            # Prepare clone command
            cmd = ["git", "clone"]
            if self.branch:
                cmd.extend(["--branch", self.branch])
            
            # Add depth 1 for faster cloning if not a specific branch
            if not self.branch:
                cmd.extend(["--depth", "1"])
            
            cmd.extend([self.git_url, self.target_dir])
            
            # Execute clone command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to clone repository: {stderr.decode()}")
                return False
            
            logger.info(f"Repository cloned successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False
    
    def detect_app_type(self) -> Optional[str]:
        """
        Detect the type of application in the repository.
        
        Returns
        -------
        Optional[str]
            Application type or None if not detected
        """
        try:
            # Check if the directory exists
            if not os.path.isdir(self.target_dir):
                logger.error(f"Target directory {self.target_dir} does not exist")
                return None
            
            # Get all files in the repository
            all_files = []
            for root, dirs, files in os.walk(self.target_dir):
                # Skip hidden directories like .git
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            # Convert to relative paths
            rel_files = [os.path.relpath(f, self.target_dir) for f in all_files]
            
            # Check for each application type
            scores = {app_type: 0 for app_type in self.APP_TYPE_PATTERNS.keys()}
            
            for app_type, patterns in self.APP_TYPE_PATTERNS.items():
                # Check for specific files
                for file_pattern in patterns["files"]:
                    for file in rel_files:
                        if file.endswith(file_pattern) or file == file_pattern:
                            scores[app_type] += 10
                
                # Check for specific directories
                for dir_pattern in patterns["dirs"]:
                    for root, dirs, _ in os.walk(self.target_dir):
                        if dir_pattern in dirs:
                            scores[app_type] += 5
                
                # Check for file extensions
                for ext in patterns["extensions"]:
                    for file in rel_files:
                        if file.endswith(ext):
                            scores[app_type] += 1
            
            # Get the application type with the highest score
            max_score = max(scores.values())
            if max_score > 0:
                # If there's a tie, prefer in this order: nodejs, python, php, shell, static_html
                priority_order = ["nodejs", "python", "php", "shell", "static_html"]
                for app_type in priority_order:
                    if scores[app_type] == max_score:
                        return app_type
            
            # If no clear winner, check for specific entry points
            if os.path.exists(os.path.join(self.target_dir, "index.html")):
                return "static_html"
            
            if any(f.endswith(".sh") for f in rel_files):
                return "shell"
            
            if any(f.endswith(".py") for f in rel_files):
                return "python"
            
            if any(f.endswith(".js") and not f.endswith(".min.js") for f in rel_files):
                return "nodejs"
            
            if any(f.endswith(".php") for f in rel_files):
                return "php"
            
            # If still no match, ask the user if in interactive mode
            if self.interactive:
                print("\nCould not automatically detect application type.")
                print("Please select the application type:")
                print("1. Node.js")
                print("2. Python")
                print("3. PHP")
                print("4. Shell script")
                print("5. Static HTML")
                
                while True:
                    try:
                        choice = input("Enter your choice (1-5): ")
                        if choice == "1":
                            return "nodejs"
                        elif choice == "2":
                            return "python"
                        elif choice == "3":
                            return "php"
                        elif choice == "4":
                            return "shell"
                        elif choice == "5":
                            return "static_html"
                        else:
                            print("Invalid choice. Please enter a number between 1 and 5.")
                    except KeyboardInterrupt:
                        print("\nOperation cancelled by user")
                        return None
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting application type: {e}")
            return None
    
    def detect_ci_system(self) -> Optional[str]:
        """
        Detect CI/CD system used in the repository.
        
        Returns
        -------
        Optional[str]
            CI/CD system name or None if not detected
        """
        try:
            for ci_system, patterns in self.CI_CONFIG_PATTERNS.items():
                for pattern in patterns:
                    if os.path.exists(os.path.join(self.target_dir, pattern)):
                        return ci_system
            
            return None
        
        except Exception as e:
            logger.error(f"Error detecting CI system: {e}")
            return None
    
    async def load_env_vars(self) -> bool:
        """
        Load environment variables from .env file or prompt user for input.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check for .env file
            env_file = os.path.join(self.target_dir, ".env")
            env_example_file = os.path.join(self.target_dir, ".env.example")
            
            # If .env file exists, load it
            if os.path.exists(env_file):
                logger.info(f"Loading environment variables from {env_file}")
                self.env_vars = self._parse_env_file(env_file)
                return True
            
            # If .env.example file exists and interactive mode is enabled, prompt user
            if os.path.exists(env_example_file) and self.interactive:
                logger.info(f"Found .env.example file. Prompting for environment variables.")
                example_vars = self._parse_env_file(env_example_file)
                
                print("\nPlease provide values for the following environment variables:")
                for key, value in example_vars.items():
                    prompt = f"{key} [{value}]: " if value else f"{key}: "
                    try:
                        user_value = input(prompt)
                        self.env_vars[key] = user_value if user_value else value
                    except KeyboardInterrupt:
                        print("\nOperation cancelled by user")
                        return False
                
                # Write to .env file
                with open(env_file, "w") as f:
                    for key, value in self.env_vars.items():
                        f.write(f"{key}={value}\n")
                
                logger.info(f"Environment variables saved to {env_file}")
                return True
            
            # If no .env files found, check for other configuration files
            config_files = [
                "config.json",
                "config.yaml",
                "config.yml",
                "config/config.json",
                "config/config.yaml",
                "config/config.yml"
            ]
            
            for config_file in config_files:
                full_path = os.path.join(self.target_dir, config_file)
                if os.path.exists(full_path):
                    logger.info(f"Found configuration file: {config_file}")
                    # We don't load these automatically, but we note their existence
                    break
            
            # No environment variables needed or found
            return True
        
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
            return False
    
    def _parse_env_file(self, file_path: str) -> Dict[str, str]:
        """
        Parse a .env file and return a dictionary of environment variables.
        
        Parameters
        ----------
        file_path : str
            Path to the .env file
            
        Returns
        -------
        Dict[str, str]
            Dictionary of environment variables
        """
        env_vars = {}
        
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Handle quotes and spaces in values
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value and value[0] == value[-1] and value[0] in ["'", "\""]:
                        value = value[1:-1]
                    
                    env_vars[key] = value
        
        return env_vars
    
    async def install_dependencies(self) -> bool:
        """
        Install dependencies based on the detected application type.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing dependencies for {self.app_type} application...")
            
            if self.app_type == "nodejs":
                return await self._install_nodejs_dependencies()
            elif self.app_type == "python":
                return await self._install_python_dependencies()
            elif self.app_type == "php":
                return await self._install_php_dependencies()
            elif self.app_type == "shell":
                return await self._install_shell_dependencies()
            elif self.app_type == "static_html":
                # No dependencies to install for static HTML
                return True
            else:
                logger.error(f"Unknown application type: {self.app_type}")
                return False
        
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    async def _install_nodejs_dependencies(self) -> bool:
        """
        Install Node.js dependencies.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check if package.json exists
            package_json_path = os.path.join(self.target_dir, "package.json")
            if not os.path.exists(package_json_path):
                logger.warning("No package.json found. Skipping dependency installation.")
                return True
            
            # Check if Node.js is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "node", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error("Node.js is not installed or not in PATH")
                    if self.interactive:
                        print("\nNode.js is required but not installed.")
                        install = input("Would you like to install Node.js now? (y/n): ")
                        if install.lower() == "y":
                            # Install Node.js using appropriate method for the OS
                            if sys.platform == "linux":
                                await self._run_command("curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -")
                                await self._run_command("sudo apt-get install -y nodejs")
                            elif sys.platform == "darwin":
                                await self._run_command("brew install node")
                            elif sys.platform == "win32":
                                await self._run_command("winget install -e --id OpenJS.NodeJS")
                            else:
                                logger.error(f"Unsupported platform: {sys.platform}")
                                return False
                        else:
                            return False
                    else:
                        return False
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("Node.js is not installed or not in PATH")
                return False
            
            # Determine package manager (npm, yarn, pnpm)
            package_manager = "npm"
            if os.path.exists(os.path.join(self.target_dir, "yarn.lock")):
                package_manager = "yarn"
            elif os.path.exists(os.path.join(self.target_dir, "pnpm-lock.yaml")):
                package_manager = "pnpm"
            
            # Install dependencies
            logger.info(f"Installing dependencies using {package_manager}...")
            
            if package_manager == "npm":
                return await self._run_command("npm install", cwd=self.target_dir)
            elif package_manager == "yarn":
                return await self._run_command("yarn install", cwd=self.target_dir)
            elif package_manager == "pnpm":
                return await self._run_command("pnpm install", cwd=self.target_dir)
            
            return True
        
        except Exception as e:
            logger.error(f"Error installing Node.js dependencies: {e}")
            return False
    
    async def _install_python_dependencies(self) -> bool:
        """
        Install Python dependencies.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check if Python is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "python", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error("Python is not installed or not in PATH")
                    return False
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("Python is not installed or not in PATH")
                return False
            
            # Check for different dependency files
            req_file = None
            if os.path.exists(os.path.join(self.target_dir, "requirements.txt")):
                req_file = "requirements.txt"
            elif os.path.exists(os.path.join(self.target_dir, "Pipfile")):
                req_file = "Pipfile"
            elif os.path.exists(os.path.join(self.target_dir, "pyproject.toml")):
                req_file = "pyproject.toml"
            elif os.path.exists(os.path.join(self.target_dir, "setup.py")):
                req_file = "setup.py"
            
            if not req_file:
                logger.warning("No Python dependency file found. Skipping dependency installation.")
                return True
            
            # Create virtual environment
            venv_dir = os.path.join(self.target_dir, "venv")
            logger.info(f"Creating virtual environment in {venv_dir}...")
            
            if not await self._run_command(f"python -m venv {venv_dir}", cwd=self.target_dir):
                logger.error("Failed to create virtual environment")
                return False
            
            # Determine activation command based on OS
            activate_cmd = ""
            pip_cmd = ""
            if sys.platform == "win32":
                activate_cmd = f"{venv_dir}\\Scripts\\activate"
                pip_cmd = f"{venv_dir}\\Scripts\\pip"
            else:
                activate_cmd = f"source {venv_dir}/bin/activate"
                pip_cmd = f"{venv_dir}/bin/pip"
            
            # Install dependencies based on the file type
            if req_file == "requirements.txt":
                return await self._run_command(f"{pip_cmd} install -r requirements.txt", cwd=self.target_dir)
            elif req_file == "Pipfile":
                # Check if pipenv is installed
                try:
                    process = await asyncio.create_subprocess_exec(
                        "pipenv", "--version",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    if process.returncode != 0:
                        logger.info("Installing pipenv...")
                        await self._run_command(f"{pip_cmd} install pipenv", cwd=self.target_dir)
                except (subprocess.SubprocessError, FileNotFoundError):
                    logger.info("Installing pipenv...")
                    await self._run_command(f"{pip_cmd} install pipenv", cwd=self.target_dir)
                
                return await self._run_command(f"{pip_cmd} install pipenv && pipenv install --deploy", cwd=self.target_dir)
            elif req_file == "pyproject.toml":
                # Check if poetry is installed
                try:
                    process = await asyncio.create_subprocess_exec(
                        "poetry", "--version",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    if process.returncode != 0:
                        logger.info("Installing poetry...")
                        await self._run_command(f"{pip_cmd} install poetry", cwd=self.target_dir)
                except (subprocess.SubprocessError, FileNotFoundError):
                    logger.info("Installing poetry...")
                    await self._run_command(f"{pip_cmd} install poetry", cwd=self.target_dir)
                
                return await self._run_command(f"{pip_cmd} install poetry && poetry install", cwd=self.target_dir)
            elif req_file == "setup.py":
                return await self._run_command(f"{pip_cmd} install -e .", cwd=self.target_dir)
            
            return True
        
        except Exception as e:
            logger.error(f"Error installing Python dependencies: {e}")
            return False
    
    async def _install_php_dependencies(self) -> bool:
        """
        Install PHP dependencies.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check if PHP is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "php", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error("PHP is not installed or not in PATH")
                    return False
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("PHP is not installed or not in PATH")
                return False
            
            # Check if composer.json exists
            composer_json_path = os.path.join(self.target_dir, "composer.json")
            if not os.path.exists(composer_json_path):
                logger.warning("No composer.json found. Skipping dependency installation.")
                return True
            
            # Check if Composer is installed
            try:
                process = await asyncio.create_subprocess_exec(
                    "composer", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error("Composer is not installed or not in PATH")
                    if self.interactive:
                        print("\nComposer is required but not installed.")
                        install = input("Would you like to install Composer now? (y/n): ")
                        if install.lower() == "y":
                            # Install Composer
                            if sys.platform == "linux" or sys.platform == "darwin":
                                await self._run_command("php -r \"copy('https://getcomposer.org/installer', 'composer-setup.php');\"", cwd=self.target_dir)
                                await self._run_command("php composer-setup.php", cwd=self.target_dir)
                                await self._run_command("php -r \"unlink('composer-setup.php');\"", cwd=self.target_dir)
                                await self._run_command("sudo mv composer.phar /usr/local/bin/composer", cwd=self.target_dir)
                            else:
                                logger.error(f"Unsupported platform for automatic Composer installation: {sys.platform}")
                                return False
                        else:
                            return False
                    else:
                        return False
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("Composer is not installed or not in PATH")
                return False
            
            # Install dependencies
            logger.info("Installing PHP dependencies using Composer...")
            return await self._run_command("composer install", cwd=self.target_dir)
        
        except Exception as e:
            logger.error(f"Error installing PHP dependencies: {e}")
            return False
    
    async def _install_shell_dependencies(self) -> bool:
        """
        Install shell script dependencies.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Look for install.sh or setup.sh
            install_script = None
            if os.path.exists(os.path.join(self.target_dir, "install.sh")):
                install_script = "install.sh"
            elif os.path.exists(os.path.join(self.target_dir, "setup.sh")):
                install_script = "setup.sh"
            
            if not install_script:
                logger.warning("No installation script found. Skipping dependency installation.")
                return True
            
            # Make the script executable
            script_path = os.path.join(self.target_dir, install_script)
            os.chmod(script_path, 0o755)
            
            # Run the installation script
            logger.info(f"Running installation script: {install_script}")
            return await self._run_command(f"./{install_script}", cwd=self.target_dir)
        
        except Exception as e:
            logger.error(f"Error installing shell dependencies: {e}")
            return False
    
    async def start_application(self) -> bool:
        """
        Start the application based on its type.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting {self.app_type} application...")
            
            if self.app_type == "nodejs":
                return await self._start_nodejs_application()
            elif self.app_type == "python":
                return await self._start_python_application()
            elif self.app_type == "php":
                return await self._start_php_application()
            elif self.app_type == "shell":
                return await self._start_shell_application()
            elif self.app_type == "static_html":
                return await self._start_static_html_application()
            else:
                logger.error(f"Unknown application type: {self.app_type}")
                return False
        
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            return False
    
    async def _start_nodejs_application(self) -> bool:
        """
        Start a Node.js application.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check package.json for start script
            package_json_path = os.path.join(self.target_dir, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                
                # Check for start script
                if "scripts" in package_data and "start" in package_data["scripts"]:
                    logger.info("Found start script in package.json")
                    return await self._run_command_async("npm start", cwd=self.target_dir, env=self.env_vars)
                
                # Check for dev script
                if "scripts" in package_data and "dev" in package_data["scripts"]:
                    logger.info("Found dev script in package.json")
                    return await self._run_command_async("npm run dev", cwd=self.target_dir, env=self.env_vars)
            
            # Check for common entry points
            entry_points = [
                "index.js",
                "server.js",
                "app.js",
                "main.js",
                "src/index.js",
                "src/server.js",
                "src/app.js",
                "src/main.js"
            ]
            
            for entry_point in entry_points:
                if os.path.exists(os.path.join(self.target_dir, entry_point)):
                    logger.info(f"Found entry point: {entry_point}")
                    return await self._run_command_async(f"node {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            logger.warning("No entry point found for Node.js application")
            
            if self.interactive:
                print("\nNo entry point found for Node.js application.")
                entry_point = input("Please specify the entry point (e.g., index.js): ")
                if entry_point:
                    return await self._run_command_async(f"node {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            return False
        except Exception as e:
            logger.error(f"Error starting Node.js application: {e}")
            return False
    
    async def _start_python_application(self) -> bool:
        """
        Start a Python application.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Determine Python executable
            python_cmd = "python"
            venv_dir = os.path.join(self.target_dir, "venv")
            if os.path.exists(venv_dir):
                if sys.platform == "win32":
                    python_cmd = f"{venv_dir}\\Scripts\\python"
                else:
                    python_cmd = f"{venv_dir}/bin/python"
            
            # Check for common entry points
            entry_points = [
                "app.py",
                "main.py",
                "run.py",
                "server.py",
                "start.py",
                "src/app.py",
                "src/main.py",
                "src/run.py",
                "src/server.py",
                "src/start.py"
            ]
            
            for entry_point in entry_points:
                if os.path.exists(os.path.join(self.target_dir, entry_point)):
                    logger.info(f"Found entry point: {entry_point}")
                    return await self._run_command_async(f"{python_cmd} {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            # Check for Flask applications
            if os.path.exists(os.path.join(self.target_dir, "wsgi.py")):
                logger.info("Found Flask application (wsgi.py)")
                return await self._run_command_async(f"{python_cmd} -m flask run", cwd=self.target_dir, env=self.env_vars)
            
            # Check for Django applications
            if os.path.exists(os.path.join(self.target_dir, "manage.py")):
                logger.info("Found Django application (manage.py)")
                return await self._run_command_async(f"{python_cmd} manage.py runserver", cwd=self.target_dir, env=self.env_vars)
            
            logger.warning("No entry point found for Python application")
            
            if self.interactive:
                print("\nNo entry point found for Python application.")
                entry_point = input("Please specify the entry point (e.g., app.py): ")
                if entry_point:
                    return await self._run_command_async(f"{python_cmd} {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            return False
        except Exception as e:
            logger.error(f"Error starting Python application: {e}")
            return False
    
    async def _start_php_application(self) -> bool:
        """
        Start a PHP application.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check for common PHP frameworks
            # Laravel
            if os.path.exists(os.path.join(self.target_dir, "artisan")):
                logger.info("Found Laravel application (artisan)")
                return await self._run_command_async("php artisan serve", cwd=self.target_dir, env=self.env_vars)
            
            # Symfony
            if os.path.exists(os.path.join(self.target_dir, "bin/console")):
                logger.info("Found Symfony application (bin/console)")
                return await self._run_command_async("php bin/console server:start", cwd=self.target_dir, env=self.env_vars)
            
            # Check for common entry points
            entry_points = [
                "index.php",
                "public/index.php",
                "web/index.php"
            ]
            
            for entry_point in entry_points:
                if os.path.exists(os.path.join(self.target_dir, entry_point)):
                    logger.info(f"Found entry point: {entry_point}")
                    # Start PHP built-in server
                    return await self._run_command_async(f"php -S localhost:8000 {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            logger.warning("No entry point found for PHP application")
            
            if self.interactive:
                print("\nNo entry point found for PHP application.")
                entry_point = input("Please specify the entry point (e.g., index.php): ")
                if entry_point:
                    return await self._run_command_async(f"php -S localhost:8000 {entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            return False
        except Exception as e:
            logger.error(f"Error starting PHP application: {e}")
            return False
    
    async def _start_shell_application(self) -> bool:
        """
        Start a shell script application.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check for common entry points
            entry_points = [
                "start.sh",
                "run.sh",
                "app.sh",
                "main.sh"
            ]
            
            for entry_point in entry_points:
                if os.path.exists(os.path.join(self.target_dir, entry_point)):
                    logger.info(f"Found entry point: {entry_point}")
                    # Make the script executable
                    script_path = os.path.join(self.target_dir, entry_point)
                    os.chmod(script_path, 0o755)
                    return await self._run_command_async(f"./{entry_point}", cwd=self.target_dir, env=self.env_vars)
            
            # Check for any shell script
            for root, _, files in os.walk(self.target_dir):
                for file in files:
                    if file.endswith(".sh"):
                        script_path = os.path.join(root, file)
                        rel_path = os.path.relpath(script_path, self.target_dir)
                        logger.info(f"Found shell script: {rel_path}")
                        
                        if self.interactive:
                            run_script = input(f"Run {rel_path}? (y/n): ")
                            if run_script.lower() != "y":
                                continue
                        
                        # Make the script executable
                        os.chmod(script_path, 0o755)
                        return await self._run_command_async(f"./{rel_path}", cwd=self.target_dir, env=self.env_vars)
            
            logger.warning("No shell script found")
            
            if self.interactive:
                print("\nNo shell script found.")
                entry_point = input("Please specify the shell script to run: ")
                if entry_point:
                    if os.path.exists(os.path.join(self.target_dir, entry_point)):
                        script_path = os.path.join(self.target_dir, entry_point)
                        os.chmod(script_path, 0o755)
                        return await self._run_command_async(f"./{entry_point}", cwd=self.target_dir, env=self.env_vars)
                    else:
                        logger.error(f"Script not found: {entry_point}")
            
            return False
        except Exception as e:
            logger.error(f"Error starting shell application: {e}")
            return False
    
    async def _start_static_html_application(self) -> bool:
        """
        Start a static HTML application.
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Check for index.html
            if os.path.exists(os.path.join(self.target_dir, "index.html")):
                logger.info("Found index.html")
                
                # Start a simple HTTP server
                if sys.platform == "win32":
                    return await self._run_command_async("python -m http.server 8000", cwd=self.target_dir, env=self.env_vars)
                else:
                    return await self._run_command_async("python3 -m http.server 8000", cwd=self.target_dir, env=self.env_vars)
            
            logger.warning("No index.html found")
            
            if self.interactive:
                print("\nNo index.html found.")
                html_file = input("Please specify the HTML file to serve: ")
                if html_file:
                    if os.path.exists(os.path.join(self.target_dir, html_file)):
                        if sys.platform == "win32":
                            return await self._run_command_async("python -m http.server 8000", cwd=self.target_dir, env=self.env_vars)
                        else:
                            return await self._run_command_async("python3 -m http.server 8000", cwd=self.target_dir, env=self.env_vars)
                    else:
                        logger.error(f"HTML file not found: {html_file}")
            
            return False
        except Exception as e:
            logger.error(f"Error starting static HTML application: {e}")
            return False
    
    async def _run_command(self, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> bool:
        """
        Run a command and wait for it to complete.
        
        Parameters
        ----------
        command : str
            Command to run
        cwd : Optional[str]
            Working directory
        env : Optional[Dict[str, str]]
            Environment variables
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            # Prepare environment variables
            full_env = os.environ.copy()
            if env:
                full_env.update(env)
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=full_env
            )
            
            # Capture output
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Command failed: {command}")
                logger.error(f"Error: {stderr.decode()}")
                return False
            
            logger.info(f"Command succeeded: {command}")
            return True
        
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return False
    
    async def _run_command_async(self, command: str, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> bool:
        """
        Run a command asynchronously and capture its output.
        
        Parameters
        ----------
        command : str
            Command to run
        cwd : Optional[str]
            Working directory
        env : Optional[Dict[str, str]]
            Environment variables
            
        Returns
        -------
        bool
            True if the command was started successfully, False otherwise
        """
        try:
            # Prepare environment variables
            full_env = os.environ.copy()
            if env:
                full_env.update(env)
            
            # Create log file
            log_file_path = os.path.join(self.target_dir, f"log_{int(time.time())}.txt")
            log_file = open(log_file_path, "w")
            self.log_files.append(log_file_path)
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=full_env
            )
            
            # Store the process
            self.processes.append(process)
            
            # Start tasks to read output
            asyncio.create_task(self._read_process_output(process, log_file))
            
            logger.info(f"Started command: {command}")
            logger.info(f"Logging to: {log_file_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting command: {e}")
            return False
    
    async def _read_process_output(self, process: asyncio.subprocess.Process, log_file) -> None:
        """
        Read and log process output.
        
        Parameters
        ----------
        process : asyncio.subprocess.Process
            Process to read output from
        log_file : file
            File to write output to
        """
        try:
            # Read stdout
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode().rstrip()
                print(f"[APP] {line_str}")
                log_file.write(f"{line_str}\n")
                log_file.flush()
            
            # Read stderr
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                
                line_str = line.decode().rstrip()
                print(f"[APP ERROR] {line_str}")
                log_file.write(f"ERROR: {line_str}\n")
                log_file.flush()
            
            # Wait for process to exit
            await process.wait()
            
            # Close log file
            log_file.close()
            
            # Remove process from list
            if process in self.processes:
                self.processes.remove(process)
        
        except Exception as e:
            logger.error(f"Error reading process output: {e}")
    
    def stop_all_processes(self) -> None:
        """Stop all running processes."""
        for process in self.processes:
            try:
                process.terminate()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
    
    async def monitor_logs(self) -> None:
        """Monitor logs and provide intelligent suggestions."""
        # Wait for logs to be generated
        await asyncio.sleep(2)
        
        # Check if any log files exist
        if not self.log_files:
            logger.warning("No log files found")
            return
        
        # Monitor the most recent log file
        log_file_path = self.log_files[-1]
        
        try:
            with open(log_file_path, "r") as f:
                log_content = f.read()
            
            # Check for common errors
            errors = self._analyze_logs(log_content)
            
            if errors:
                logger.warning("Found potential issues in the logs:")
                for error in errors:
                    logger.warning(f"- {error['message']}")
                    if error.get('suggestion'):
                        logger.info(f"  Suggestion: {error['suggestion']}")
        
        except Exception as e:
            logger.error(f"Error monitoring logs: {e}")
    
    def _analyze_logs(self, log_content: str) -> List[Dict[str, str]]:
        """
        Analyze logs for common errors and provide suggestions.
        
        Parameters
        ----------
        log_content : str
            Log content to analyze
            
        Returns
        -------
        List[Dict[str, str]]
            List of errors with messages and suggestions
        """
        errors = []
        
        # Check for common errors based on application type
        if self.app_type == "nodejs":
            # Check for missing dependencies
            if "Cannot find module" in log_content:
                module_match = re.search(r"Cannot find module '([^']+)'", log_content)
                if module_match:
                    module_name = module_match.group(1)
                    errors.append({
                        "message": f"Missing Node.js module: {module_name}",
                        "suggestion": f"Run 'npm install {module_name}' to install the missing dependency."
                    })
            
            # Check for port already in use
            if "EADDRINUSE" in log_content:
                port_match = re.search(r"EADDRINUSE.*:(\d+)", log_content)
                if port_match:
                    port = port_match.group(1)
                    errors.append({
                        "message": f"Port {port} is already in use",
                        "suggestion": f"Change the port in your application or stop the process using port {port}."
                    })
        
        elif self.app_type == "python":
            # Check for missing dependencies
            if "ModuleNotFoundError" in log_content or "ImportError" in log_content:
                module_match = re.search(r"No module named '([^']+)'", log_content)
                if module_match:
                    module_name = module_match.group(1)
                    errors.append({
                        "message": f"Missing Python module: {module_name}",
                        "suggestion": f"Run 'pip install {module_name}' to install the missing dependency."
                    })
            
            # Check for port already in use
            if "Address already in use" in log_content:
                port_match = re.search(r"Address already in use.*:(\d+)", log_content)
                if port_match:
                    port = port_match.group(1)
                    errors.append({
                        "message": f"Port {port} is already in use",
                        "suggestion": f"Change the port in your application or stop the process using port {port}."
                    })
        
        elif self.app_type == "php":
            # Check for missing dependencies
            if "Class 'PDO' not found" in log_content:
                errors.append({
                    "message": "Missing PHP PDO extension",
                    "suggestion": "Install the PHP PDO extension for your database."
                })
            
            # Check for port already in use
            if "Address already in use" in log_content:
                errors.append({
                    "message": "Port is already in use",
                    "suggestion": "Change the port in your application or stop the process using that port."
                })
        
        # Generic errors
        
        # Check for permission issues
        if "Permission denied" in log_content:
            errors.append({
                "message": "Permission denied error",
                "suggestion": "Check file and directory permissions. You may need to run with sudo or as administrator."
            })
        
        # Check for file not found
        if "No such file or directory" in log_content or "ENOENT" in log_content:
            file_match = re.search(r"No such file or directory: '([^']+)'", log_content)
            if file_match:
                file_path = file_match.group(1)
                errors.append({
                    "message": f"File not found: {file_path}",
                    "suggestion": f"Check if the file exists and the path is correct."
                })
        
        # Check for database connection issues
        if "SQLSTATE" in log_content or "database connection" in log_content.lower():
            errors.append({
                "message": "Database connection error",
                "suggestion": "Check your database credentials and make sure the database server is running."
            })
        
        return errors


class GitRunnerCLI:
    """Command-line interface for the Git Runner."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.parser = argparse.ArgumentParser(
            description="UnitMCP Git Runner - Clone, configure, and run applications from Git repositories"
        )
        
        self.parser.add_argument(
            "git_url",
            help="URL of the Git repository to clone"
        )
        
        self.parser.add_argument(
            "--target-dir", "-d",
            help="Directory to clone the repository into (default: temporary directory)"
        )
        
        self.parser.add_argument(
            "--branch", "-b",
            help="Branch to checkout (default: default branch)"
        )
        
        self.parser.add_argument(
            "--non-interactive", "-n",
            action="store_true",
            help="Run in non-interactive mode (don't prompt for input)"
        )
        
        self.parser.add_argument(
            "--no-auto-start", "-s",
            action="store_true",
            help="Don't automatically start the application after setup"
        )
        
        self.parser.add_argument(
            "--log-level", "-l",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Logging level (default: INFO)"
        )
    
    async def run(self) -> int:
        """
        Run the CLI.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        args = self.parser.parse_args()
        
        runner = GitRunner(
            git_url=args.git_url,
            target_dir=args.target_dir,
            branch=args.branch,
            interactive=not args.non_interactive,
            auto_start=not args.no_auto_start,
            log_level=args.log_level
        )
        
        return await runner.run()


async def main() -> int:
    """
    Main entry point.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    cli = GitRunnerCLI()
    return await cli.run()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
