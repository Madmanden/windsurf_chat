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
    
    # Process code blocks first
    message = format_code_blocks(message)
    
    # Convert message to Markdown
    md = Markdown(message, code_theme="monokai", hyperlinks=True)
    
    return Panel(
        md,
        border_style="blue",
        title=f"Assistant ({verbosity.title()})",
        title_align="left",
        style=style,
        padding=(1, 2)
    )

def format_user_message(message: str, include_prompt: bool = False) -> str:
    """Format user message with a distinct style"""
    # Create a temporary console for rendering
    temp_console = Console(record=True)
    temp_console.print(message)
    content = temp_console.export_text()
    
    panel = Panel(
        content.strip(),
        border_style="yellow",
        title="User",
        title_align="left",
        style="yellow",
        padding=(1, 2)
    )
    
    return str(panel)


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
        code = match.group(2).strip()
        # Keep the markdown format but ensure proper spacing
        return f"\n```{language}\n{code}\n```\n"
    
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
