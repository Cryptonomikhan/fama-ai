#!/usr/bin/env python3
"""
Formation model implementation for the Agno framework.

This module provides support for Formation Cloud's model API in the Agno framework.
"""
import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterator, List, Optional, Union, AsyncIterator

import httpx

from agno.exceptions import ModelProviderError
from agno.models.base import Model
from agno.models.message import Message
from agno.models.response import ModelResponse

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class Formation(Model):
    """
    A class for interacting with Formation Cloud models.
    
    Formation Cloud provides intelligent model routing with "best-x" capabilities:
    - "best-reasoning": Best model for reasoning tasks
    - "best-quality": Best model for high-quality outputs
    - "best-speed": Best model for fast responses
    - "best-rag": Best model for retrieval augmented generation
    
    Attributes:
        id (str): The id of the Formation model to use or 'best-x' options. Default is "best-quality".
        name (str): The name of this model instance. Default is "Formation".
        provider (str): The provider of the model. Default is "Formation".
        temperature (Optional[float]): Controls randomness in the model's output.
        max_tokens (Optional[int]): The maximum number of tokens to generate.
        top_p (Optional[float]): Controls diversity via nucleus sampling.
        stop (Optional[Union[str, List[str]]]): Up to 4 sequences where the API will stop generating further tokens.
        frequency_penalty (Optional[float]): Penalizes new tokens based on their frequency in the text so far.
        presence_penalty (Optional[float]): Penalizes new tokens based on whether they appear in the text so far.
        seed (Optional[int]): A seed for deterministic sampling.
        response_format (Optional[Any]): An object specifying the format that the model must output.
        request_params (Optional[Dict[str, Any]]): Additional parameters to include in the request.
        api_key (Optional[str]): The API key for authenticating with Formation Cloud.
        base_url (Optional[Union[str, httpx.URL]]): The base URL for API requests.
        timeout (Optional[float]): The timeout for API requests.
        max_retries (Optional[int]): The maximum number of retries for failed requests.
        default_headers (Optional[Any]): Default headers to include in all requests.
        default_query (Optional[Any]): Default query parameters to include in all requests.
        client_params (Optional[Dict[str, Any]]): Additional parameters for client configuration.
        client (Optional[httpx.Client]): An optional pre-configured HTTP client.
        async_client (Optional[httpx.AsyncClient]): An optional pre-configured async HTTP client.
    """
    
    id: str = "best-quality"
    name: str = "Formation"
    provider: str = "Formation"
    
    # Request parameters
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    seed: Optional[int] = None
    response_format: Optional[Any] = None
    request_params: Optional[Dict[str, Any]] = None
    
    # Client parameters
    api_key: Optional[str] = None
    base_url: Optional[Union[str, httpx.URL]] = None
    timeout: Optional[float] = 120.0
    max_retries: Optional[int] = 3
    default_headers: Optional[Any] = None
    default_query: Optional[Any] = None
    client_params: Optional[Dict[str, Any]] = None
    
    # HTTP clients
    client: Optional[httpx.Client] = None
    async_client: Optional[httpx.AsyncClient] = None
    
    def get_client_params(self) -> Dict[str, Any]:
        """
        Get parameters for creating HTTP clients.
        
        Returns:
            Dict[str, Any]: A dictionary of client parameters
        """
        self.api_key = self.api_key or os.environ.get("FORMATION_API_KEY")
        if not self.api_key:
            logger.error("FORMATION_API_KEY not set. Please set the FORMATION_API_KEY environment variable.")
            
        self.base_url = self.base_url or os.environ.get("FORMATION_API_BASE_URL", "https://api.formation.ai/v1")
        
        _client_params: Dict[str, Any] = {
            "base_url": self.base_url,
            "timeout": self.timeout or 120.0,
            "headers": {"Content-Type": "application/json"}
        }
        
        if self.api_key is not None:
            _client_params["headers"]["Authorization"] = f"Bearer {self.api_key}"
            
        if self.max_retries is not None:
            _client_params["max_retries"] = self.max_retries
            
        if self.default_headers is not None:
            _client_params["headers"].update(self.default_headers)
            
        if self.default_query is not None:
            _client_params["params"] = self.default_query
            
        if self.client_params is not None:
            _client_params.update(self.client_params)
            
        return _client_params
    
    def get_client(self) -> httpx.Client:
        """
        Returns an HTTP client for Formation Cloud API requests.
        
        Returns:
            httpx.Client: An instance of the HTTP client.
        """
        if self.client:
            return self.client
            
        _client_params = self.get_client_params()
        self.client = httpx.Client(**_client_params)
        return self.client
        
    def get_async_client(self) -> httpx.AsyncClient:
        """
        Returns an asynchronous HTTP client for Formation Cloud API requests.
        
        Returns:
            httpx.AsyncClient: An instance of the asynchronous HTTP client.
        """
        if self.async_client:
            return self.async_client
            
        _client_params = self.get_client_params()
        self.async_client = httpx.AsyncClient(**_client_params)
        return self.async_client
    
    @property
    def request_kwargs(self) -> Dict[str, Any]:
        """
        Returns keyword arguments for model API requests.
        
        Returns:
            Dict[str, Any]: A dictionary of keyword arguments for API requests.
        """
        _request_params: Dict[str, Any] = {
            "model": self.id
        }
        
        if self.temperature is not None:
            _request_params["temperature"] = self.temperature
            
        if self.max_tokens is not None:
            _request_params["max_tokens"] = self.max_tokens
            
        if self.top_p is not None:
            _request_params["top_p"] = self.top_p
            
        if self.stop is not None:
            _request_params["stop"] = self.stop
            
        if self.frequency_penalty is not None:
            _request_params["frequency_penalty"] = self.frequency_penalty
            
        if self.presence_penalty is not None:
            _request_params["presence_penalty"] = self.presence_penalty
            
        if self.seed is not None:
            _request_params["seed"] = self.seed
        
        if self._tools is not None:
            _request_params["tools"] = self._tools
            if self.tool_choice is None:
                _request_params["tool_choice"] = "auto"
            else:
                _request_params["tool_choice"] = self.tool_choice
                
        if self.request_params is not None:
            _request_params.update(self.request_params)
            
        return _request_params
    
    def _format_message(self, message: Message) -> Dict[str, Any]:
        """
        Format a message into the format expected by Formation Cloud API.
        
        Args:
            message (Message): The message to format.
            
        Returns:
            Dict[str, Any]: The formatted message.
        """
        message_dict = {
            "role": message.role,
            "content": message.content if message.content is not None else "",
            "name": message.name,
            "tool_call_id": message.tool_call_id,
            "tool_calls": message.tool_calls,
        }
        
        # Remove None values
        return {k: v for k, v in message_dict.items() if v is not None}
    
    def invoke(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Send a chat completion request to the Formation Cloud API.
        
        Args:
            messages (List[Message]): The messages to send to the model.
            
        Returns:
            Dict[str, Any]: The response from the Formation Cloud API.
            
        Raises:
            ModelProviderError: If there is an error with the Formation Cloud API.
        """
        client = self.get_client()
        
        # Format messages
        formatted_messages = [self._format_message(msg) for msg in messages]
        
        # Prepare request
        request_data = {
            **self.request_kwargs,
            "messages": formatted_messages
        }
        
        # Send request
        try:
            response = client.post("/chat/completions", json=request_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"Formation API returned error {e.response.status_code}: {e.response.text}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error communicating with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
    
    async def ainvoke(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Send an asynchronous chat completion request to the Formation Cloud API.
        
        Args:
            messages (List[Message]): The messages to send to the model.
            
        Returns:
            Dict[str, Any]: The response from the Formation Cloud API.
            
        Raises:
            ModelProviderError: If there is an error with the Formation Cloud API.
        """
        client = self.get_async_client()
        
        # Format messages
        formatted_messages = [self._format_message(msg) for msg in messages]
        
        # Prepare request
        request_data = {
            **self.request_kwargs,
            "messages": formatted_messages
        }
        
        # Send request
        try:
            response = await client.post("/chat/completions", json=request_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"Formation API returned error {e.response.status_code}: {e.response.text}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error communicating with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
    
    def invoke_stream(self, messages: List[Message]) -> Iterator[Dict[str, Any]]:
        """
        Send a streaming chat completion request to the Formation Cloud API.
        
        Args:
            messages (List[Message]): The messages to send to the model.
            
        Returns:
            Iterator[Dict[str, Any]]: An iterator of responses from the Formation Cloud API.
            
        Raises:
            ModelProviderError: If there is an error with the Formation Cloud API.
        """
        client = self.get_client()
        
        # Format messages
        formatted_messages = [self._format_message(msg) for msg in messages]
        
        # Prepare request
        request_data = {
            **self.request_kwargs,
            "messages": formatted_messages,
            "stream": True
        }
        
        # Send request
        try:
            with client.stream("POST", "/chat/completions", json=request_data) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        line = line[6:].strip()
                        if line == "[DONE]":
                            break
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON from line: {line}")
        except httpx.HTTPStatusError as e:
            error_message = f"Formation API returned error {e.response.status_code}: {e.response.text}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error communicating with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
    
    async def ainvoke_stream(self, messages: List[Message]) -> AsyncIterator[Dict[str, Any]]:
        """
        Send an asynchronous streaming chat completion request to the Formation Cloud API.
        
        Args:
            messages (List[Message]): The messages to send to the model.
            
        Returns:
            AsyncIterator[Dict[str, Any]]: An async iterator of responses from the Formation Cloud API.
            
        Raises:
            ModelProviderError: If there is an error with the Formation Cloud API.
        """
        client = self.get_async_client()
        
        # Format messages
        formatted_messages = [self._format_message(msg) for msg in messages]
        
        # Prepare request
        request_data = {
            **self.request_kwargs,
            "messages": formatted_messages,
            "stream": True
        }
        
        # Send request
        try:
            async with client.stream("POST", "/chat/completions", json=request_data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:].strip()
                        if line == "[DONE]":
                            break
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON from line: {line}")
        except httpx.HTTPStatusError as e:
            error_message = f"Formation API returned error {e.response.status_code}: {e.response.text}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error communicating with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error with Formation API: {str(e)}"
            logger.error(error_message)
            raise ModelProviderError(error_message) from e
    
    def parse_provider_response(self, response: Dict[str, Any]) -> ModelResponse:
        """
        Parse the response from the Formation Cloud API.
        
        Args:
            response (Dict[str, Any]): The response from the Formation Cloud API.
            
        Returns:
            ModelResponse: The parsed response.
        """
        try:
            # Handle non-streaming response
            if "choices" in response and isinstance(response["choices"], list):
                choice = response["choices"][0]
                content = None
                function_call = None
                tool_calls = None
                
                if "message" in choice:
                    message = choice["message"]
                    content = message.get("content")
                    
                    if "tool_calls" in message:
                        tool_calls = message["tool_calls"]
                    if "function_call" in message:
                        function_call = message["function_call"]
                
                return ModelResponse(
                    content=content,
                    model=response.get("model", self.id),
                    provider=self.provider,
                    function_call=function_call,
                    tool_calls=tool_calls,
                    finish_reason=choice.get("finish_reason"),
                    usage=response.get("usage"),
                )
            # Handle streaming response chunk
            elif "choices" in response and isinstance(response["choices"], list) and "delta" in response["choices"][0]:
                choice = response["choices"][0]
                delta = choice["delta"]
                
                content = delta.get("content", "")
                function_call = delta.get("function_call")
                tool_calls = delta.get("tool_calls")
                
                return ModelResponse(
                    content=content,
                    model=response.get("model", self.id),
                    provider=self.provider,
                    function_call=function_call,
                    tool_calls=tool_calls,
                    finish_reason=choice.get("finish_reason"),
                    usage=response.get("usage"),
                )
            else:
                logger.warning(f"Unexpected response format from Formation API: {response}")
                return ModelResponse(
                    content="",
                    model=self.id,
                    provider=self.provider,
                )
        except Exception as e:
            logger.error(f"Error parsing Formation API response: {str(e)}")
            return ModelResponse(
                content="Error parsing response",
                model=self.id,
                provider=self.provider,
            ) 