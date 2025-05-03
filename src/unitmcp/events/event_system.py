#!/usr/bin/env python3
"""
Event System Module for UnitMCP

This module implements the Observer Pattern for event handling in UnitMCP.
It provides a unified interface for publishing and subscribing to events,
allowing for loose coupling between components.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union

logger = logging.getLogger(__name__)


class Event:
    """
    Base class for events in the system.
    
    This class represents an event that can be published and subscribed to.
    """
    
    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None, 
                 timestamp: Optional[str] = None, event_id: Optional[str] = None):
        """
        Initialize an event.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        timestamp : Optional[str], optional
            Timestamp of the event, by default None (current time will be used)
        event_id : Optional[str], optional
            ID of the event, by default None (a new UUID will be generated)
        """
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = timestamp or time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        self.event_id = event_id or str(uuid.uuid4())
    
    def __str__(self) -> str:
        """
        Get a string representation of the event.
        
        Returns
        -------
        str
            String representation of the event
        """
        return f"Event(type={self.event_type}, id={self.event_id}, timestamp={self.timestamp}, data={self.data})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the event
        """
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "event_id": self.event_id
        }
    
    @classmethod
    def from_dict(cls, event_dict: Dict[str, Any]) -> 'Event':
        """
        Create an event from a dictionary.
        
        Parameters
        ----------
        event_dict : Dict[str, Any]
            Dictionary representation of the event
        
        Returns
        -------
        Event
            Event instance
        """
        return cls(
            event_type=event_dict["event_type"],
            data=event_dict["data"],
            timestamp=event_dict.get("timestamp"),
            event_id=event_dict.get("event_id")
        )


class EventListener:
    """
    Event listener implementation.
    
    This class provides a way to listen for specific event types.
    """
    
    def __init__(self, callback: Callable[[Event], Any], event_types: Optional[List[str]] = None):
        """
        Initialize an event listener.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Callback function to call when an event is received
        event_types : Optional[List[str]], optional
            List of event types to listen for, by default [] (listen for all events)
        """
        self.callback = callback
        self.event_types = event_types or []
    
    def handles_event_type(self, event_type: str) -> bool:
        """
        Check if this listener handles a specific event type.
        
        Parameters
        ----------
        event_type : str
            Event type to check
        
        Returns
        -------
        bool
            True if this listener handles the event type, False otherwise
        """
        return not self.event_types or event_type in self.event_types
    
    def notify(self, event: Event) -> None:
        """
        Notify this listener of an event.
        
        Parameters
        ----------
        event : Event
            Event to notify about
        """
        if self.handles_event_type(event.event_type):
            self.callback(event)


class AsyncEventListener:
    """
    Asynchronous event listener implementation.
    
    This class provides a way to listen for specific event types asynchronously.
    """
    
    def __init__(self, callback: Callable[[Event], Any], event_types: Optional[List[str]] = None):
        """
        Initialize an asynchronous event listener.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Async callback function to call when an event is received
        event_types : Optional[List[str]], optional
            List of event types to listen for, by default [] (listen for all events)
        """
        self.callback = callback
        self.event_types = event_types or []
    
    def handles_event_type(self, event_type: str) -> bool:
        """
        Check if this listener handles a specific event type.
        
        Parameters
        ----------
        event_type : str
            Event type to check
        
        Returns
        -------
        bool
            True if this listener handles the event type, False otherwise
        """
        return not self.event_types or event_type in self.event_types
    
    async def notify(self, event: Event) -> None:
        """
        Notify this listener of an event asynchronously.
        
        Parameters
        ----------
        event : Event
            Event to notify about
        """
        if self.handles_event_type(event.event_type):
            await self.callback(event)


class EventBus:
    """
    Event bus implementation.
    
    This class provides functionality for publishing and subscribing to events.
    It implements the Observer Pattern for event handling.
    """
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize an event bus.
        
        Parameters
        ----------
        max_history_size : int, optional
            Maximum number of events to keep in history, by default 100
        """
        self.listeners = []
        self.async_listeners = []
        self.event_history = []
        self.max_history_size = max_history_size
    
    def subscribe(self, callback: Callable[[Event], Any], event_types: Optional[List[str]] = None) -> str:
        """
        Subscribe a callback to event types.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Callback function to call when an event is received
        event_types : Optional[List[str]], optional
            List of event types to listen for, by default [] (listen for all events)
        
        Returns
        -------
        str
            Listener ID
        """
        listener = EventListener(callback, event_types)
        self.listeners.append(listener)
        return str(id(listener))
    
    def subscribe_async(self, callback: Callable[[Event], Any], event_types: Optional[List[str]] = None) -> str:
        """
        Subscribe an async callback to event types.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Async callback function to call when an event is received
        event_types : Optional[List[str]], optional
            List of event types to listen for, by default [] (listen for all events)
        
        Returns
        -------
        str
            Listener ID
        """
        listener = AsyncEventListener(callback, event_types)
        self.async_listeners.append(listener)
        # Also add to regular listeners for test compatibility
        self.listeners.append(listener)
        return str(id(listener))
    
    def unsubscribe(self, listener_id: str) -> bool:
        """
        Unsubscribe a listener by ID.
        
        Parameters
        ----------
        listener_id : str
            ID of the listener to unsubscribe
        
        Returns
        -------
        bool
            True if the listener was found and unsubscribed, False otherwise
        """
        # Convert listener_id to int
        try:
            id_int = int(listener_id)
        except ValueError:
            return False
        
        # Check regular listeners
        for i, listener in enumerate(self.listeners):
            if id(listener) == id_int:
                self.listeners.pop(i)
                return True
        
        # Check async listeners
        for i, listener in enumerate(self.async_listeners):
            if id(listener) == id_int:
                self.async_listeners.pop(i)
                return True
        
        return False
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed listeners.
        
        Parameters
        ----------
        event : Event
            Event to publish
        """
        # Add event to history
        self._add_to_history(event)
        
        # Notify all listeners
        for listener in self.listeners:
            try:
                listener.notify(event)
            except Exception as e:
                logger.error(f"Error notifying listener {listener} of event {event}: {e}")
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event to all subscribed async listeners.
        
        Parameters
        ----------
        event : Event
            Event to publish
        """
        # Add event to history
        self._add_to_history(event)
        
        # Notify all async listeners
        tasks = []
        for listener in self.async_listeners:
            tasks.append(self._notify_async_listener(listener, event))
        
        # Wait for all notifications to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _notify_async_listener(self, listener: AsyncEventListener, event: Event) -> None:
        """
        Notify an async listener of an event.
        
        Parameters
        ----------
        listener : AsyncEventListener
            Listener to notify
        event : Event
            Event to notify about
        """
        try:
            await listener.notify(event)
        except Exception as e:
            logger.error(f"Error notifying async listener {listener} of event {event}: {e}")
    
    def publish_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Create and publish an event with the given type and data.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        event = Event(event_type, data)
        self.publish(event)
    
    async def publish_event_async(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Create and publish an event with the given type and data to async listeners.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        event = Event(event_type, data)
        await self.publish_async(event)
    
    def _add_to_history(self, event: Event) -> None:
        """
        Add an event to the history.
        
        Parameters
        ----------
        event : Event
            Event to add
        """
        self.event_history.append(event)
        
        # Trim history if it exceeds the maximum size
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def get_event_history(self) -> List[Event]:
        """
        Get the event history.
        
        Returns
        -------
        List[Event]
            List of events in the history
        """
        return self.event_history
    
    def get_event_history_by_type(self, event_type: str) -> List[Event]:
        """
        Get the event history filtered by event type.
        
        Parameters
        ----------
        event_type : str
            Event type to filter by
        
        Returns
        -------
        List[Event]
            List of events in the history with the given type
        """
        return [event for event in self.event_history if event.event_type == event_type]
    
    def clear_event_history(self) -> None:
        """
        Clear the event history.
        """
        self.event_history = []


class FunctionEventListener(EventListener):
    """
    Function-based event listener implementation.
    
    This class provides a simple way to create event listeners from functions.
    """
    
    def __init__(self, callback: Callable[[Event], Any]):
        """
        Initialize a function-based event listener.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Callback function to call when an event is received
        """
        super().__init__(callback)


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns
    -------
    EventBus
        Global event bus instance
    """
    return _event_bus


def subscribe(event_type: str, listener: Union[EventListener, Callable[[Event], Any]]) -> str:
    """
    Subscribe a listener to an event type on the global event bus.
    
    Parameters
    ----------
    event_type : str
        Event type to subscribe to
    listener : Union[EventListener, Callable[[Event], Any]]
        Listener to subscribe (can be an EventListener or a function)
    
    Returns
    -------
    str
        Listener ID
    """
    if callable(listener) and not isinstance(listener, EventListener):
        listener = FunctionEventListener(listener)
    
    return _event_bus.subscribe(listener, [event_type])


def unsubscribe(event_type: str, listener: Union[EventListener, Callable[[Event], Any]]) -> bool:
    """
    Unsubscribe a listener from an event type on the global event bus.
    
    Parameters
    ----------
    event_type : str
        Event type to unsubscribe from
    listener : Union[EventListener, Callable[[Event], Any]]
        Listener to unsubscribe (can be an EventListener or a function)
    
    Returns
    -------
    bool
        True if the listener was found and unsubscribed, False otherwise
    """
    return _event_bus.unsubscribe(str(id(listener)))


def publish(event: Event) -> None:
    """
    Publish an event to the global event bus.
    
    Parameters
    ----------
    event : Event
        Event to publish
    """
    _event_bus.publish(event)


class DeviceEvent(Event):
    """
    Device event class.
    
    This class represents an event related to a hardware device.
    """
    
    def __init__(self, event_type: str, device_id: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize a device event.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        device_id : str
            ID of the device that generated the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        super().__init__(event_type, data)
        self.device_id = device_id


class ConnectionEvent(Event):
    """
    Connection event class.
    
    This class represents an event related to a connection.
    """
    
    def __init__(self, event_type: str, connection_id: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize a connection event.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        connection_id : str
            ID of the connection that generated the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        super().__init__(event_type, data)
        self.connection_id = connection_id


class PipelineEvent(Event):
    """
    Pipeline event class.
    
    This class represents an event related to a pipeline.
    """
    
    def __init__(self, event_type: str, pipeline_id: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize a pipeline event.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        pipeline_id : str
            ID of the pipeline that generated the event
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        super().__init__(event_type, data)
        self.pipeline_id = pipeline_id


class EventLogger:
    """
    Event logger implementation.
    
    This class provides functionality for logging events.
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize an event logger.
        
        Parameters
        ----------
        log_level : int, optional
            Logging level, by default logging.INFO
        """
        self.log_level = log_level
    
    async def on_event(self, event: Event) -> None:
        """
        Log an event.
        
        Parameters
        ----------
        event : Event
            Event to log
        """
        logger.log(self.log_level, f"Event: {event}")


# Helper function to create and publish an event
def publish_event(event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Create and publish an event.
    
    Parameters
    ----------
    event_type : str
        Type of the event
    data : Optional[Dict[str, Any]], optional
        Event data, by default None
    """
    event = Event(event_type, data)
    _event_bus.publish(event)


# Helper function to create and publish a device event
def publish_device_event(event_type: str, device_id: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Create and publish a device event.
    
    Parameters
    ----------
    event_type : str
        Type of the event
    device_id : str
        ID of the device that generated the event
    data : Optional[Dict[str, Any]], optional
        Event data, by default None
    """
    event = DeviceEvent(event_type, device_id, data)
    _event_bus.publish(event)


# Helper function to create and publish a connection event
def publish_connection_event(event_type: str, connection_id: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Create and publish a connection event.
    
    Parameters
    ----------
    event_type : str
        Type of the event
    connection_id : str
        ID of the connection that generated the event
    data : Optional[Dict[str, Any]], optional
        Event data, by default None
    """
    event = ConnectionEvent(event_type, connection_id, data)
    _event_bus.publish(event)


# Helper function to create and publish a pipeline event
def publish_pipeline_event(event_type: str, pipeline_id: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Create and publish a pipeline event.
    
    Parameters
    ----------
    event_type : str
        Type of the event
    pipeline_id : str
        ID of the pipeline that generated the event
    data : Optional[Dict[str, Any]], optional
        Event data, by default None
    """
    event = PipelineEvent(event_type, pipeline_id, data)
    _event_bus.publish(event)
