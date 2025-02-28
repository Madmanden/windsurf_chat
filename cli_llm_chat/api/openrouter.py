"""
OpenRouter API Client
Handles communication with the OpenRouter API for LLM access.
"""

import requests
import json
from typing import Dict, List, Any, Optional


class OpenRouterClient:
    """Client for interacting with the OpenRouter API"""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize the OpenRouter client
        
        Args:
            api_key: OpenRouter API key
        """
        if not api_key or api_key == "your_api_key_here" or api_key == "sk-or-v1-your-api-key-here":
            raise ValueError("Invalid API key. Please set a valid OpenRouter API key.")
            
        self.api_key = api_key
        self.default_model = None
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",  
            "HTTP-Referer": "https://github.com/cli-llm-chat",  
            "X-Title": "CLI LLM Chat"  
        }
    
    def chat_completion(
        self, 
        model: str, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter
        
        Args:
            model: Model identifier (e.g., "openai/gpt-3.5-turbo")
            messages: List of message objects with role and content
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            debug: Whether to print debug information
            
        Returns:
            API response as a dictionary
        """
        if not self.api_key:
            raise ValueError("API key not set. Please set your API key using the config-set command.")
            
        if not model:
            raise ValueError("Model ID not specified. Please provide a valid model ID.")
            
        if not messages or len(messages) == 0:
            raise ValueError("No messages provided. Please provide at least one message.")
        
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Debug information
        if debug:
            print(f"\nRequest URL: {url}")
            print(f"Headers: Authorization: Bearer ****{self.api_key[-4:] if len(self.api_key) >= 4 else '****'}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Debug response
            if debug:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
            
            if response.status_code != 200:
                error_msg = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if debug:
                        print(f"Error response: {error_data}")
                    if "error" in error_data:
                        error_msg = f"API Error: {error_data['error']['message']}"
                    elif "message" in error_data:
                        error_msg = f"API Error: {error_data['message']}"
                except:
                    if debug:
                        print(f"Could not parse error response: {response.text}")
                    if response.text:
                        error_msg = f"API Error: {response.text}"
                raise Exception(error_msg)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            if debug:
                print(f"Request error: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
    
    def list_models(self):
        """
        Get a list of available models from the OpenRouter API
        """
        if not self.api_key:
            raise ValueError("API key not set. Please set your API key using the config-set command.")
        
        url = "https://openrouter.ai/api/v1/models"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch models. Status code: {response.status_code}. Response: {response.text}")
        
        return response.json().get('data', [])
