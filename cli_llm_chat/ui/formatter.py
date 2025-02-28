"""
Message formatting utilities for the CLI LLM Chat UI
"""

import re
from rich.markdown import Markdown
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax


def format_message(message: str, verbosity: str = "brief") -> Panel:
    """
    Format a message for display in the terminal
    
    Args:
        message: The message text to format
        verbosity: The level of verbosity for the message
        
    Returns:
        Formatted message as a Rich Panel object
    """
    style = Style(color="green", bold=False)
    
    if verbosity == "brief":
        content = message.strip()
    else:
        content = str(Markdown(f"**Detailed Response:**\n\n{message}"))
    
    return Panel(
        content,
        border_style="blue",
        title="Assistant" if verbosity == "brief" else "Assistant (Detailed)",
        title_align="left",
        style=style
    )

def format_user_message(message: str) -> Panel:
    """Format user message with a distinct style"""
    return Panel(
        message,
        border_style="yellow",
        title="User",
        title_align="left",
        style="yellow"
    )


def format_code_blocks(message: str) -> str:
    """
    Enhance code block formatting in messages
    
    Args:
        message: The message text to format
        
    Returns:
        Message with enhanced code block formatting
    """
    # Replace triple backtick code blocks with Rich syntax highlighting
    pattern = r"```(\w+)?\n(.*?)```"
    
    def replace_code_block(match):
        language = match.group(1) or "text"
        code = match.group(2)
        syntax = Syntax(code.strip(), language, theme="monokai", line_numbers=True)
        return f"\n{syntax}\n"
    
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
