# CLI LLM Chat

A command-line interface for chatting with LLMs using the OpenRouter API.

## Features

- Chat with various LLMs through OpenRouter API
- Clean, intuitive terminal interface using Rich formatting
- Save and load conversation history
- Configure API keys and default settings
- View available models
- Create and continue named conversations

## Getting Started

### Prerequisites

- Python 3.8 or higher
- An OpenRouter API key (sign up at [OpenRouter](https://openrouter.ai/))

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/cli-llm-chat.git
cd cli-llm-chat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make the script executable:

```bash
chmod +x llmchat
```

### Getting an OpenRouter API Key

1. Sign up for an account at [OpenRouter](https://openrouter.ai/)
2. Navigate to your account settings or API section
3. Create a new API key - it should start with `sk-or-v1-`
4. Copy this key for use in the CLI LLM Chat app

### Configuration

Before using the CLI LLM Chat, you need to configure your OpenRouter API key:

```bash
./llmchat config-set
```

This will prompt you to enter your OpenRouter API key and default model. You can also set these values directly:

```bash
./llmchat config-set --api-key YOUR_API_KEY --default-model google/gemini-2.0-flash-001
```

> **Note:** Your OpenRouter API key should start with `sk-or-`. You can get your API key by signing up at [OpenRouter](https://openrouter.ai/).

Alternatively, you can set these values in a `.env` file:

```
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
DEFAULT_MODEL=google/gemini-2.0-flash-001
```

## Usage

### Starting a chat session

Simply run the command without any arguments to start an interactive chat session:

```bash
llmchat
```

You can also specify options:

```bash
llmchat --model google/gemini-2.0-flash-001 --temperature 0.8
```

For non-interactive mode, you can send a single message:

```bash
llmchat --message "What is the capital of France?"
```

If you need to see debug information (like API requests and responses), add the `--debug` flag:

```bash
llmchat --debug
```

### Named Conversations

You can create and continue named conversations that persist between sessions:

```bash
# Start or continue a named conversation
llmchat --conversation my_project

# Send a single message to a named conversation
llmchat --message "What's the next step?" --conversation my_project
```

### Chat commands

During a chat session, you can use these special commands:
- `/exit` - Exit the chat session
- `/clear` - Clear the conversation history
- `/save <name>` - Save the current conversation with a specific name
- `/list` - List all saved conversations
- `/load <name>` - Load a previously saved conversation
- `/help` - Show available commands

### List available models

```bash
llmchat models
```

This will display a list of available models from OpenRouter, grouped by provider.

### Troubleshooting

If you encounter issues with the CLI LLM Chat app, you can use the test-model command to diagnose problems:

```bash
llmchat test-model --model google/gemini-2.0-flash-001 --message "Hello, what model are you?"
```

Common issues:
1. **Invalid API key format** - Make sure your API key starts with `sk-or-`
2. **Authentication errors** - Verify that your API key is active and correctly entered
3. **Connection issues** - Check your internet connection or OpenRouter service status

## Tech Stack

- **Language**: Python 3.9+
- **CLI Framework**: Typer (modern CLI tool built on Click)
- **Terminal UI**: Rich (for beautiful terminal formatting)
- **HTTP Client**: Requests (for API integration)
- **Configuration**: Python-dotenv (for secure API key storage)
- **Data Storage**: JSON (for conversation history)

## License

MIT
