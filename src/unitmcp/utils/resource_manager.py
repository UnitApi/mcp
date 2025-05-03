"""
Resource management utilities for UnitMCP.

This module provides utilities for managing resources such as network connections,
file handles, and other resources that need proper cleanup.

Classes:
    ResourceManager: Context manager for tracking and cleaning up resources
    
Functions:
    safe_close: Safely close a resource, handling exceptions

Example:
    ```python
    from unitmcp.utils.resource_manager import ResourceManager
    
    # Use as a context manager
    with ResourceManager() as rm:
        # Register resources for automatic cleanup
        ssh_client = paramiko.SSHClient()
        ssh_client.connect(hostname, port, username, password)
        rm.register(ssh_client, cleanup_func=ssh_client.close)
        
        # Resources will be automatically cleaned up when exiting the context
    ```
"""

import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

from .exceptions import ResourceError

logger = logging.getLogger(__name__)

T = TypeVar('T')

def safe_close(resource: Any, cleanup_func: Optional[Callable] = None) -> None:
    """
    Safely close a resource, handling exceptions.
    
    Args:
        resource: The resource to close
        cleanup_func: Optional function to call to clean up the resource.
            If None, tries to call close() or __exit__() on the resource.
    
    Raises:
        ResourceError: If the resource cannot be closed and the error is critical
    """
    if resource is None:
        return
        
    try:
        if cleanup_func:
            cleanup_func()
        elif hasattr(resource, 'close') and callable(resource.close):
            resource.close()
        elif hasattr(resource, '__exit__') and callable(resource.__exit__):
            resource.__exit__(None, None, None)
    except Exception as e:
        logger.warning(f"Error closing resource {resource}: {e}")
        logger.debug(traceback.format_exc())


class ResourceManager:
    """
    Context manager for tracking and cleaning up resources.
    
    This class provides a way to register resources that need to be
    cleaned up, and ensures they are properly closed when the context
    is exited, even if an exception occurs.
    """
    
    def __init__(self):
        """Initialize the resource manager."""
        self._resources: List[Dict[str, Any]] = []
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager and clean up all registered resources.
        
        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
        """
        self.cleanup_all()
    
    def register(self, resource: Any, cleanup_func: Optional[Callable] = None, 
                 name: Optional[str] = None) -> Any:
        """
        Register a resource for cleanup.
        
        Args:
            resource: The resource to register
            cleanup_func: Optional function to call to clean up the resource.
                If None, tries to call close() or __exit__() on the resource.
            name: Optional name for the resource, for logging purposes
            
        Returns:
            The registered resource
        """
        if resource is None:
            return None
            
        resource_name = name or str(resource)
        self._resources.append({
            'resource': resource,
            'cleanup_func': cleanup_func,
            'name': resource_name
        })
        
        return resource
    
    def unregister(self, resource: Any) -> None:
        """
        Unregister a resource.
        
        Args:
            resource: The resource to unregister
        """
        self._resources = [r for r in self._resources if r['resource'] is not resource]
    
    def cleanup(self, resource: Any) -> None:
        """
        Clean up a specific resource.
        
        Args:
            resource: The resource to clean up
            
        Raises:
            ResourceError: If the resource cannot be cleaned up
        """
        for r in self._resources:
            if r['resource'] is resource:
                safe_close(r['resource'], r.get('cleanup_func'))
                self.unregister(resource)
                return
                
        raise ResourceError(f"Resource not found: {resource}")
    
    def cleanup_all(self) -> None:
        """
        Clean up all registered resources in reverse order.
        
        This ensures that resources are cleaned up in the opposite order
        they were registered, which is important for dependencies.
        """
        # Clean up in reverse order (LIFO)
        for r in reversed(self._resources):
            try:
                safe_close(r['resource'], r.get('cleanup_func'))
            except Exception as e:
                logger.error(f"Error cleaning up resource {r['name']}: {e}")
                logger.debug(traceback.format_exc())
        
        self._resources = []


class ManagedResource(Generic[T]):
    """
    A wrapper for a resource that ensures proper cleanup.
    
    This class can be used to wrap a resource and ensure it is properly
    closed when it is no longer needed.
    
    Example:
        ```python
        # Create a managed SSH client
        ssh_client = ManagedResource(
            paramiko.SSHClient(),
            cleanup_func=lambda client: client.close()
        )
        
        # Use the resource
        ssh_client.value.connect(hostname, port, username, password)
        
        # The resource will be automatically cleaned up when ssh_client is garbage collected
        ```
    """
    
    def __init__(self, resource: T, cleanup_func: Optional[Callable[[T], None]] = None):
        """
        Initialize the managed resource.
        
        Args:
            resource: The resource to manage
            cleanup_func: Optional function to call to clean up the resource.
                If None, tries to call close() or __exit__() on the resource.
        """
        self._resource = resource
        self._cleanup_func = cleanup_func
        
    def __del__(self):
        """Clean up the resource when the wrapper is garbage collected."""
        self.close()
    
    @property
    def value(self) -> T:
        """Get the wrapped resource."""
        return self._resource
    
    def close(self) -> None:
        """Close the resource."""
        if self._resource is not None:
            if self._cleanup_func:
                self._cleanup_func(self._resource)
            else:
                safe_close(self._resource)
            self._resource = None
    
    def __enter__(self):
        """Enter the context manager."""
        return self._resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and clean up the resource."""
        self.close()
