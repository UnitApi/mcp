"""Runner manager module for UnitMCP Orchestrator."""

import os
import sys
import time
import logging
import subprocess
import uuid
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class RunnerManager:
    """
    Manager for UnitMCP runners.
    
    This class provides functionality to:
    - Start and stop runners
    - Monitor runner status
    - Manage runner configurations
    """
    
    def __init__(self):
        """Initialize the RunnerManager."""
        self.active_runners = {}
        logger.info("RunnerManager initialized")
    
    def start_runner(self, example_path: str, example_name: str, 
                    simulation: bool = True, host: str = "localhost", 
                    port: int = 8080, ssh_username: str = None, 
                    ssh_key_path: str = None, ssl_enabled: bool = False,
                    **kwargs) -> Dict[str, Any]:
        """
        Start a runner for an example.
        
        Args:
            example_path: Path to the example directory
            example_name: Name of the example
            simulation: Whether to run in simulation mode
            host: Host to connect to for remote execution
            port: Port to use for connection
            ssh_username: Username for SSH connection
            ssh_key_path: Path to SSH key file
            ssl_enabled: Whether to enable SSL
            **kwargs: Additional arguments to pass to the runner
            
        Returns:
            Dictionary with information about the running example
        """
        # Create a unique ID for this runner
        runner_id = str(uuid.uuid4())
        
        # Prepare environment variables
        env = os.environ.copy()
        env["SIMULATION"] = "1" if simulation else "0"
        env["SERVER_HOST"] = host
        env["SERVER_PORT"] = str(port)
        
        if ssh_username:
            env["RPI_USERNAME"] = ssh_username
        
        if ssh_key_path:
            env["SSH_KEY_PATH"] = os.path.expanduser(ssh_key_path)
        
        env["ENABLE_SSL"] = "true" if ssl_enabled else "false"
        
        # Store information about the running example
        runner_info = {
            "id": runner_id,
            "example": example_name,
            "path": example_path,
            "simulation": simulation,
            "host": host,
            "port": port,
            "ssh_username": ssh_username,
            "ssh_key_path": ssh_key_path,
            "ssl_enabled": ssl_enabled,
            "status": "starting",
            "pid": None,
            "start_time": None,
            "env": env
        }
        
        self.active_runners[runner_id] = runner_info
        
        # Check for runner.py, server.py, or start_server.py
        runner_path = os.path.join(example_path, "runner.py")
        server_path = os.path.join(example_path, "server.py")
        start_server_path = os.path.join(example_path, "start_server.py")
        
        start_time = time.time()
        
        # Determine which script to run
        if os.path.exists(runner_path):
            script_path = runner_path
        elif os.path.exists(server_path):
            script_path = server_path
        elif os.path.exists(start_server_path):
            script_path = start_server_path
        else:
            runner_info["status"] = "failed"
            runner_info["error"] = "No runner.py, server.py, or start_server.py found"
            return runner_info
        
        # Build command
        cmd = [sys.executable, script_path]
        
        # Add any additional arguments
        for key, value in kwargs.items():
            if key.startswith("arg_"):
                arg_name = key[4:]  # Remove "arg_" prefix
                cmd.extend([f"--{arg_name}", str(value)])
        
        logger.info(f"Starting runner for example '{example_name}': {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd, 
                env=env, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=example_path
            )
            
            runner_info["pid"] = process.pid
            runner_info["start_time"] = start_time
            runner_info["status"] = "running"
            runner_info["process"] = process
            
            return runner_info
        except Exception as e:
            logger.error(f"Failed to start runner for example '{example_name}': {e}")
            runner_info["status"] = "failed"
            runner_info["error"] = str(e)
            return runner_info
    
    def stop_runner(self, runner_id: str) -> bool:
        """
        Stop a running example.
        
        Args:
            runner_id: ID of the runner to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if runner_id not in self.active_runners:
            logger.warning(f"Runner '{runner_id}' not found")
            return False
        
        runner_info = self.active_runners[runner_id]
        if runner_info["status"] != "running":
            logger.warning(f"Runner '{runner_id}' is not running")
            return False
        
        try:
            process = runner_info.get("process")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            runner_info["status"] = "stopped"
            return True
        except Exception as e:
            logger.error(f"Failed to stop runner '{runner_id}': {e}")
            return False
    
    def get_runner_status(self, runner_id: str) -> Dict[str, Any]:
        """
        Get status of a running example.
        
        Args:
            runner_id: ID of the runner
            
        Returns:
            Dictionary with status information
        """
        if runner_id not in self.active_runners:
            raise ValueError(f"Runner '{runner_id}' not found")
        
        runner_info = self.active_runners[runner_id]
        process = runner_info.get("process")
        
        if process:
            # Check if process is still running
            if process.poll() is not None:
                runner_info["status"] = "finished" if process.returncode == 0 else "failed"
                runner_info["return_code"] = process.returncode
            
            # Get output
            try:
                # Try to get output without blocking
                stdout_data = b""
                stderr_data = b""
                
                if process.stdout:
                    stdout_data = process.stdout.read1(4096) if hasattr(process.stdout, 'read1') else b""
                
                if process.stderr:
                    stderr_data = process.stderr.read1(4096) if hasattr(process.stderr, 'read1') else b""
                
                if stdout_data:
                    if "stdout" not in runner_info:
                        runner_info["stdout"] = ""
                    runner_info["stdout"] += stdout_data.decode(errors='replace')
                
                if stderr_data:
                    if "stderr" not in runner_info:
                        runner_info["stderr"] = ""
                    runner_info["stderr"] += stderr_data.decode(errors='replace')
                
            except Exception as e:
                logger.warning(f"Error getting process output: {e}")
        
        return runner_info
    
    def get_active_runners(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active runners.
        
        Returns:
            Dictionary with runner IDs as keys and status information as values
        """
        # Update status of all runners
        for runner_id in list(self.active_runners.keys()):
            try:
                self.get_runner_status(runner_id)
            except Exception:
                pass
        
        return self.active_runners
    
    def cleanup_finished_runners(self) -> int:
        """
        Remove finished runners from the active runners list.
        
        Returns:
            Number of runners removed
        """
        count = 0
        for runner_id in list(self.active_runners.keys()):
            try:
                status = self.get_runner_status(runner_id)
                if status["status"] in ["finished", "failed", "stopped"]:
                    del self.active_runners[runner_id]
                    count += 1
            except Exception:
                # If we can't get status, assume it's dead
                del self.active_runners[runner_id]
                count += 1
        
        return count
