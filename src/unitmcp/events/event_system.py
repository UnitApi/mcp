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
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union

logger = logging.getLogger(__name__)


class Event:
    """
    Base class for events in the system.
    
    This class represents an event that can be published and subscribed to.
    """
    
    def __init__(self, event_type: str, source: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize an event.
        
        Parameters
        ----------
        event_type : str
            Type of the event
        source : str
            Source of the event (e.g., component or device ID)
        data : Optional[Dict[str, Any]], optional
            Event data, by default None
        """
        self.event_type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        """
        Get a string representation of the event.
        
        Returns
        -------
        str
            String representation of the event
        """
        return f"Event(type={self.event_type}, source={self.source}, timestamp={self.timestamp}, data={self.data})"


class EventListener(ABC):
    """
    Abstract base class for event listeners.
    
    This class defines the interface that all event listener implementations must follow.
    """
    
    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """
        Handle an event.
        
        Parameters
        ----------
        event : Event
            Event to handle
        """
        pass


class AsyncEventListener(EventListener):
    """
    Abstract base class for asynchronous event listeners.
    
    This class defines the interface for event listeners that handle events asynchronously.
    """
    
    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """
        Handle an event asynchronously.
        
        Parameters
        ----------
        event : Event
            Event to handle
        """
        pass


class EventBus:
    """
    Event bus implementation.
    
    This class provides functionality for publishing and subscribing to events.
    It implements the Observer Pattern for event handling.
    """
    
    def __init__(self):
        """
        Initialize an event bus.
        """
        self.listeners: Dict[str, Set[EventListener]] = {}
        self.wildcard_listeners: Set[EventListener] = set()
    
    def subscribe(self, event_type: str, listener: EventListener) -> None:
        """
        Subscribe a listener to an event type.
        
        Parameters
        ----------
        event_type : str
            Event type to subscribe to
        listener : EventListener
            Listener to subscribe
        """
        if event_type == "*":
            self.wildcard_listeners.add(listener)
        else:
            if event_type not in self.listeners:
                self.listeners[event_type] = set()
            self.listeners[event_type].add(listener)
        
        logger.debug(f"Subscribed {listener} to event type {event_type}")
    
    def unsubscribe(self, event_type: str, listener: EventListener) -> None:
        """
        Unsubscribe a listener from an event type.
        
        Parameters
        ----------
        event_type : str
            Event type to unsubscribe from
        listener : EventListener
            Listener to unsubscribe
        """
        if event_type == "*":
            self.wildcard_listeners.discard(listener)
        elif event_type in self.listeners:
            self.listeners[event_type].discard(listener)
            if not self.listeners[event_type]:
                del self.listeners[event_type]
        
        logger.debug(f"Unsubscribed {listener} from event type {event_type}")
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed listeners.
        
        Parameters
        ----------
        event : Event
            Event to publish
        """
        tasks = []
        
        # Notify specific listeners
        for listener in self.listeners.get(event.event_type, set()):
            tasks.append(self._notify_listener(listener, event))
        
        # Notify wildcard listeners
        for listener in self.wildcard_listeners:
            tasks.append(self._notify_listener(listener, event))
        
        # Wait for all notifications to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Published event: {event}")
    
    async def _notify_listener(self, listener: EventListener, event: Event) -> None:
        """
        Notify a listener of an event.
        
        Parameters
        ----------
        listener : EventListener
            Listener to notify
        event : Event
            Event to notify about
        """
        try:
            await listener.on_event(event)
        except Exception as e:
            logger.error(f"Error notifying listener {listener} of event {event}: {e}")


class FunctionEventListener(EventListener):
    """
    Function-based event listener implementation.
    
    This class provides a simple way to create event listeners from functions.
    """
    
    def __init__(self, callback: Callable[[Event], Any]):
        """
        Initialize a function event listener.
        
        Parameters
        ----------
        callback : Callable[[Event], Any]
            Callback function to call when an event is received
        """
        self.callback = callback
    
    async def on_event(self, event: Event) -> None:
        """
        Handle an event by calling the callback function.
        
        Parameters
        ----------
        event : Event
            Event to handle
        """
        result = self.callback(event)
        if asyncio.iscoroutine(result):
            await result


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


def subscribe(event_type: str, listener: Union[EventListener, Callable[[Event], Any]]) -> None:
    """
    Subscribe a listener to an event type on the global event bus.
    
    Parameters
    ----------
    event_type : str
        Event type to subscribe to
    listener : Union[EventListener, Callable[[Event], Any]]
        Listener to subscribe (can be an EventListener or a function)
    """
    if not isinstance(listener, EventListener):
        listener = FunctionEventListener(listener)
    
    _event_bus.subscribe(event_type, listener)


def unsubscribe(event_type: str, listener: Union[EventListener, Callable[[Event], Any]]) -> None:
    """
    Unsubscribe a listener from an event type on the global event bus.
    
    Parameters
    ----------
    event_type : str
        Event type to unsubscribe from
    listener : Union[EventListener, Callable[[Event], Any]]
        Listener to unsubscribe (can be an EventListener or a function)
    """
    if not isinstance(listener, EventListener):
        listener = FunctionEventListener(listener)
    
    _event_bus.unsubscribe(event_type, listener)


async def publish(event: Event) -> None:
    """
    Publish an event to the global event bus.
    
    Parameters
    ----------
    event : Event
        Event to publish
    """
    await _event_bus.publish(event)


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
        super().__init__(event_type, f"device:{device_id}", data)
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
        super().__init__(event_type, f"connection:{connection_id}", data)
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
        super().__init__(event_type, f"pipeline:{pipeline_id}", data)
        self.pipeline_id = pipeline_id


class EventLogger(EventListener):
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
async def publish_event(event_type: str, source: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Create and publish an event.
    
    Parameters
    ----------
    event_type : str
        Type of the event
    source : str
        Source of the event
    data : Optional[Dict[str, Any]], optional
        Event data, by default None
    """
    event = Event(event_type, source, data)
    await publish(event)


# Helper function to create and publish a device event
async def publish_device_event(event_type: str, device_id: str, data: Optional[Dict[str, Any]] = None) -> None:
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
    await publish(event)


# Helper function to create and publish a connection event
async def publish_connection_event(event_type: str, connection_id: str, data: Optional[Dict[str, Any]] = None) -> None:
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
    await publish(event)


# Helper function to create and publish a pipeline event
async def publish_pipeline_event(event_type: str, pipeline_id: str, data: Optional[Dict[str, Any]] = None) -> None:
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
    await publish(event)
