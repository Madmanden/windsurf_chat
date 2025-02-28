# CLI LLM Chat App
This is an app that allows you to chat with LLMs using the OpenRouter API through a command-line interface in Mac terminal.

## Features
- Basic chat functionality
- Integration with OpenRouter API
- Easy installation and usage

## API Integration
- Connect to OpenRouter API for accessing various LLMs
- Handle authentication with API keys
- Manage API request/response flow

## Terminal UI
- Create a clean, intuitive terminal interface
- Support for conversation history
- Message formatting and display
- Input handling with command options

## Configuration System
- Store API keys securely
- Allow model selection and parameters
- Save user preferences

## Tech Stack
- **Language**: Python 3.9+
- **CLI Framework**: Typer (modern CLI tool built on Click)
- **Terminal UI**: Rich (for beautiful terminal formatting)
- **HTTP Client**: Requests (for API integration)
- **Configuration**: Python-dotenv (for secure API key storage)
- **Data Storage**: JSON (for conversation history)
- **Packaging**: Poetry (for dependency management and packaging)