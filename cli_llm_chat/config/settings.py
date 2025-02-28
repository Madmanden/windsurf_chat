"""
Configuration management for CLI LLM Chat
Handles loading, saving, and managing user configuration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def get_config_dir() -> Path:
    """
    Get the configuration directory path
    
    Returns:
        Path to the configuration directory
    """
    # Use XDG_CONFIG_HOME if available, otherwise use ~/.config
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        base_dir = Path(config_home)
    else:
        base_dir = Path.home() / ".config"
    
    # Create app-specific config directory
    config_dir = base_dir / "cli-llm-chat"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir


def get_config_file() -> Path:
    """
    Get the configuration file path
    
    Returns:
        Path to the configuration file
    """
    return get_config_dir() / "config.json"


DEFAULT_CONFIG = {
    "response_verbosity": "brief",  # 'brief' or 'detailed'
    "api_key": None,
    "default_model": "google/gemini-2.0-flash-001",
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file
    
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # First try to load from .env file
    load_dotenv()
    
    # Check for environment variables
    api_key = os.environ.get("OPENROUTER_API_KEY")
    default_model = os.environ.get("DEFAULT_MODEL")
    response_verbosity = os.environ.get("RESPONSE_VERBOSITY")
    
    if api_key:
        config["api_key"] = api_key
    
    if default_model:
        config["default_model"] = default_model
    
    if response_verbosity:
        config["response_verbosity"] = response_verbosity
    
    # Then try to load from config file (overrides env vars)
    config_file = get_config_file()
    
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
    
    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file
    
    Args:
        config: Configuration dictionary to save
    """
    config_file = get_config_file()
    
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving configuration: {e}")


def get_conversation_dir() -> Path:
    """
    Get the directory for storing conversation history
    
    Returns:
        Path to the conversation directory
    """
    data_dir = get_config_dir() / "conversations"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def save_conversation(conversation_id: str, messages: list) -> None:
    """
    Save a conversation to a file
    
    Args:
        conversation_id: Unique identifier for the conversation
        messages: List of message objects
    """
    conv_dir = get_conversation_dir()
    conv_file = conv_dir / f"{conversation_id}.json"
    
    try:
        with open(conv_file, "w") as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")


def load_conversation(conversation_id: str) -> list:
    """
    Load a conversation from a file
    
    Args:
        conversation_id: Unique identifier for the conversation
        
    Returns:
        List of message objects
    """
    conv_dir = get_conversation_dir()
    conv_file = conv_dir / f"{conversation_id}.json"
    
    if not conv_file.exists():
        return []
    
    try:
        with open(conv_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading conversation: {e}")
        return []


def list_conversations() -> list:
    """
    List all saved conversations
    
    Returns:
        List of conversation IDs
    """
    conv_dir = get_conversation_dir()
    
    if not conv_dir.exists():
        return []
    
    return [f.stem for f in conv_dir.glob("*.json")]
