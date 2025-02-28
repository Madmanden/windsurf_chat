"""
Helper utilities for CLI LLM Chat
"""

import uuid
import datetime
from typing import Dict, List, Any


def generate_conversation_id() -> str:
    """
    Generate a unique ID for a new conversation
    
    Returns:
        Unique conversation ID
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def format_timestamp(timestamp: float) -> str:
    """
    Format a Unix timestamp as a human-readable date/time
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted date/time string
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def count_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string
    This is a very rough approximation (about 4 chars per token)
    
    Args:
        text: Text to count tokens for
        
    Returns:
        Estimated token count
    """
    return len(text) // 4
