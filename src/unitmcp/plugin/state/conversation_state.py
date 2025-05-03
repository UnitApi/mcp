"""
Conversation state management for UnitMCP Claude Plugin.

This module provides functionality to track conversation context
and device references across multi-turn interactions.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class ConversationStateManager:
    """
    Manages conversation state for the Claude UnitMCP plugin.
    
    This class tracks conversation context, device references,
    and recent operations to improve command interpretation.
    """
    
    def __init__(self):
        self.conversations = {}
        
    def update(self, query: Dict[str, Any]):
        """
        Update the conversation state with a new query.
        
        Args:
            query: Dictionary containing the query information
                - text: The text of the query
                - user_id: Identifier for the user
                - conversation_id: Identifier for the conversation
        """
        conversation_id = query.get("conversation_id", "default")
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "recent_devices": [],
                "recent_actions": [],
                "context": {},
                "history": []
            }
            
        # Update history
        self.conversations[conversation_id]["history"].append({
            "text": query["text"],
            "timestamp": datetime.now().isoformat(),
            "user_id": query.get("user_id", "unknown")
        })
        
        logger.debug(f"Updated conversation state for {conversation_id}")
        
    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the context for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            
        Returns:
            A dictionary containing the conversation context
        """
        return self.conversations.get(conversation_id, {}).get("context", {})
        
    def update_device_reference(self, conversation_id: str, device_id: str):
        """
        Update the recent device references for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            device_id: Identifier for the device
        """
        if conversation_id not in self.conversations:
            return
            
        recent_devices = self.conversations[conversation_id]["recent_devices"]
        
        # Remove existing reference to the device
        recent_devices = [d for d in recent_devices if d != device_id]
        
        # Add the device to the front of the list
        recent_devices.insert(0, device_id)
        
        # Keep only the 5 most recent devices
        self.conversations[conversation_id]["recent_devices"] = recent_devices[:5]
        
        logger.debug(f"Updated device reference for {conversation_id}: {device_id}")
    
    def update_action_reference(self, conversation_id: str, action: str):
        """
        Update the recent action references for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            action: The action that was performed
        """
        if conversation_id not in self.conversations:
            return
            
        recent_actions = self.conversations[conversation_id]["recent_actions"]
        
        # Remove existing reference to the action
        recent_actions = [a for a in recent_actions if a != action]
        
        # Add the action to the front of the list
        recent_actions.insert(0, action)
        
        # Keep only the 5 most recent actions
        self.conversations[conversation_id]["recent_actions"] = recent_actions[:5]
        
        logger.debug(f"Updated action reference for {conversation_id}: {action}")
    
    def update_context(self, conversation_id: str, key: str, value: Any):
        """
        Update a specific context value for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            key: The context key to update
            value: The value to set
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "recent_devices": [],
                "recent_actions": [],
                "context": {},
                "history": []
            }
            
        self.conversations[conversation_id]["context"][key] = value
        
        logger.debug(f"Updated context for {conversation_id}: {key}={value}")
    
    def get_recent_devices(self, conversation_id: str) -> List[str]:
        """
        Get the recent device references for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            
        Returns:
            A list of recent device IDs
        """
        return self.conversations.get(conversation_id, {}).get("recent_devices", [])
    
    def get_recent_actions(self, conversation_id: str) -> List[str]:
        """
        Get the recent action references for a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            
        Returns:
            A list of recent actions
        """
        return self.conversations.get(conversation_id, {}).get("recent_actions", [])
    
    def get_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            conversation_id: Identifier for the conversation
            limit: Maximum number of history items to return
            
        Returns:
            A list of conversation history items
        """
        history = self.conversations.get(conversation_id, {}).get("history", [])
        return history[-limit:] if limit > 0 else history
