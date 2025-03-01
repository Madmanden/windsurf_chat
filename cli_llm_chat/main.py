#!/usr/bin/env python3
"""
CLI LLM Chat App
A command-line interface for chatting with LLMs using the OpenRouter API.
"""

import typer
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional, List, Dict, Any
import requests
import os
from cli_llm_chat.ui.formatter import format_message, format_user_message
from cli_llm_chat.ui.terminal import TerminalUI

from cli_llm_chat.api.openrouter import OpenRouterClient
from cli_llm_chat.config.settings import (
    get_config_dir,
    load_config,
    save_config,
    get_api_key,
    validate_api_key,
    save_conversation,
    load_conversation,
    list_conversations
)

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from pathlib import Path

# Create Typer app
app = typer.Typer(
    help="CLI LLM Chat - A command-line interface for chatting with LLMs via OpenRouter",
    add_completion=False
)

# Initialize console
console = Console()

# Global state
conversation_history = {}

@app.command()
def chat(
    message: Optional[str] = typer.Option(None, "--message", "-m", "-msg", help="Single message to send (non-interactive mode)"),
    model: str = typer.Option(None, "--model", help="Model to use for chat"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", "-temp", help="Temperature for response generation"),
    max_tokens: int = typer.Option(1000, "--max-tokens", help="Maximum tokens in response"),
    debug: bool = typer.Option(False, "--debug", help="Show debug information"),
    conversation: str = typer.Option(None, "--conversation", "-c", "-conv", help="Name of the conversation to continue or create"),
):
    """
    Start a chat session with an LLM
    """
    global conversation_history
    
    # Load configuration
    config = load_config()
    
    # Get API key
    api_key = get_api_key(config)
    if not api_key:
        console.print("[bold red]Error:[/bold red] API key not found. Please set it using the config command or OPENROUTER_API_KEY environment variable.")
        raise typer.Exit(1)
    
    # Validate API key format
    if not validate_api_key(api_key):
        console.print("[bold red]Error:[/bold red] Invalid API key format. Please check your API key.")
        raise typer.Exit(1)
    
    # Set model from config if not provided
    if not model:
        model = config.get("default_model", "google/gemini-2.0-flash-001")
    
    # Initialize API client
    client = OpenRouterClient(api_key)
    
    # Set conversation name
    if not conversation:
        conversation = "default"
    
    # Initialize conversation history if not exists
    if conversation not in conversation_history:
        # Try to load from saved conversations
        loaded_messages = load_conversation(conversation)
        if loaded_messages:
            conversation_history[conversation] = loaded_messages
            console.print(f"Loaded conversation: {conversation}")
        else:
            # Set up new conversation with system message
            verbosity = config.get("verbosity", "medium")
            system_message = {
                "short": "You are a helpful AI assistant. IMPORTANT: Always provide concise responses of 1-5 lines maximum. Keep explanations minimal and focused.",
                "medium": "You are a helpful AI assistant. IMPORTANT: Provide balanced responses between 5-15 lines. Include key details and brief examples while maintaining clarity.",
                "long": "You are a helpful AI assistant. IMPORTANT: Provide comprehensive responses with detailed explanations, relevant examples, and thorough context. Focus on depth and completeness."
            }[verbosity]
            
            conversation_history[conversation] = [
                {"role": "system", "content": system_message}
            ]
    
    # Handle single message mode
    if message:
        # Add user message to history
        conversation_history[conversation].append({"role": "user", "content": message})
        
        try:
            # Get response from API
            with console.status("[bold green]Thinking...[/bold green]"):
                response = client.chat_completion(
                    model=model,
                    messages=conversation_history[conversation],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    debug=debug
                )
            
            assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Display formatted response
            console.print("\n")
            verbosity = config.get("verbosity", "medium")
            formatted_message = format_message(assistant_message, verbosity=verbosity)
            console.print(formatted_message)
            
            # Add assistant message to history
            conversation_history[conversation].append({"role": "assistant", "content": assistant_message})
            
            # Save conversation
            if conversation:
                save_conversation(conversation, conversation_history[conversation])
            
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        
        return
    
    # Interactive mode
    terminal = TerminalUI()
    
    def handle_input(user_input, conversation_history=conversation_history, conversation=conversation):
        
        # Handle special commands
        if user_input.lower() == "/clear":
            conversation_history[conversation] = []
            terminal.append_message("System", "Conversation history cleared.")
            return
        elif user_input.lower() == "/help":
            help_text = """
Available commands:
  /exit - Exit the chat session
  /clear - Clear conversation history
  /save <name> - Save the current conversation
  /list - List all saved conversations
  /load <name> - Load a saved conversation
  /help - Show this help message"""
            terminal.append_message("System", help_text)
            return
        elif user_input.lower().startswith("/save "):
            new_name = user_input[6:].strip()
            if new_name:
                save_conversation(new_name, conversation_history[conversation])
                conversation = new_name
                terminal.append_message("System", f"Conversation saved as: {new_name}")
            else:
                terminal.append_message("System", "Please provide a name for the conversation")
            return
        elif user_input.lower() == "/list":
            conversations = list_conversations()
            if conversations:
                terminal.append_message("System", "Saved conversations:\n" + "\n".join(f"  {conv}" for conv in conversations))
            else:
                terminal.append_message("System", "No saved conversations found.")
            return
        elif user_input.lower().startswith("/load "):
            conv_name = user_input[6:].strip()
            if conv_name:
                loaded_messages = load_conversation(conv_name)
                if loaded_messages:
                    conversation = conv_name
                    conversation_history[conversation] = loaded_messages
                    terminal.append_message("System", f"Loaded conversation: {conv_name} with {len(loaded_messages)} messages")
                else:
                    terminal.append_message("System", f"Conversation not found: {conv_name}")
            else:
                terminal.append_message("System", "Please provide a name of the conversation to load")
            return
        
        # Add user message to history
        conversation_history[conversation].append({"role": "user", "content": user_input})
        
        try:
            # Get response from API
            response = client.chat_completion(
                model=model,
                messages=conversation_history[conversation],
                temperature=temperature,
                max_tokens=max_tokens,
                debug=debug
            )
            
            assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Add assistant message to history
            conversation_history[conversation].append({"role": "assistant", "content": assistant_message})
            
            # Save conversation after each message
            save_conversation(conversation, conversation_history[conversation])
            
            # Display formatted response
            terminal.append_message("Assistant", assistant_message)
            
        except Exception as e:
            terminal.append_message("System", f"Error: {str(e)}")
    
    try:
        terminal.run(on_input=handle_input)
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting chat...[/yellow]")
    except EOFError:
        console.print("\n[yellow]Exiting chat...[/yellow]")

@app.command()
def config_set(
    api_key: str = typer.Option(
        None, "--api-key", help="OpenRouter API key (use 'keep' to keep current value)"
    ),
    default_model: str = typer.Option(
        None, "--default-model", help="Default model to use"
    ),
    verbosity: str = typer.Option(
        None, "--verbosity", "-v",
        help="Set response length: 'short' (1-5 lines), 'medium' (5-15 lines), or 'long' (detailed explanations)"
    ),
):
    """
    Set configuration values
    """
    # Load existing config
    config = load_config()
    
    # Update API key if provided
    if api_key is not None:
        if api_key.lower() == "keep" and "api_key" in config:
            console.print("Keeping existing API key")
        else:
            # Validate API key format
            if not validate_api_key(api_key):
                console.print("[bold red]Error:[/bold red] Invalid API key format. Please check your API key.")
                raise typer.Exit(1)
            
            config["api_key"] = api_key
            console.print("API key updated")
    
    # Update default model if provided
    if default_model is not None:
        config["default_model"] = default_model
        console.print(f"Default model set to: {default_model}")
    
    # Update verbosity if provided
    if verbosity is not None:
        if verbosity not in ["short", "medium", "long"]:
            console.print("[bold red]Error:[/bold red] Verbosity must be one of: 'short', 'medium', or 'long'")
            raise typer.Exit(1)
        
        config["verbosity"] = verbosity
        console.print(f"Verbosity set to: {verbosity}")
    
    # Save updated config
    save_config(config)
    
    # Display current configuration
    console.print("\nCurrent configuration:")
    
    # Display API key (masked)
    if "api_key" in config:
        masked_key = config["api_key"][:4] + "..." + config["api_key"][-4:]
        console.print(f"API key: {masked_key}")
    else:
        console.print("API key: [not set]")
    
    # Display default model
    console.print(f"Default model: {config.get('default_model', '[not set]')}")
    
    # Display verbosity
    console.print(f"Verbosity: {config.get('verbosity', 'medium')}")

@app.command()
def test_model(
    model: str = typer.Option("google/gemini-2.0-flash-001", help="Model to test"),
    message: str = typer.Option("Hello! Can you tell me what model you are?", help="Test message to send"),
    debug: bool = typer.Option(False, "--debug", help="Show debug information"),
):
    """
    Test a specific model with your API key
    """
    # Load configuration
    config = load_config()
    
    # Get API key
    api_key = get_api_key(config)
    if not api_key:
        console.print("[bold red]Error:[/bold red] API key not found. Please set it using the config command or OPENROUTER_API_KEY environment variable.")
        raise typer.Exit(1)
    
    # Initialize API client
    client = OpenRouterClient(api_key)
    
    # Send test message
    console.print(f"Testing model: {model}")
    console.print(f"Message: {message}")
    console.print("")
    
    try:
        # Get response from API
        with console.status("[bold green]Waiting for response...[/bold green]"):
            response = client.chat_completion(
                model=model,
                messages=[{"role": "user", "content": message}],
                debug=debug
            )
        
        # Display response
        assistant_message = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        console.print(Markdown(assistant_message))
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

@app.command()
def debug():
    """
    Run diagnostics to check API connectivity and configuration
    """
    console.print("[bold]Running diagnostics...[/bold]")
    
    # Check config directory
    config_dir = get_config_dir()
    console.print(f"Config directory: {config_dir}")
    if os.path.exists(config_dir):
        console.print("✅ Config directory exists")
    else:
        console.print("❌ Config directory does not exist")
    
    # Check config file
    config_file = os.path.join(config_dir, "config.json")
    console.print(f"Config file: {config_file}")
    if os.path.exists(config_file):
        console.print("✅ Config file exists")
        
        # Check if config file is valid JSON
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            console.print("✅ Config file is valid JSON")
            
            # Check if API key is set
            if "api_key" in config:
                masked_key = config["api_key"][:4] + "..." + config["api_key"][-4:]
                console.print(f"✅ API key is set: {masked_key}")
                
                # Validate API key format
                if validate_api_key(config["api_key"]):
                    console.print("✅ API key format is valid")
                else:
                    console.print("❌ API key format is invalid")
            else:
                console.print("❌ API key is not set in config file")
            
            # Check if default model is set
            if "default_model" in config:
                console.print(f"✅ Default model is set: {config['default_model']}")
            else:
                console.print("ℹ️ Default model is not set (will use default)")
            
            # Check if verbosity is set
            if "verbosity" in config:
                console.print(f"✅ Verbosity is set: {config['verbosity']}")
            else:
                console.print("ℹ️ Verbosity is not set (will use default)")
                
        except json.JSONDecodeError:
            console.print("❌ Config file is not valid JSON")
    else:
        console.print("❌ Config file does not exist")
    
    # Check environment variable
    env_api_key = os.environ.get("OPENROUTER_API_KEY")
    if env_api_key:
        masked_key = env_api_key[:4] + "..." + env_api_key[-4:]
        console.print(f"✅ OPENROUTER_API_KEY environment variable is set: {masked_key}")
        
        # Validate API key format
        if validate_api_key(env_api_key):
            console.print("✅ Environment API key format is valid")
        else:
            console.print("❌ Environment API key format is invalid")
    else:
        console.print("ℹ️ OPENROUTER_API_KEY environment variable is not set")
    
    # Test API connectivity
    api_key = get_api_key(load_config())
    if api_key:
        try:
            client = OpenRouterClient(api_key)
            with console.status("[bold green]Testing API connectivity...[/bold green]"):
                models = client.list_models()
            console.print(f"✅ API connectivity test successful: {len(models)} models available")
        except Exception as e:
            console.print(f"❌ API connectivity test failed: {str(e)}")
    else:
        console.print("❌ Cannot test API connectivity: No API key available")

@app.command()
def models(limit: int = typer.Option(20, help="Maximum number of models to display")):
    """
    List available models from OpenRouter API
    """
    # Load configuration
    config = load_config()
    
    # Get API key
    api_key = get_api_key(config)
    if not api_key:
        console.print("[bold red]Error:[/bold red] API key not found. Please set it using the config command or OPENROUTER_API_KEY environment variable.")
        raise typer.Exit(1)
    
    # Initialize API client
    client = OpenRouterClient(api_key)
    
    # Get models
    try:
        with console.status("[bold green]Fetching models...[/bold green]"):
            models_list = client.list_models()
        
        # Sort models by id
        models_list.sort(key=lambda x: x.get("id", ""))
        
        # Limit number of models
        models_list = models_list[:limit]
        
        # Display models
        console.print(f"[bold]Available models ({len(models_list)}):[/bold]")
        for model in models_list:
            model_id = model.get("id", "Unknown")
            context_length = model.get("context_length", "Unknown")
            pricing = model.get("pricing", {})
            input_price = pricing.get("input", 0)
            output_price = pricing.get("output", 0)
            
            # Format pricing per million tokens
            input_price_formatted = f"${input_price:.5f}" if input_price else "Unknown"
            output_price_formatted = f"${output_price:.5f}" if output_price else "Unknown"
            
            console.print(f"[bold]{model_id}[/bold]")
            console.print(f"  Context length: {context_length} tokens")
            console.print(f"  Pricing (per token): Input {input_price_formatted} / Output {output_price_formatted}")
            console.print("")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    app()
