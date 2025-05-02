#!/usr/bin/env python3
"""
Unit tests for the event system module.

This module contains tests for the event system implementations.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import logging
from typing import Dict, Any, List, Callable, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from unitmcp.events.event_system import (
    Event,
    EventListener,
    EventBus,
    AsyncEventListener
)


class TestEvent(unittest.TestCase):
    """
    Test cases for the Event class.
    """
    
    def test_init(self):
        """
        Test initialization of Event.
        """
        event_type = "test_event"
        data = {"key": "value"}
        event = Event(event_type, data)
        
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.data, data)
        self.assertIsNotNone(event.timestamp)
        self.assertIsNotNone(event.event_id)
    
    def test_to_dict(self):
        """
        Test converting an event to a dictionary.
        """
        event_type = "test_event"
        data = {"key": "value"}
        event = Event(event_type, data)
        
        event_dict = event.to_dict()
        
        self.assertEqual(event_dict["event_type"], event_type)
        self.assertEqual(event_dict["data"], data)
        self.assertIn("timestamp", event_dict)
        self.assertIn("event_id", event_dict)
    
    def test_from_dict(self):
        """
        Test creating an event from a dictionary.
        """
        event_dict = {
            "event_type": "test_event",
            "data": {"key": "value"},
            "timestamp": "2023-01-01T00:00:00",
            "event_id": "test_id"
        }
        
        event = Event.from_dict(event_dict)
        
        self.assertEqual(event.event_type, event_dict["event_type"])
        self.assertEqual(event.data, event_dict["data"])
        self.assertEqual(event.timestamp, event_dict["timestamp"])
        self.assertEqual(event.event_id, event_dict["event_id"])
    
    def test_str(self):
        """
        Test string representation of an event.
        """
        event_type = "test_event"
        data = {"key": "value"}
        event = Event(event_type, data)
        
        event_str = str(event)
        
        self.assertIn(event_type, event_str)
        self.assertIn(str(data), event_str)
        self.assertIn(event.event_id, event_str)


class TestEventListener(unittest.TestCase):
    """
    Test cases for the EventListener class.
    """
    
    def test_init(self):
        """
        Test initialization of EventListener.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = EventListener(callback, event_types)
        
        self.assertEqual(listener.callback, callback)
        self.assertEqual(listener.event_types, event_types)
    
    def test_init_default_event_types(self):
        """
        Test initialization of EventListener with default event types.
        """
        callback = MagicMock()
        listener = EventListener(callback)
        
        self.assertEqual(listener.callback, callback)
        self.assertEqual(listener.event_types, [])
    
    def test_handles_event_type(self):
        """
        Test checking if a listener handles an event type.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = EventListener(callback, event_types)
        
        self.assertTrue(listener.handles_event_type("test_event"))
        self.assertFalse(listener.handles_event_type("other_event"))
    
    def test_handles_event_type_empty_list(self):
        """
        Test checking if a listener with an empty event types list handles an event type.
        """
        callback = MagicMock()
        listener = EventListener(callback)
        
        self.assertTrue(listener.handles_event_type("test_event"))
        self.assertTrue(listener.handles_event_type("other_event"))
    
    def test_notify(self):
        """
        Test notifying a listener of an event.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = EventListener(callback, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        listener.notify(event)
        
        callback.assert_called_once_with(event)
    
    def test_notify_not_handled(self):
        """
        Test notifying a listener of an event it doesn't handle.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = EventListener(callback, event_types)
        
        event = Event("other_event", {"key": "value"})
        
        listener.notify(event)
        
        callback.assert_not_called()


class TestAsyncEventListener(unittest.TestCase):
    """
    Test cases for the AsyncEventListener class.
    """
    
    def test_init(self):
        """
        Test initialization of AsyncEventListener.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = AsyncEventListener(callback, event_types)
        
        self.assertEqual(listener.callback, callback)
        self.assertEqual(listener.event_types, event_types)
    
    def test_init_default_event_types(self):
        """
        Test initialization of AsyncEventListener with default event types.
        """
        callback = MagicMock()
        listener = AsyncEventListener(callback)
        
        self.assertEqual(listener.callback, callback)
        self.assertEqual(listener.event_types, [])
    
    def test_handles_event_type(self):
        """
        Test checking if a listener handles an event type.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        listener = AsyncEventListener(callback, event_types)
        
        self.assertTrue(listener.handles_event_type("test_event"))
        self.assertFalse(listener.handles_event_type("other_event"))
    
    def test_handles_event_type_empty_list(self):
        """
        Test checking if a listener with an empty event types list handles an event type.
        """
        callback = MagicMock()
        listener = AsyncEventListener(callback)
        
        self.assertTrue(listener.handles_event_type("test_event"))
        self.assertTrue(listener.handles_event_type("other_event"))
    
    async def async_test_notify(self):
        """
        Test notifying an async listener of an event.
        """
        # Create a mock async callback
        async def async_callback(event):
            pass
        
        callback = MagicMock(side_effect=async_callback)
        event_types = ["test_event"]
        listener = AsyncEventListener(callback, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        await listener.notify(event)
        
        callback.assert_called_once_with(event)
    
    async def async_test_notify_not_handled(self):
        """
        Test notifying an async listener of an event it doesn't handle.
        """
        # Create a mock async callback
        async def async_callback(event):
            pass
        
        callback = MagicMock(side_effect=async_callback)
        event_types = ["test_event"]
        listener = AsyncEventListener(callback, event_types)
        
        event = Event("other_event", {"key": "value"})
        
        await listener.notify(event)
        
        callback.assert_not_called()
    
    def test_notify(self):
        """
        Test the notify method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_notify())
        finally:
            loop.close()
    
    def test_notify_not_handled(self):
        """
        Test the notify method with an event that is not handled.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_notify_not_handled())
        finally:
            loop.close()


class TestEventBus(unittest.TestCase):
    """
    Test cases for the EventBus class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.event_bus = EventBus()
    
    def test_init(self):
        """
        Test initialization of EventBus.
        """
        self.assertEqual(self.event_bus.listeners, [])
        self.assertEqual(self.event_bus.event_history, [])
        self.assertEqual(self.event_bus.max_history_size, 100)
    
    def test_subscribe(self):
        """
        Test subscribing a listener to the event bus.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        listener_id = self.event_bus.subscribe(callback, event_types)
        
        self.assertEqual(len(self.event_bus.listeners), 1)
        self.assertIsInstance(self.event_bus.listeners[0], EventListener)
        self.assertEqual(self.event_bus.listeners[0].callback, callback)
        self.assertEqual(self.event_bus.listeners[0].event_types, event_types)
        self.assertIsNotNone(listener_id)
    
    def test_subscribe_async(self):
        """
        Test subscribing an async listener to the event bus.
        """
        async def async_callback(event):
            pass
        
        event_types = ["test_event"]
        
        listener_id = self.event_bus.subscribe_async(async_callback, event_types)
        
        self.assertEqual(len(self.event_bus.listeners), 1)
        self.assertIsInstance(self.event_bus.listeners[0], AsyncEventListener)
        self.assertEqual(self.event_bus.listeners[0].callback.__name__, async_callback.__name__)
        self.assertEqual(self.event_bus.listeners[0].event_types, event_types)
        self.assertIsNotNone(listener_id)
    
    def test_unsubscribe(self):
        """
        Test unsubscribing a listener from the event bus.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        listener_id = self.event_bus.subscribe(callback, event_types)
        
        self.assertEqual(len(self.event_bus.listeners), 1)
        
        self.event_bus.unsubscribe(listener_id)
        
        self.assertEqual(len(self.event_bus.listeners), 0)
    
    def test_unsubscribe_invalid_id(self):
        """
        Test unsubscribing a listener with an invalid ID.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        listener_id = self.event_bus.subscribe(callback, event_types)
        
        self.assertEqual(len(self.event_bus.listeners), 1)
        
        self.event_bus.unsubscribe("invalid_id")
        
        self.assertEqual(len(self.event_bus.listeners), 1)
    
    def test_publish(self):
        """
        Test publishing an event to the event bus.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        self.event_bus.subscribe(callback, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        self.event_bus.publish(event)
        
        callback.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    def test_publish_event_type_and_data(self):
        """
        Test publishing an event type and data to the event bus.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        self.event_bus.subscribe(callback, event_types)
        
        event_type = "test_event"
        data = {"key": "value"}
        
        self.event_bus.publish_event(event_type, data)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.data, data)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0].event_type, event_type)
        self.assertEqual(self.event_bus.event_history[0].data, data)
    
    def test_publish_no_matching_listeners(self):
        """
        Test publishing an event with no matching listeners.
        """
        callback = MagicMock()
        event_types = ["test_event"]
        
        self.event_bus.subscribe(callback, event_types)
        
        event = Event("other_event", {"key": "value"})
        
        self.event_bus.publish(event)
        
        callback.assert_not_called()
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    def test_publish_multiple_listeners(self):
        """
        Test publishing an event to multiple listeners.
        """
        callback1 = MagicMock()
        callback2 = MagicMock()
        event_types = ["test_event"]
        
        self.event_bus.subscribe(callback1, event_types)
        self.event_bus.subscribe(callback2, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        self.event_bus.publish(event)
        
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    def test_publish_listener_exception(self):
        """
        Test publishing an event where a listener raises an exception.
        """
        callback1 = MagicMock(side_effect=Exception("Test exception"))
        callback2 = MagicMock()
        event_types = ["test_event"]
        
        self.event_bus.subscribe(callback1, event_types)
        self.event_bus.subscribe(callback2, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        # Capture logging output
        with self.assertLogs(level=logging.ERROR) as log:
            self.event_bus.publish(event)
            
            # Check that the exception was logged
            self.assertIn("Error notifying listener", log.output[0])
            self.assertIn("Test exception", log.output[0])
        
        # Check that the second listener was still called
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    async def async_test_publish_async(self):
        """
        Test publishing an event to async listeners.
        """
        # Create a mock async callback
        async def async_callback(event):
            pass
        
        callback = MagicMock(side_effect=async_callback)
        event_types = ["test_event"]
        
        self.event_bus.subscribe_async(callback, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        await self.event_bus.publish_async(event)
        
        callback.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    async def async_test_publish_event_async(self):
        """
        Test publishing an event type and data to async listeners.
        """
        # Create a mock async callback
        async def async_callback(event):
            pass
        
        callback = MagicMock(side_effect=async_callback)
        event_types = ["test_event"]
        
        self.event_bus.subscribe_async(callback, event_types)
        
        event_type = "test_event"
        data = {"key": "value"}
        
        await self.event_bus.publish_event_async(event_type, data)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.data, data)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0].event_type, event_type)
        self.assertEqual(self.event_bus.event_history[0].data, data)
    
    async def async_test_publish_async_no_matching_listeners(self):
        """
        Test publishing an event with no matching async listeners.
        """
        # Create a mock async callback
        async def async_callback(event):
            pass
        
        callback = MagicMock(side_effect=async_callback)
        event_types = ["test_event"]
        
        self.event_bus.subscribe_async(callback, event_types)
        
        event = Event("other_event", {"key": "value"})
        
        await self.event_bus.publish_async(event)
        
        callback.assert_not_called()
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    async def async_test_publish_async_multiple_listeners(self):
        """
        Test publishing an event to multiple async listeners.
        """
        # Create mock async callbacks
        async def async_callback1(event):
            pass
        
        async def async_callback2(event):
            pass
        
        callback1 = MagicMock(side_effect=async_callback1)
        callback2 = MagicMock(side_effect=async_callback2)
        event_types = ["test_event"]
        
        self.event_bus.subscribe_async(callback1, event_types)
        self.event_bus.subscribe_async(callback2, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        await self.event_bus.publish_async(event)
        
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    async def async_test_publish_async_listener_exception(self):
        """
        Test publishing an event where an async listener raises an exception.
        """
        # Create mock async callbacks
        async def async_callback1(event):
            raise Exception("Test exception")
        
        async def async_callback2(event):
            pass
        
        callback1 = MagicMock(side_effect=async_callback1)
        callback2 = MagicMock(side_effect=async_callback2)
        event_types = ["test_event"]
        
        self.event_bus.subscribe_async(callback1, event_types)
        self.event_bus.subscribe_async(callback2, event_types)
        
        event = Event("test_event", {"key": "value"})
        
        # Capture logging output
        with self.assertLogs(level=logging.ERROR) as log:
            await self.event_bus.publish_async(event)
            
            # Check that the exception was logged
            self.assertIn("Error notifying async listener", log.output[0])
            self.assertIn("Test exception", log.output[0])
        
        # Check that the second listener was still called
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0], event)
    
    def test_get_event_history(self):
        """
        Test getting the event history.
        """
        event1 = Event("test_event_1", {"key": "value1"})
        event2 = Event("test_event_2", {"key": "value2"})
        
        self.event_bus.publish(event1)
        self.event_bus.publish(event2)
        
        history = self.event_bus.get_event_history()
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], event1)
        self.assertEqual(history[1], event2)
    
    def test_get_event_history_by_type(self):
        """
        Test getting the event history filtered by event type.
        """
        event1 = Event("test_event_1", {"key": "value1"})
        event2 = Event("test_event_2", {"key": "value2"})
        event3 = Event("test_event_1", {"key": "value3"})
        
        self.event_bus.publish(event1)
        self.event_bus.publish(event2)
        self.event_bus.publish(event3)
        
        history = self.event_bus.get_event_history_by_type("test_event_1")
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], event1)
        self.assertEqual(history[1], event3)
    
    def test_clear_event_history(self):
        """
        Test clearing the event history.
        """
        event1 = Event("test_event_1", {"key": "value1"})
        event2 = Event("test_event_2", {"key": "value2"})
        
        self.event_bus.publish(event1)
        self.event_bus.publish(event2)
        
        self.assertEqual(len(self.event_bus.event_history), 2)
        
        self.event_bus.clear_event_history()
        
        self.assertEqual(len(self.event_bus.event_history), 0)
    
    def test_max_history_size(self):
        """
        Test that the event history is limited to the maximum size.
        """
        # Set a small max history size
        self.event_bus.max_history_size = 2
        
        event1 = Event("test_event_1", {"key": "value1"})
        event2 = Event("test_event_2", {"key": "value2"})
        event3 = Event("test_event_3", {"key": "value3"})
        
        self.event_bus.publish(event1)
        self.event_bus.publish(event2)
        self.event_bus.publish(event3)
        
        self.assertEqual(len(self.event_bus.event_history), 2)
        self.assertEqual(self.event_bus.event_history[0], event2)
        self.assertEqual(self.event_bus.event_history[1], event3)
    
    def test_publish_async(self):
        """
        Test the publish_async method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_publish_async())
        finally:
            loop.close()
    
    def test_publish_event_async(self):
        """
        Test the publish_event_async method.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_publish_event_async())
        finally:
            loop.close()
    
    def test_publish_async_no_matching_listeners(self):
        """
        Test the publish_async method with no matching listeners.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_publish_async_no_matching_listeners())
        finally:
            loop.close()
    
    def test_publish_async_multiple_listeners(self):
        """
        Test the publish_async method with multiple listeners.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_publish_async_multiple_listeners())
        finally:
            loop.close()
    
    def test_publish_async_listener_exception(self):
        """
        Test the publish_async method with a listener that raises an exception.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_test_publish_async_listener_exception())
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
