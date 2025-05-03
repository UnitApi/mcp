#!/usr/bin/env python3
"""
Process Manager for UnitMCP Remote Shell

This module provides process management capabilities for the remote shell,
allowing for monitoring and controlling multiple concurrent processes.
It helps prevent resource contention and ensures proper cleanup of resources.

Usage:
    Import this module in simple_remote_shell.py to manage processes.
"""

import os
import signal
import subprocess
import threading
import time
import logging
import psutil
import json
from datetime import datetime
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / ".unitmcp_process_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProcessManager")

class ProcessManager:
    """Manages processes for UnitMCP remote shell."""
    
    def __init__(self, lock_file_path=None):
        """Initialize the process manager."""
        self.processes = {}  # Dictionary to track running processes
        self.resources = {}  # Dictionary to track resource usage
        self.lock = threading.RLock()  # Lock for thread safety
        self.lock_file_path = lock_file_path or (Path.home() / ".unitmcp_process_lock.json")
        self.load_state()
        
        # Enhanced monitoring
        self.system_load_threshold = 0.8  # 80% CPU load threshold
        self.memory_threshold = 0.9  # 90% memory usage threshold
        self.monitoring_interval = 5  # seconds
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Start system monitoring
        self.start_system_monitoring()
    
    def load_state(self):
        """Load process state from file."""
        try:
            if self.lock_file_path.exists():
                with open(self.lock_file_path, 'r') as f:
                    data = json.load(f)
                    # Only load resource locks, not processes (they might be stale)
                    self.resources = data.get('resources', {})
                    
                    # Check if any processes are still running
                    stale_processes = data.get('processes', {})
                    for pid_str, proc_info in stale_processes.items():
                        pid = int(pid_str)
                        try:
                            # Check if process is still running
                            os.kill(pid, 0)
                            logger.info(f"Found existing process {pid} ({proc_info.get('name', 'unknown')})")
                            # Add to our tracking
                            self.processes[pid] = proc_info
                        except OSError:
                            # Process is not running, release its resources
                            self._release_resources(proc_info.get('resources', []))
                            logger.info(f"Cleaned up stale process {pid}")
        except Exception as e:
            logger.error(f"Error loading process state: {e}")
            self.resources = {}
            self.processes = {}
    
    def save_state(self):
        """Save process state to file."""
        try:
            with self.lock:
                with open(self.lock_file_path, 'w') as f:
                    json.dump({
                        'processes': self.processes,
                        'resources': self.resources,
                        'updated': datetime.now().isoformat()
                    }, f)
        except Exception as e:
            logger.error(f"Error saving process state: {e}")
    
    def _acquire_resources(self, resources):
        """
        Attempt to acquire resources needed by a process.
        
        Args:
            resources: List of resource identifiers (e.g., GPIO pin numbers)
            
        Returns:
            bool: True if all resources were acquired, False otherwise
        """
        with self.lock:
            # Check if any resources are already in use
            for resource in resources:
                if resource in self.resources and self.resources[resource]['in_use']:
                    logger.warning(f"Resource {resource} is already in use by process {self.resources[resource]['pid']}")
                    return False
            
            # Acquire all resources
            for resource in resources:
                self.resources[resource] = {
                    'in_use': True,
                    'acquired_time': time.time(),
                    'pid': None  # Will be set when process starts
                }
            
            return True
    
    def _release_resources(self, resources):
        """Release resources used by a process."""
        with self.lock:
            for resource in resources:
                if resource in self.resources:
                    self.resources[resource]['in_use'] = False
            self.save_state()
    
    def start_process(self, command, name=None, resources=None, timeout=None):
        """
        Start a new process with resource management.
        
        Args:
            command: Command to execute (list or string)
            name: Name for the process (for logging)
            resources: List of resources needed by the process
            timeout: Maximum execution time in seconds
            
        Returns:
            tuple: (success, process_id or error_message)
        """
        resources = resources or []
        name = name or f"process_{int(time.time())}"
        
        # Check system load before starting new process
        if self._is_system_overloaded():
            logger.warning("System is overloaded, delaying process start")
            # Wait for system load to decrease
            wait_time = 0
            max_wait = 30  # Maximum wait time in seconds
            while self._is_system_overloaded() and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
            
            if self._is_system_overloaded():
                logger.error("System remains overloaded after waiting, cannot start process")
                return False, "System is overloaded, cannot start process"
        
        # Try to acquire resources
        if not self._acquire_resources(resources):
            return False, "Required resources are in use by another process"
        
        try:
            # Start the process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=isinstance(command, str)
            )
            
            pid = process.pid
            logger.info(f"Started process {pid} ({name})")
            
            # Update resource ownership
            with self.lock:
                for resource in resources:
                    if resource in self.resources:
                        self.resources[resource]['pid'] = pid
                
                # Track the process
                self.processes[pid] = {
                    'name': name,
                    'command': command,
                    'start_time': time.time(),
                    'resources': resources,
                    'timeout': timeout,
                    'process_object': process  # Store the process object for better management
                }
                self.save_state()
            
            # Start a monitoring thread if timeout is specified
            if timeout:
                threading.Thread(
                    target=self._monitor_process,
                    args=(pid, timeout),
                    daemon=True
                ).start()
            
            return True, pid
        
        except Exception as e:
            # Release resources on failure
            self._release_resources(resources)
            logger.error(f"Error starting process: {e}")
            return False, str(e)
    
    def _is_system_overloaded(self):
        """Check if the system is overloaded."""
        try:
            # Check CPU load
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.system_load_threshold * 100:
                logger.warning(f"High CPU usage: {cpu_percent}%")
                return True
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold * 100:
                logger.warning(f"High memory usage: {memory.percent}%")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking system load: {e}")
            return False  # Assume not overloaded if we can't check
    
    def start_system_monitoring(self):
        """Start the system monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._system_monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("System monitoring active")
    
    def stop_system_monitoring(self):
        """Stop the system monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _system_monitor_loop(self):
        """Monitor system resources and processes."""
        while self.monitoring_active:
            try:
                # Check for process anomalies
                fixed, remaining = self.handle_anomalies(auto_fix=True)
                
                # Log any fixed anomalies
                for anomaly in fixed:
                    logger.info(f"Fixed anomaly: {anomaly}")
                
                # Check system load
                if self._is_system_overloaded():
                    # System is overloaded, take action
                    self._handle_system_overload()
                
                # Adjust monitoring interval based on system state
                if fixed or remaining or self._is_system_overloaded():
                    # More frequent checks if there are issues
                    sleep_time = 1
                else:
                    sleep_time = self.monitoring_interval
                
                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error in system monitor loop: {e}")
                time.sleep(5)  # Sleep longer on error
    
    def _handle_system_overload(self):
        """Handle system overload by terminating non-essential processes."""
        with self.lock:
            # Sort processes by priority (lower priority first)
            # Priority is determined by: no resources > non-interactive > oldest
            processes_to_check = []
            for pid, info in self.processes.items():
                priority = 0
                # Processes without resources are lower priority
                if not info.get('resources'):
                    priority -= 2
                # Non-interactive processes are lower priority
                if 'interactive' not in info.get('name', '').lower():
                    priority -= 1
                # Older processes are lower priority
                age = time.time() - info.get('start_time', time.time())
                priority -= min(age / 3600, 5)  # Max 5 points for age (5 hours)
                
                processes_to_check.append((pid, priority, info))
            
            # Sort by priority (lowest first)
            processes_to_check.sort(key=lambda x: x[1])
            
            # Terminate up to 2 lowest priority processes
            terminated_count = 0
            for pid, _, info in processes_to_check:
                if terminated_count >= 2:
                    break
                
                try:
                    logger.warning(f"Terminating process {pid} ({info.get('name')}) due to system overload")
                    self.terminate_process(pid)
                    terminated_count += 1
                except Exception as e:
                    logger.error(f"Error terminating process {pid}: {e}")
            
            if terminated_count > 0:
                logger.info(f"Terminated {terminated_count} processes to reduce system load")
    
    def _monitor_process(self, pid, timeout):
        """Monitor a process and terminate if it exceeds timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            try:
                # Check if process exists
                os.kill(pid, 0)
                
                # Check if process has completed
                if pid not in self.processes:
                    logger.info(f"Process {pid} completed within timeout")
                    return
                
                # Wait and check again
                time.sleep(1)
            except OSError:
                # Process no longer exists
                logger.info(f"Process {pid} no longer exists")
                self.cleanup_process(pid)
                return
        
        # If we get here, the process has timed out
        logger.warning(f"Process {pid} timed out after {timeout} seconds")
        self.terminate_process(pid)
    
    def cleanup_process(self, pid):
        """Clean up after a process has completed."""
        with self.lock:
            if pid in self.processes:
                resources = self.processes[pid].get('resources', [])
                self._release_resources(resources)
                
                # Close file descriptors if process object is available
                process_obj = self.processes[pid].get('process_object')
                if process_obj:
                    try:
                        if process_obj.stdout:
                            process_obj.stdout.close()
                        if process_obj.stderr:
                            process_obj.stderr.close()
                    except Exception as e:
                        logger.error(f"Error closing process file descriptors: {e}")
                
                del self.processes[pid]
                self.save_state()
                logger.info(f"Cleaned up process {pid}")
    
    def terminate_process(self, pid):
        """Terminate a running process."""
        try:
            # Try to terminate gracefully first
            os.kill(pid, signal.SIGTERM)
            
            # Give it a moment to terminate
            for _ in range(5):
                time.sleep(0.1)
                try:
                    # Check if process still exists
                    os.kill(pid, 0)
                except OSError:
                    # Process is gone
                    break
            else:
                # Process didn't terminate, force kill
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.warning(f"Force killed process {pid}")
                except OSError:
                    pass
            
            # Clean up resources
            self.cleanup_process(pid)
            return True
        except OSError as e:
            logger.error(f"Error terminating process {pid}: {e}")
            return False
    
    def get_running_processes(self):
        """Get information about all running processes."""
        with self.lock:
            current_time = time.time()
            result = {}
            
            for pid, info in list(self.processes.items()):
                # Check if process is still running
                try:
                    os.kill(pid, 0)
                    # Calculate runtime
                    runtime = current_time - info.get('start_time', current_time)
                    
                    # Get additional process info if available
                    try:
                        proc = psutil.Process(pid)
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        memory_info = proc.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)
                        
                        result[pid] = {
                            **info,
                            'runtime': runtime,
                            'runtime_formatted': f"{int(runtime // 60)}m {int(runtime % 60)}s",
                            'cpu_percent': cpu_percent,
                            'memory_mb': memory_mb
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Fall back to basic info if psutil info not available
                        result[pid] = {
                            **info,
                            'runtime': runtime,
                            'runtime_formatted': f"{int(runtime // 60)}m {int(runtime % 60)}s"
                        }
                except OSError:
                    # Process is not running anymore, clean it up
                    self.cleanup_process(pid)
            
            return result
    
    def get_resource_status(self):
        """Get status of all tracked resources."""
        with self.lock:
            return self.resources.copy()
    
    def handle_anomalies(self, auto_fix=False):
        """
        Check for and handle process anomalies.
        
        Args:
            auto_fix: If True, automatically fix detected anomalies
            
        Returns:
            tuple: (fixed_anomalies, remaining_anomalies)
        """
        fixed_anomalies = []
        remaining_anomalies = []
        
        with self.lock:
            current_time = time.time()
            
            # Check for process timeouts and resource contentions
            for pid, proc_info in list(self.processes.items()):
                # Check if process is still running
                try:
                    os.kill(pid, 0)
                    
                    # Check for timeout
                    timeout = proc_info.get('timeout')
                    if timeout and current_time - proc_info['start_time'] > timeout:
                        if auto_fix:
                            try:
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.1)
                                # Check if it's still alive and force kill if needed
                                try:
                                    os.kill(pid, 0)
                                    os.kill(pid, signal.SIGKILL)
                                except OSError:
                                    pass  # Process already terminated
                                
                                # Release resources
                                self._release_resources(proc_info.get('resources', []))
                                
                                # Remove from tracking
                                del self.processes[pid]
                                
                                fixed_anomalies.append({
                                    'type': 'timeout',
                                    'pid': pid,
                                    'name': proc_info.get('name'),
                                    'runtime': current_time - proc_info['start_time']
                                })
                            except OSError as e:
                                logger.error(f"Error terminating process {pid}: {e}")
                        else:
                            remaining_anomalies.append({
                                'type': 'timeout',
                                'pid': pid,
                                'name': proc_info.get('name'),
                                'runtime': current_time - proc_info['start_time']
                            })
                    
                    # Check for long-running processes (over 30 minutes)
                    elif current_time - proc_info['start_time'] > 1800:  # 30 minutes
                        if auto_fix:
                            # For long-running processes, we'll just log them but not terminate
                            # unless they're using critical resources
                            if proc_info.get('resources'):
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                    time.sleep(0.1)
                                    # Check if it's still alive and force kill if needed
                                    try:
                                        os.kill(pid, 0)
                                        os.kill(pid, signal.SIGKILL)
                                    except OSError:
                                        pass  # Process already terminated
                                    
                                    # Release resources
                                    self._release_resources(proc_info.get('resources', []))
                                    
                                    # Remove from tracking
                                    del self.processes[pid]
                                    
                                    fixed_anomalies.append({
                                        'type': 'long_running',
                                        'pid': pid,
                                        'name': proc_info.get('name'),
                                        'runtime': current_time - proc_info['start_time']
                                    })
                                except OSError as e:
                                    logger.error(f"Error terminating long-running process {pid}: {e}")
                            else:
                                # Just log non-resource-using long-running processes
                                remaining_anomalies.append({
                                    'type': 'long_running_no_resources',
                                    'pid': pid,
                                    'name': proc_info.get('name'),
                                    'runtime': current_time - proc_info['start_time']
                                })
                        else:
                            remaining_anomalies.append({
                                'type': 'long_running',
                                'pid': pid,
                                'name': proc_info.get('name'),
                                'runtime': current_time - proc_info['start_time']
                            })
                    
                    # Check for high CPU usage processes (over 80% for more than 5 minutes)
                    try:
                        proc = psutil.Process(pid)
                        cpu_percent = proc.cpu_percent(interval=0.1)
                        
                        if cpu_percent > 80 and current_time - proc_info['start_time'] > 300:  # 5 minutes
                            if auto_fix and proc_info.get('resources'):
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                    time.sleep(0.1)
                                    # Check if it's still alive and force kill if needed
                                    try:
                                        os.kill(pid, 0)
                                        os.kill(pid, signal.SIGKILL)
                                    except OSError:
                                        pass  # Process already terminated
                                    
                                    # Release resources
                                    self._release_resources(proc_info.get('resources', []))
                                    
                                    # Remove from tracking
                                    del self.processes[pid]
                                    
                                    fixed_anomalies.append({
                                        'type': 'high_cpu_usage',
                                        'pid': pid,
                                        'name': proc_info.get('name'),
                                        'cpu_percent': cpu_percent,
                                        'runtime': current_time - proc_info['start_time']
                                    })
                                except OSError as e:
                                    logger.error(f"Error terminating high CPU process {pid}: {e}")
                            else:
                                remaining_anomalies.append({
                                    'type': 'high_cpu_usage',
                                    'pid': pid,
                                    'name': proc_info.get('name'),
                                    'cpu_percent': cpu_percent,
                                    'runtime': current_time - proc_info['start_time']
                                })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                except OSError:
                    # Process is not running, clean up
                    self._release_resources(proc_info.get('resources', []))
                    del self.processes[pid]
                    logger.info(f"Cleaned up process {pid} that is no longer running")
            
            # Check for resource contentions
            resource_users = {}
            for pid, proc_info in self.processes.items():
                for resource in proc_info.get('resources', []):
                    if resource not in resource_users:
                        resource_users[resource] = []
                    resource_users[resource].append(pid)
            
            for resource, pids in resource_users.items():
                if len(pids) > 1:
                    # Resource contention detected
                    if auto_fix:
                        # Keep the most recent process and terminate others
                        pids_sorted = sorted(
                            pids,
                            key=lambda pid: self.processes[pid]['start_time'],
                            reverse=True
                        )
                        keep_pid = pids_sorted[0]
                        
                        for pid in pids_sorted[1:]:
                            try:
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.1)
                                # Check if it's still alive and force kill if needed
                                try:
                                    os.kill(pid, 0)
                                    os.kill(pid, signal.SIGKILL)
                                except OSError:
                                    pass  # Process already terminated
                                
                                # Release resources
                                self._release_resources(self.processes[pid].get('resources', []))
                                
                                # Remove from tracking
                                del self.processes[pid]
                                
                                fixed_anomalies.append({
                                    'type': 'resource_contention_fixed',
                                    'resource': resource,
                                    'terminated_pid': pid,
                                    'kept_pid': keep_pid
                                })
                            except OSError as e:
                                logger.error(f"Error terminating process {pid} in resource contention: {e}")
                    else:
                        remaining_anomalies.append({
                            'type': 'resource_contention',
                            'resource': resource,
                            'pids': pids
                        })
            
            # Check for zombie processes
            try:
                # This is Linux-specific
                if os.path.exists('/proc'):
                    for proc_dir in os.listdir('/proc'):
                        if proc_dir.isdigit():
                            pid = int(proc_dir)
                            try:
                                with open(f'/proc/{pid}/stat', 'r') as f:
                                    stat = f.read()
                                    # Field 3 is process state, 'Z' means zombie
                                    if ' Z ' in stat and pid in self.processes:
                                        if auto_fix:
                                            try:
                                                os.kill(pid, signal.SIGKILL)
                                                self._release_resources(self.processes[pid].get('resources', []))
                                                del self.processes[pid]
                                                fixed_anomalies.append({
                                                    'type': 'zombie_process_fixed',
                                                    'pid': pid
                                                })
                                            except OSError:
                                                pass
                                        else:
                                            remaining_anomalies.append({
                                                'type': 'zombie_process',
                                                'pid': pid
                                            })
                            except (IOError, OSError):
                                pass
            except Exception as e:
                logger.error(f"Error checking for zombie processes: {e}")
            
            # Check for orphaned resources (resources marked as in-use but with no associated process)
            orphaned_resources = []
            for resource, info in self.resources.items():
                if info.get('in_use') and info.get('pid'):
                    pid = info.get('pid')
                    if pid not in self.processes:
                        try:
                            # Double-check if process exists
                            os.kill(pid, 0)
                        except OSError:
                            # Process doesn't exist, resource is orphaned
                            orphaned_resources.append(resource)
            
            # Fix orphaned resources
            if orphaned_resources and auto_fix:
                for resource in orphaned_resources:
                    self.resources[resource]['in_use'] = False
                    self.resources[resource]['pid'] = None
                    fixed_anomalies.append({
                        'type': 'orphaned_resource_fixed',
                        'resource': resource
                    })
            elif orphaned_resources:
                for resource in orphaned_resources:
                    remaining_anomalies.append({
                        'type': 'orphaned_resource',
                        'resource': resource,
                        'pid': self.resources[resource].get('pid')
                    })
        
        # Save state after handling anomalies
        if fixed_anomalies:
            self.save_state()
        
        return fixed_anomalies, remaining_anomalies
    
    def get_system_status(self):
        """Get overall system status."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'process_count': len(self.processes),
                'resource_count': len([r for r, info in self.resources.items() if info.get('in_use')])
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e)
            }

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of the ProcessManager."""
    global _instance
    if _instance is None:
        _instance = ProcessManager()
    return _instance

# Install dependencies if needed
def ensure_dependencies():
    """Ensure required dependencies are installed."""
    try:
        import psutil
    except ImportError:
        print("Installing required dependency: psutil")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("Successfully installed psutil")
        except Exception as e:
            print(f"Failed to install psutil: {e}")
            print("Process monitoring will have limited functionality")

# Ensure dependencies when module is imported
ensure_dependencies()
