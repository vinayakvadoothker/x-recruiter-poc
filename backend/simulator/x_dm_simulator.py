"""
X DM Simulator - Simple message handler.

Provides a simple interface for managing chat history.
Can be easily swapped for real X API when available.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class XDMSimulator:
    """
    Simulates X DM interface for hackathon demo.
    
    Simple message handler that stores chat history.
    Designed to be easily replaced with real X API client.
    """
    
    def __init__(self):
        """Initialize simulator with empty chat history."""
        self.chat_history: List[Dict] = []
    
    def send_message(self, message: str, sender: str = "user") -> None:
        """
        Add a message to chat history.
        
        Args:
            message: Message text
            sender: Sender identifier ("user" for recruiter, "assistant" for @x_recruiting)
        """
        chat_entry = {
            'role': sender,
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        self.chat_history.append(chat_entry)
        logger.debug(f"Message added from {sender}: {message[:50]}...")
    
    def receive_message(self, message: str) -> None:
        """
        Add a system response message to chat history.
        
        Args:
            message: Response message from @x_recruiting
        """
        self.send_message(message, sender="assistant")
    
    def get_chat_history(self) -> List[Dict]:
        """
        Get full chat history.
        
        Returns:
            List of message dictionaries with role, content, and timestamp
        """
        return self.chat_history.copy()
    
    def display_chat(self) -> None:
        """
        Display chat history in CLI format.
        
        Useful for testing and demo purposes.
        """
        if not self.chat_history:
            print("No messages yet.")
            return
        
        print("\n" + "=" * 60)
        print("X DM Chat History")
        print("=" * 60)
        
        for msg in self.chat_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            # Format role display
            if role == "user":
                prefix = "You:"
            elif role == "assistant":
                prefix = "@x_recruiting:"
            else:
                prefix = f"{role}:"
            
            print(f"\n{prefix}")
            print(f"  {content}")
            if timestamp:
                print(f"  [{timestamp}]")
        
        print("\n" + "=" * 60)
    
    def clear_history(self) -> None:
        """Clear all chat history."""
        self.chat_history = []
        logger.info("Chat history cleared")
    
    def get_last_message(self) -> Optional[Dict]:
        """
        Get the last message from chat history.
        
        Returns:
            Last message dictionary or None if history is empty
        """
        return self.chat_history[-1] if self.chat_history else None
    
    def get_messages_by_role(self, role: str) -> List[Dict]:
        """
        Get all messages from a specific role.
        
        Args:
            role: Role to filter by ("user" or "assistant")
        
        Returns:
            List of message dictionaries matching the role
        """
        return [msg for msg in self.chat_history if msg.get('role') == role]

