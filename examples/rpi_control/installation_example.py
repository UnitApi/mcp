#!/usr/bin/env python3
"""
Installation and Setup Example for UnitMCP

This example demonstrates how to:
1. Detect the platform (Raspberry Pi, desktop, etc.)
2. Install required dependencies
3. Configure the system for UnitMCP operation
4. Set up necessary services
5. Perform a basic self-test to verify functionality

This script helps users get started with the UnitMCP system.
"""

import os
import sys
import platform
import subprocess
import argparse
import json
import logging
import shutil
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("unitmcp_install.log")
    ]
)
logger = logging.getLogger("UnitMCP-Install")


class PlatformInfo:
    """Class to detect and store platform information."""
    
    def __init__(self):
        """Initialize and detect platform information."""
        self.system = platform.system()
        self.machine = platform.machine()
        self.distribution = self._get_distribution()
        self.is_raspberry_pi = self._is_raspberry_pi()
        
    def _get_distribution(self) -> str:
        """Get the Linux distribution name if applicable."""
        if self.system != "Linux":
            return "Unknown"
            
        # Try to get distribution info
        try:
            # Try /etc/os-release first
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("ID="):
                            return line.split("=")[1].strip().strip('"')
            
            # Fall back to platform module
            return platform.linux_distribution()[0]
        except:
            return "Unknown Linux"
            
    def _is_raspberry_pi(self) -> bool:
        """Detect if running on a Raspberry Pi."""
        # Check machine type
        if self.machine not in ["armv7l", "aarch64"]:
            return False
            
        # Check for Raspberry Pi model file
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", "r") as f:
                model = f.read()
                if "Raspberry Pi" in model:
                    return True
                    
        return False
        
    def get_summary(self) -> Dict[str, str]:
        """Get a summary of platform information."""
        return {
            "system": self.system,
            "machine": self.machine,
            "distribution": self.distribution,
            "is_raspberry_pi": self.is_raspberry_pi
        }


class DependencyManager:
    """Class to manage system dependencies."""
    
    def __init__(self, platform_info: PlatformInfo):
        """Initialize the dependency manager.
        
        Args:
            platform_info: Platform information
        """
        self.platform_info = platform_info
        
    def get_package_manager(self) -> Tuple[str, List[str]]:
        """Get the appropriate package manager command for the platform."""
        if self.platform_info.system == "Linux":
            if self.platform_info.distribution in ["debian", "ubuntu", "raspbian"]:
                return "apt-get", ["apt-get", "install", "-y"]
            elif self.platform_info.distribution in ["fedora", "centos", "rhel"]:
                return "dnf", ["dnf", "install", "-y"]
            else:
                logger.warning(f"Unknown Linux distribution: {self.platform_info.distribution}")
                return "apt-get", ["apt-get", "install", "-y"]
        elif self.platform_info.system == "Darwin":  # macOS
            return "brew", ["brew", "install"]
        else:
            logger.warning(f"Unsupported system: {self.platform_info.system}")
            return "unknown", []
            
    def check_package_manager(self) -> bool:
        """Check if the package manager is available."""
        pkg_mgr, _ = self.get_package_manager()
        if pkg_mgr == "unknown":
            return False
            
        try:
            if pkg_mgr == "apt-get":
                subprocess.run(["apt-get", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif pkg_mgr == "dnf":
                subprocess.run(["dnf", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif pkg_mgr == "brew":
                subprocess.run(["brew", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                return False
            return True
        except:
            return False
            
    def get_required_packages(self) -> List[str]:
        """Get the list of required system packages."""
        common_packages = ["python3", "python3-pip", "git"]
        
        if self.platform_info.is_raspberry_pi:
            # Raspberry Pi specific packages
            rpi_packages = [
                "python3-rpi.gpio",
                "python3-smbus",
                "i2c-tools",
                "python3-pigpio",
                "pigpio",
                "python3-gpiozero"
            ]
            return common_packages + rpi_packages
        else:
            # Desktop packages
            desktop_packages = []
            return common_packages + desktop_packages
            
    def get_python_packages(self) -> List[str]:
        """Get the list of required Python packages."""
        common_packages = [
            "pyaudio",
            "numpy",
            "sounddevice",
            "pyttsx3",
            "speech_recognition",
            "gpiozero",
            "RPi.GPIO",
            "smbus2",
            "pigpio"
        ]
        
        return common_packages
        
    def install_system_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install system packages.
        
        Args:
            packages: List of packages to install
            dry_run: If True, only print commands without executing
            
        Returns:
            True if successful, False otherwise
        """
        if not packages:
            logger.info("No system packages to install")
            return True
            
        pkg_mgr_name, pkg_mgr_cmd = self.get_package_manager()
        if pkg_mgr_name == "unknown":
            logger.error("No supported package manager found")
            return False
            
        cmd = pkg_mgr_cmd + packages
        
        logger.info(f"Installing system packages: {', '.join(packages)}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        if dry_run:
            logger.info("Dry run - not executing command")
            return True
            
        try:
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode != 0:
                logger.error(f"Failed to install packages: {process.stderr.decode()}")
                return False
            logger.info("System packages installed successfully")
            return True
        except Exception as e:
            logger.error(f"Error installing system packages: {e}")
            return False
            
    def install_python_packages(self, packages: List[str], dry_run: bool = False) -> bool:
        """Install Python packages.
        
        Args:
            packages: List of packages to install
            dry_run: If True, only print commands without executing
            
        Returns:
            True if successful, False otherwise
        """
        if not packages:
            logger.info("No Python packages to install")
            return True
            
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        
        logger.info(f"Installing Python packages: {', '.join(packages)}")
        logger.info(f"Command: {' '.join(cmd)}")
        
        if dry_run:
            logger.info("Dry run - not executing command")
            return True
            
        try:
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode != 0:
                logger.error(f"Failed to install Python packages: {process.stderr.decode()}")
                return False
            logger.info("Python packages installed successfully")
            return True
        except Exception as e:
            logger.error(f"Error installing Python packages: {e}")
            return False


class ServiceManager:
    """Class to manage system services."""
    
    def __init__(self, platform_info: PlatformInfo):
        """Initialize the service manager.
        
        Args:
            platform_info: Platform information
        """
        self.platform_info = platform_info
        self.service_dir = "/etc/systemd/system" if self.platform_info.system == "Linux" else None
        
    def create_service_file(self, service_name: str, description: str, 
                          exec_start: str, working_dir: str, 
                          user: str = "root", dry_run: bool = False) -> bool:
        """Create a systemd service file.
        
        Args:
            service_name: Name of the service
            description: Service description
            exec_start: Command to execute
            working_dir: Working directory
            user: User to run the service as
            dry_run: If True, only print actions without executing
            
        Returns:
            True if successful, False otherwise
        """
        if self.platform_info.system != "Linux":
            logger.warning("Service creation only supported on Linux")
            return False
            
        if not self.service_dir or not os.path.exists(self.service_dir):
            logger.error(f"Service directory not found: {self.service_dir}")
            return False
            
        service_path = os.path.join(self.service_dir, f"{service_name}.service")
        
        service_content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
ExecStart={exec_start}
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
        
        logger.info(f"Creating service file: {service_path}")
        if dry_run:
            logger.info("Dry run - not creating service file")
            logger.info(f"Service file content:\n{service_content}")
            return True
            
        try:
            with open(service_path, "w") as f:
                f.write(service_content)
                
            # Set permissions
            os.chmod(service_path, 0o644)
            
            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            logger.info(f"Service file created: {service_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating service file: {e}")
            return False
            
    def enable_service(self, service_name: str, start: bool = True, dry_run: bool = False) -> bool:
        """Enable and optionally start a service.
        
        Args:
            service_name: Name of the service
            start: Whether to start the service
            dry_run: If True, only print actions without executing
            
        Returns:
            True if successful, False otherwise
        """
        if self.platform_info.system != "Linux":
            logger.warning("Service management only supported on Linux")
            return False
            
        logger.info(f"Enabling service: {service_name}")
        if dry_run:
            logger.info("Dry run - not enabling service")
            return True
            
        try:
            # Enable service
            subprocess.run(["systemctl", "enable", service_name], 
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            if start:
                logger.info(f"Starting service: {service_name}")
                subprocess.run(["systemctl", "start", service_name], 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            logger.info(f"Service enabled: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Error enabling service: {e}")
            return False


class ConfigManager:
    """Class to manage UnitMCP configuration."""
    
    def __init__(self, platform_info: PlatformInfo, base_dir: str):
        """Initialize the configuration manager.
        
        Args:
            platform_info: Platform information
            base_dir: Base directory for UnitMCP
        """
        self.platform_info = platform_info
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "config")
        
    def create_config_dir(self) -> bool:
        """Create the configuration directory."""
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir, exist_ok=True)
                logger.info(f"Created configuration directory: {self.config_dir}")
                return True
            except Exception as e:
                logger.error(f"Error creating configuration directory: {e}")
                return False
        return True
        
    def create_default_config(self, dry_run: bool = False) -> bool:
        """Create default configuration files.
        
        Args:
            dry_run: If True, only print actions without executing
            
        Returns:
            True if successful, False otherwise
        """
        if not self.create_config_dir():
            return False
            
        # Create main config file
        config = {
            "server": {
                "host": "0.0.0.0" if self.platform_info.is_raspberry_pi else "127.0.0.1",
                "port": 8888
            },
            "hardware": {
                "platform": "raspberry_pi" if self.platform_info.is_raspberry_pi else "desktop",
                "gpio_enabled": self.platform_info.is_raspberry_pi,
                "i2c_enabled": self.platform_info.is_raspberry_pi,
                "audio_enabled": True
            },
            "logging": {
                "level": "INFO",
                "file": os.path.join(self.base_dir, "logs", "unitmcp.log")
            }
        }
        
        config_path = os.path.join(self.config_dir, "config.json")
        
        logger.info(f"Creating default configuration: {config_path}")
        if dry_run:
            logger.info("Dry run - not creating configuration file")
            logger.info(f"Configuration content:\n{json.dumps(config, indent=2)}")
            return True
            
        try:
            # Create logs directory
            logs_dir = os.path.join(self.base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Write config file
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Default configuration created: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating default configuration: {e}")
            return False


class SelfTest:
    """Class to perform self-tests of the UnitMCP system."""
    
    def __init__(self, platform_info: PlatformInfo, base_dir: str):
        """Initialize the self-test.
        
        Args:
            platform_info: Platform information
            base_dir: Base directory for UnitMCP
        """
        self.platform_info = platform_info
        self.base_dir = base_dir
        
    def check_python_version(self) -> bool:
        """Check if the Python version is compatible."""
        major, minor = sys.version_info[:2]
        if major < 3 or (major == 3 and minor < 7):
            logger.error(f"Incompatible Python version: {major}.{minor}. Requires Python 3.7+")
            return False
            
        logger.info(f"Python version check passed: {major}.{minor}")
        return True
        
    def check_required_modules(self) -> bool:
        """Check if required Python modules are available."""
        required_modules = [
            "asyncio", "json", "logging", "os", "sys", "time", 
            "platform", "subprocess", "argparse"
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
                
        if missing_modules:
            logger.error(f"Missing required modules: {', '.join(missing_modules)}")
            return False
            
        logger.info("Required modules check passed")
        return True
        
    def check_optional_modules(self) -> Dict[str, bool]:
        """Check if optional Python modules are available."""
        optional_modules = {
            "RPi.GPIO": "GPIO control",
            "gpiozero": "GPIO abstraction",
            "smbus2": "I2C communication",
            "pyaudio": "Audio recording/playback",
            "pyttsx3": "Text-to-speech",
            "speech_recognition": "Speech recognition"
        }
        
        results = {}
        for module, description in optional_modules.items():
            try:
                __import__(module.split(".")[0])
                logger.info(f"Optional module available: {module} ({description})")
                results[module] = True
            except ImportError:
                logger.warning(f"Optional module not available: {module} ({description})")
                results[module] = False
                
        return results
        
    def check_gpio_access(self) -> bool:
        """Check if GPIO access is available."""
        if not self.platform_info.is_raspberry_pi:
            logger.info("GPIO check skipped (not a Raspberry Pi)")
            return False
            
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            # Just check if we can access GPIO without actually using pins
            logger.info("GPIO access check passed")
            return True
        except Exception as e:
            logger.warning(f"GPIO access check failed: {e}")
            return False
            
    def check_i2c_access(self) -> bool:
        """Check if I2C access is available."""
        if not self.platform_info.is_raspberry_pi:
            logger.info("I2C check skipped (not a Raspberry Pi)")
            return False
            
        # Check if i2c-tools is installed
        i2cdetect_path = shutil.which("i2cdetect")
        if not i2cdetect_path:
            logger.warning("i2cdetect not found, I2C check skipped")
            return False
            
        try:
            # Check if I2C is enabled
            process = subprocess.run(["i2cdetect", "-l"], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode != 0:
                logger.warning("I2C access check failed: i2cdetect command failed")
                return False
                
            output = process.stdout.decode()
            if not output.strip():
                logger.warning("I2C access check failed: No I2C buses found")
                return False
                
            logger.info("I2C access check passed")
            return True
        except Exception as e:
            logger.warning(f"I2C access check failed: {e}")
            return False
            
    def check_audio_access(self) -> bool:
        """Check if audio access is available."""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            p.terminate()
            
            if device_count > 0:
                logger.info(f"Audio access check passed: {device_count} devices found")
                return True
            else:
                logger.warning("Audio access check failed: No audio devices found")
                return False
        except Exception as e:
            logger.warning(f"Audio access check failed: {e}")
            return False
            
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all self-tests.
        
        Returns:
            Dictionary of test results
        """
        results = {
            "python_version": self.check_python_version(),
            "required_modules": self.check_required_modules(),
            "gpio_access": self.check_gpio_access(),
            "i2c_access": self.check_i2c_access(),
            "audio_access": self.check_audio_access()
        }
        
        # Add optional module results
        optional_modules = self.check_optional_modules()
        for module, result in optional_modules.items():
            results[f"module_{module}"] = result
            
        # Calculate overall result
        critical_tests = ["python_version", "required_modules"]
        results["overall"] = all(results[test] for test in critical_tests)
        
        return results


class InstallationExample:
    """Main installation and setup example class."""
    
    def __init__(self, base_dir: str, dry_run: bool = False):
        """Initialize the installation example.
        
        Args:
            base_dir: Base directory for UnitMCP
            dry_run: If True, only print actions without executing
        """
        self.base_dir = os.path.abspath(base_dir)
        self.dry_run = dry_run
        self.platform_info = PlatformInfo()
        self.dependency_manager = DependencyManager(self.platform_info)
        self.service_manager = ServiceManager(self.platform_info)
        self.config_manager = ConfigManager(self.platform_info, self.base_dir)
        self.self_test = SelfTest(self.platform_info, self.base_dir)
        
    def print_system_info(self):
        """Print system information."""
        info = self.platform_info.get_summary()
        
        logger.info("System Information:")
        logger.info(f"  System: {info['system']}")
        logger.info(f"  Machine: {info['machine']}")
        logger.info(f"  Distribution: {info['distribution']}")
        logger.info(f"  Raspberry Pi: {'Yes' if info['is_raspberry_pi'] else 'No'}")
        
    def install_dependencies(self):
        """Install system and Python dependencies."""
        # Check package manager
        if not self.dependency_manager.check_package_manager():
            logger.error("Package manager not available")
            return False
            
        # Install system packages
        system_packages = self.dependency_manager.get_required_packages()
        if not self.dependency_manager.install_system_packages(system_packages, self.dry_run):
            logger.error("Failed to install system packages")
            return False
            
        # Install Python packages
        python_packages = self.dependency_manager.get_python_packages()
        if not self.dependency_manager.install_python_packages(python_packages, self.dry_run):
            logger.error("Failed to install Python packages")
            return False
            
        logger.info("Dependencies installed successfully")
        return True
        
    def configure_system(self):
        """Configure the system for UnitMCP."""
        # Create default configuration
        if not self.config_manager.create_default_config(self.dry_run):
            logger.error("Failed to create default configuration")
            return False
            
        # Enable I2C on Raspberry Pi if needed
        if self.platform_info.is_raspberry_pi and not self.dry_run:
            try:
                # Check if I2C is already enabled
                if not os.path.exists("/dev/i2c-1"):
                    logger.info("Enabling I2C interface...")
                    
                    # Update config.txt
                    with open("/boot/config.txt", "a") as f:
                        f.write("\n# Enable I2C interface\ndtparam=i2c_arm=on\n")
                        
                    logger.info("I2C interface enabled (requires reboot)")
            except Exception as e:
                logger.error(f"Error enabling I2C interface: {e}")
                
        logger.info("System configured successfully")
        return True
        
    def setup_services(self):
        """Set up system services."""
        if not self.platform_info.is_raspberry_pi:
            logger.info("Skipping service setup (not a Raspberry Pi)")
            return True
            
        # Create UnitMCP service
        service_name = "unitmcp"
        description = "UnitMCP Hardware Control Service"
        exec_start = f"{sys.executable} {os.path.join(self.base_dir, 'src/unitmcp/server/main.py')}"
        
        if not self.service_manager.create_service_file(
            service_name, description, exec_start, self.base_dir, "root", self.dry_run):
            logger.error("Failed to create service file")
            return False
            
        # Enable and start service
        if not self.service_manager.enable_service(service_name, True, self.dry_run):
            logger.error("Failed to enable service")
            return False
            
        logger.info("Services set up successfully")
        return True
        
    def run_self_test(self):
        """Run self-tests to verify functionality."""
        logger.info("Running self-tests...")
        
        results = self.self_test.run_all_tests()
        
        logger.info("Self-test results:")
        for test, result in results.items():
            if test != "overall":
                status = "PASSED" if result else "FAILED"
                logger.info(f"  {test}: {status}")
                
        overall = "PASSED" if results["overall"] else "FAILED"
        logger.info(f"Overall self-test result: {overall}")
        
        return results["overall"]
        
    def run_installation(self):
        """Run the complete installation process."""
        logger.info("Starting UnitMCP installation")
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Dry run: {'Yes' if self.dry_run else 'No'}")
        
        # Print system information
        self.print_system_info()
        
        # Install dependencies
        logger.info("\n=== Installing Dependencies ===")
        if not self.install_dependencies():
            logger.error("Installation failed at dependency installation step")
            return False
            
        # Configure system
        logger.info("\n=== Configuring System ===")
        if not self.configure_system():
            logger.error("Installation failed at system configuration step")
            return False
            
        # Set up services
        logger.info("\n=== Setting Up Services ===")
        if not self.setup_services():
            logger.error("Installation failed at service setup step")
            return False
            
        # Run self-test
        logger.info("\n=== Running Self-Tests ===")
        self.run_self_test()
        
        logger.info("\nUnitMCP installation completed successfully")
        
        if self.platform_info.is_raspberry_pi and not self.dry_run:
            logger.info("\nNOTE: Some changes may require a system reboot to take effect")
            
        return True


def main():
    """Main function to run the installation example."""
    parser = argparse.ArgumentParser(description="UnitMCP Installation and Setup Example")
    parser.add_argument("--base-dir", default=os.getcwd(), 
                      help="Base directory for UnitMCP installation")
    parser.add_argument("--dry-run", action="store_true", 
                      help="Print actions without executing them")
    args = parser.parse_args()
    
    example = InstallationExample(args.base_dir, args.dry_run)
    example.run_installation()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nInstallation interrupted by user")
    except Exception as e:
        logger.error(f"Error during installation: {e}", exc_info=True)
