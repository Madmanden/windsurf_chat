"""
Message formatting utilities for the CLI LLM Chat UI
"""

import re
from rich.markdown import Markdown
from rich.text import Text
from rich.console import Console


def format_message(message: str) -> Markdown:
    """
    Format a message for display in the terminal
    
    Args:
        message: The message text to format
        
    Returns:
        Formatted message as a Rich Markdown object
    """
    # Process the message as markdown
    return Markdown(message)


def format_code_blocks(message: str) -> str:
    """
    Enhance code block formatting in messages
    
    Args:
        message: The message text to format
        
    Returns:
        Message with enhanced code block formatting
    """
    # Replace triple backtick code blocks with Rich syntax
    pattern = r"```(\w+)?\n(.*?)```"
    
    def replace_code_block(match):
        language = match.group(1) or ""
        code = match.group(2)
        return f"\n[bold purple]```{language}[/bold purple]\n[dim]{code}[/dim]\n[bold purple]```[/bold purple]"
    
    return re.sub(pattern, replace_code_block, message, flags=re.DOTALL)


def truncate_message(message: str, max_length: int = 1000) -> str:
    """
    Truncate a message if it exceeds the maximum length
    
    Args:
        message: The message to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated message
    """
    if len(message) <= max_length:
        return message
    
    return message[:max_length] + "... [italic](message truncated)[/italic]"
