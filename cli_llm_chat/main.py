#!/usr/bin/env python3
"""
CLI LLM Chat App
A command-line interface for chatting with LLMs using the OpenRouter API.
"""

import os
import json
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional, List, Dict, Any
import requests
import os
from cli_llm_chat.ui.formatter import format_message, format_user_message

from cli_llm_chat.api.openrouter import OpenRouterClient
from cli_llm_chat.config.settings import (
    load_config, 
    save_config, 
    save_conversation, 
    load_conversation, 
    list_conversations,
    get_config_file,
    get_config_dir
)
import uuid
import dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path

# Load environment variables
dotenv.load_dotenv()

# Initialize Typer app
app = typer.Typer(
    help="CLI LLM Chat - A command-line interface for chatting with LLMs via OpenRouter",
    add_completion=False,
)

# Initialize Rich console
console = Console()

# Load configuration
config = load_config()

# Define callback for no command provided (default to chat)
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    message: Optional[str] = typer.Option(None, "--message", "-m", "-msg", help="Single message to send (non-interactive mode)"),
    model: str = typer.Option(None, "--model", help="Model to use for chat"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", "-temp", help="Temperature for response generation"),
    max_tokens: int = typer.Option(1000, "--max-tokens", help="Maximum tokens in response"),
    debug: bool = typer.Option(False, "--debug", help="Show debug information"),
    conversation: str = typer.Option(None, "--conversation", "-c", "-conv", help="Name of the conversation to continue or create"),
):
    """CLI LLM Chat - A command-line interface for chatting with LLMs via OpenRouter"""
    # If no command is provided, run the chat command
    if ctx.invoked_subcommand is None:
        chat(message=message, model=model, temperature=temperature, max_tokens=max_tokens, debug=debug, conversation=conversation)

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
    global conversation_history, config
    
    # Reload config to get latest settings
    config = load_config()
    
    # Get API key from config
    api_key = config.get("api_key") or os.getenv("OPENROUTER_API_KEY", "")
    
    if not api_key:
        console.print("[bold red]Error:[/bold red] API key not found. Please set it using the config_set command.")
        return
    
    # Use default model if not specified
    if not model:
        model = config.get("default_model", "google/gemini-2.0-flash-001")
    
    # Initialize OpenRouter client
    client = OpenRouterClient(api_key=api_key)
    
    # Display chat session info
    console.print(Panel(f"Chat session started with model: {model}", 
                       title="CLI LLM Chat", 
                       border_style="blue"))
    
    # Generate a conversation ID if not provided
    if conversation and conversation not in conversation_history:
        # Try to load existing conversation
        loaded_messages = load_conversation(conversation)
        if loaded_messages:
            conversation_history[conversation] = loaded_messages
            console.print(f"[bold green]Loaded conversation:[/bold green] {conversation} with {len(loaded_messages)} messages")
        else:
            conversation_history[conversation] = []
    elif conversation is None:
        # Generate a random ID for this conversation
        conversation = str(uuid.uuid4())[:8]
        conversation_history[conversation] = []
    
    # Add system message if starting new conversation
    if not conversation_history[conversation]:
        verbosity = config.get("verbosity", "medium")
        if debug:
            console.print(f"[yellow]Current verbosity setting: {verbosity}[/yellow]")
            
        system_message = {
            "short": "You are a helpful AI assistant. IMPORTANT: Always provide concise responses of 1-5 lines maximum. Keep explanations minimal and focused.",
            "medium": "You are a helpful AI assistant. IMPORTANT: Provide balanced responses between 5-15 lines. Include key details and brief examples while maintaining clarity.",
            "long": "You are a helpful AI assistant. IMPORTANT: Provide comprehensive responses with detailed explanations, relevant examples, and thorough context. Focus on depth and completeness."
        }[verbosity]
        conversation_history[conversation].append({
            "role": "system",
            "content": system_message
        })
    
    # Single message mode
    if message:
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
            console.print(format_message(assistant_message, verbosity=verbosity))
            
            # Add assistant message to history
            conversation_history[conversation].append({"role": "assistant", "content": assistant_message})
            
            # Save conversation
            if conversation:
                save_conversation(conversation, conversation_history[conversation])
            
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        
        return
    
    # Interactive mode
    console.print("\nType your messages below. Type /exit to end the session, /clear to clear history, or /help for more commands.")
    
    # Set up command history
    history_file = Path(get_config_dir()) / "command_history"
    session = PromptSession(history=FileHistory(str(history_file)))
    
    while True:
        # Get user input with history support
        console.print("\n")
        try:
            user_input = session.prompt("[Type your message here...] > ")
        
        # Handle special commands
        if user_input.lower() == "/exit":
            console.print("Exiting chat session...", style="yellow")
            break
        elif user_input.lower() == "/clear":
            conversation_history[conversation] = []
            console.print("Conversation history cleared.", style="yellow")
            continue
        elif user_input.lower() == "/help":
            console.print("Available commands:", style="yellow")
            console.print("  /exit - Exit the chat session", style="yellow")
            console.print("  /clear - Clear conversation history", style="yellow")
            console.print("  /save <name> - Save the current conversation with a name", style="yellow")
            console.print("  /list - List all saved conversations", style="yellow")
            console.print("  /load <name> - Load a saved conversation", style="yellow")
            console.print("  /help - Show this help message", style="yellow")
            continue
        elif user_input.lower().startswith("/save "):
            new_name = user_input[6:].strip()
            if new_name:
                # Save under the new name
                save_conversation(new_name, conversation_history[conversation])
                # Update the current conversation name
                conversation = new_name
                console.print(f"Conversation saved as: {new_name}", style="green")
            else:
                console.print("Please provide a name for the conversation", style="red")
            continue
        elif user_input.lower().startswith("/verbosity ") or user_input.lower() in ["/vs", "/vm", "/vl"]:
            # Handle shortcut commands
            if user_input.lower() == "/vs":
                new_verbosity = "short"
            elif user_input.lower() == "/vm":
                new_verbosity = "medium"
            elif user_input.lower() == "/vl":
                new_verbosity = "long"
            else:
                new_verbosity = user_input[10:].strip().lower()
                
            if new_verbosity in ["short", "medium", "long"]:
                config["verbosity"] = new_verbosity
                save_config(config)
                # Update system message for new verbosity
                system_message = {
                    "short": "You are a helpful AI assistant. IMPORTANT: Always provide concise responses of 1-5 lines maximum. Keep explanations minimal and focused.",
                    "medium": "You are a helpful AI assistant. IMPORTANT: Provide balanced responses between 5-15 lines. Include key details and brief examples while maintaining clarity.",
                    "long": "You are a helpful AI assistant. IMPORTANT: Provide comprehensive responses with detailed explanations, relevant examples, and thorough context. Focus on depth and completeness."
                }[new_verbosity]
                # Replace the first message (system message) with updated verbosity
                conversation_history[conversation][0] = {"role": "system", "content": system_message}
                console.print(f"Verbosity changed to: {new_verbosity}", style="green")
            else:
                console.print("Invalid verbosity level. Use 'short', 'medium', or 'long'", style="red")
            continue
        elif user_input.lower() == "/list":
            conversations = list_conversations()
            if conversations:
                console.print("Saved conversations:", style="yellow")
                for conv in conversations:
                    console.print(f"  {conv}", style="yellow")
            else:
                console.print("No saved conversations found.", style="yellow")
            continue
        elif user_input.lower().startswith("/load "):
            conv_name = user_input[6:].strip()
            if conv_name:
                loaded_messages = load_conversation(conv_name)
                if loaded_messages:
                    conversation = conv_name
                    conversation_history[conversation] = loaded_messages
                    console.print(f"Loaded conversation: {conv_name} with {len(loaded_messages)} messages", style="green")
                else:
                    console.print(f"Conversation not found: {conv_name}", style="red")
            else:
                console.print("Please provide a name of the conversation to load", style="red")
            continue
        
        # Add user message to history
        conversation_history[conversation].append({"role": "user", "content": user_input})
        
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
            
            # Add assistant message to history
            conversation_history[conversation].append({"role": "assistant", "content": assistant_message})
            
            # Save conversation after each message
            save_conversation(conversation, conversation_history[conversation])
            
            # Display formatted response
            console.print("\n")
            verbosity = config.get("verbosity", "medium")
            console.print(format_message(assistant_message, verbosity=verbosity))
            
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")


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
    """Set configuration values"""
    global config
    
    # Load current configuration
    current_config = load_config()
    
    # If API key is provided, validate it
    if api_key and api_key != 'keep':
        # Validate API key format
        if not api_key.startswith("sk-or-"):
            console.print("[yellow]Warning: API key does not start with 'sk-or-'[/yellow]")
            console.print("OpenRouter API keys typically start with 'sk-or-'")
            confirm = Prompt.ask("Do you want to continue with this API key?")
            if not confirm:
                console.print("Configuration not updated.")
                return
        
        # Test the API key
        try:
            console.print("Testing API key...")
            client = OpenRouterClient(api_key)
            models = client.list_models()
            console.print("[green]API key is valid![/green]")
        except Exception as e:
            console.print(f"[red]Error testing API key: {str(e)}[/red]")
            confirm = Prompt.ask("Do you want to save this API key anyway?")
            if not confirm:
                console.print("Configuration not updated.")
                return
    # If API key is 'keep', use the existing one
    elif api_key == 'keep':
        api_key = current_config.get('api_key')
    # If no API key is provided and we're not just updating other settings
    elif api_key is None and default_model is None and verbosity is None:
        api_key = Prompt.ask("Enter your OpenRouter API key", password=True)
    
    if default_model is None and api_key is not None and verbosity is None:
        default_model = Prompt.ask(
            "Enter default model", 
            default="google/gemini-2.0-flash-001"
        )
    
    # Update configuration
    if api_key is not None:
        config["api_key"] = api_key
        console.print("API key updated successfully!", style="green")
    
    if default_model is not None:
        config["default_model"] = default_model
        console.print(f"Default model set to: {default_model}", style="green")
    
    if verbosity is not None:
        if verbosity not in ["short", "medium", "long"]:
            console.print("Error: Verbosity must be 'short', 'medium', or 'long'", style="red")
            return
        config["verbosity"] = verbosity
        console.print(f"Verbosity set to: {verbosity}", style="green")
    
    # Save configuration
    save_config(config)
    
    # Display current configuration
    console.print(Panel("Current Configuration", border_style="blue"))
    
    # Safely display masked API key if it exists
    if config.get('api_key'):
        masked_key = f"****{config.get('api_key', '')[-4:]}" if len(config.get('api_key', '')) >= 4 else "****"
        console.print(f"API Key: {masked_key}")
    else:
        console.print("API Key: [dim]Not set[/dim]")
    
    console.print(f"Default Model: {config.get('default_model', '[dim]Not set[/dim]')}")
    console.print(f"Response Verbosity: {config.get('verbosity', '[dim]Not set[/dim]')}")


@app.command()
def test_model(
    model: str = typer.Option("google/gemini-2.0-flash-001", help="Model to test"),
    message: str = typer.Option("Hello! Can you tell me what model you are?", help="Test message to send"),
    debug: bool = typer.Option(False, "--debug", help="Show debug information"),
):
    """Test a specific model with your API key"""
    api_key = config.get("api_key")
    
    if not api_key:
        console.print("[red]Error: API key not set[/red]")
        console.print("Run [bold]llmchat config-set[/bold] to set your API key")
        return
    
    console.print(Panel(f"Testing model: {model}", border_style="blue"))
    
    try:
        client = OpenRouterClient(api_key)
        
        # Send a simple message to test the model
        messages = [{"role": "user", "content": message}]
        
        with console.status(f"[bold green]Sending request to {model}...[/bold green]"):
            response = client.chat_completion(model, messages, debug=debug)
        
        # Display the response
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            console.print("\n[bold green]Response:[/bold green]")
            console.print(content)
            console.print("\n[bold green]Success![/bold green] The model is working correctly.")
        else:
            console.print("[red]Error: Unexpected response format[/red]")
            console.print(f"Response: {response}")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print("\n[bold yellow]Troubleshooting suggestions:[/bold yellow]")
        console.print("1. Check that your API key is correct and active")
        console.print("2. Verify that the model ID is valid")
        console.print("3. Make sure you have access to the selected model")
        console.print("4. Check your internet connection")
        console.print("5. OpenRouter might be experiencing issues - check their status page")


@app.command()
def debug():
    """
    Run diagnostics to check API connectivity and configuration
    """
    console.print(Panel("CLI LLM Chat Diagnostics", border_style="blue"))
    
    # Check configuration
    console.print("[bold]Checking configuration...[/bold]")
    config_file = get_config_file()
    if config_file.exists():
        console.print(f"✅ Configuration file found at: {config_file}")
    else:
        console.print(f"❌ Configuration file not found at: {config_file}")
    
    # Check API key
    api_key = config.get("api_key")
    if api_key:
        masked_key = f"****{api_key[-4:]}" if len(api_key) >= 4 else "****"
        console.print(f"✅ API key is set (ending with {masked_key})")
        
        # Check API key format
        if api_key.startswith("sk-or-"):
            console.print("✅ API key has the correct format (starts with 'sk-or-')")
        else:
            console.print("❌ API key has incorrect format (should start with 'sk-or-')")
    else:
        console.print("❌ API key is not set")
    
    # Check default model
    default_model = config.get("default_model")
    if default_model:
        console.print(f"✅ Default model is set to: {default_model}")
    else:
        console.print("❌ Default model is not set")
    
    # Check response verbosity
    verbosity = config.get("verbosity")
    if verbosity:
        console.print(f"✅ Response verbosity is set to: {verbosity}")
    else:
        console.print("❌ Response verbosity is not set")
    
    # Test API connectivity
    if api_key:
        console.print("\n[bold]Testing API connectivity...[/bold]")
        try:
            with console.status("[bold green]Connecting to OpenRouter API...[/bold green]"):
                response = requests.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            
            if response.status_code == 200:
                console.print("✅ Successfully connected to OpenRouter API")
                models_count = len(response.json().get("data", []))
                console.print(f"✅ Retrieved {models_count} models from API")
            else:
                console.print(f"❌ Failed to connect to OpenRouter API (Status code: {response.status_code})")
                console.print(f"Response: {response.text}")
                
                # Provide troubleshooting advice
                console.print("\n[bold yellow]Troubleshooting suggestions:[/bold yellow]")
                console.print("1. Verify your API key is correct and active")
                console.print("2. Check your internet connection")
                console.print("3. OpenRouter might be experiencing issues - check their status page")
                console.print("4. Try setting a new API key with: llmchat config-set")
        except Exception as e:
            console.print(f"❌ Error connecting to OpenRouter API: {str(e)}")
    
    # Environment variables
    console.print("\n[bold]Checking environment variables...[/bold]")
    env_api_key = os.environ.get("OPENROUTER_API_KEY")
    if env_api_key:
        masked_env_key = f"****{env_api_key[-4:]}" if len(env_api_key) >= 4 else "****"
        console.print(f"✅ OPENROUTER_API_KEY environment variable is set (ending with {masked_env_key})")
    else:
        console.print("ℹ️ OPENROUTER_API_KEY environment variable is not set")
    
    env_default_model = os.environ.get("DEFAULT_MODEL")
    if env_default_model:
        console.print(f"✅ DEFAULT_MODEL environment variable is set to: {env_default_model}")
    else:
        console.print("ℹ️ DEFAULT_MODEL environment variable is not set")
    
    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if api_key and (api_key.startswith("sk-or-") or env_api_key):
        console.print("✅ Your configuration appears to be valid")
    else:
        console.print("❌ There are issues with your configuration that need to be fixed")
        console.print("Run [bold]llmchat config-set[/bold] to update your configuration")


@app.command()
def models(limit: int = typer.Option(20, help="Maximum number of models to display")):
    """List available models from OpenRouter API"""
    try:
        console.print(Panel("Available Models", border_style="blue"))
        
        # Get models from OpenRouter API
        api_key = config.get('api_key')
        if not api_key:
            console.print("[bold red]Error: API key not set[/bold red]")
            console.print("Run [bold]llmchat config-set[/bold] to set your API key")
            return
        
        # Add debugging information
        console.print("[dim]Fetching models from OpenRouter API...[/dim]")
        
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code != 200:
            console.print(f"[bold red]Error: Failed to fetch models. Status code: {response.status_code}[/bold red]")
            console.print(f"Response: {response.text}")
            return
        
        models_data = response.json().get('data', [])
        
        # Group models by provider
        providers = {}
        for model in models_data:
            provider = model.get('id', '').split('/')[0].upper() if '/' in model.get('id', '') else 'OTHER'
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        # Display models by provider with a limit
        model_count = 0
        for provider, models in providers.items():
            if model_count >= limit:
                console.print(f"\n[dim]Showing {model_count} of {len(models_data)} models. Use --limit to show more.[/dim]")
                break
                
            console.print(f"\n[bold]{provider}[/bold]")
            
            for model in models:
                if model_count >= limit:
                    break
                    
                model_id = model.get('id', '')
                description = model.get('description', 'No description available')
                
                # Truncate description if too long
                if len(description) > 200:
                    description = description[:197] + "..."
                
                pricing = model.get('pricing', {})
                
                # Safely extract pricing values with fallbacks
                prompt_price = pricing.get('prompt', '0')
                completion_price = pricing.get('completion', '0')
                
                console.print(f"  [bold cyan]{model_id}[/bold cyan]")
                console.print(f"    {description}")
                
                # Convert prices to float before formatting
                try:
                    prompt_price_float = float(prompt_price)
                    completion_price_float = float(completion_price)
                    console.print(f"    Pricing: ${prompt_price_float:.6f}/1K prompt tokens, ${completion_price_float:.6f}/1K completion tokens")
                except (ValueError, TypeError):
                    # If conversion fails, just display the raw values
                    console.print(f"    Pricing: ${prompt_price}/1K prompt tokens, ${completion_price}/1K completion tokens")
                
                model_count += 1
            
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")


if __name__ == "__main__":
    app()
