"""
Formation model implementation for the agno framework.

This module provides support for Formation Cloud's model API.
"""
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from os import getenv
from typing import Any, Dict, Iterator, List, Optional, Union

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
        self.api_key = self.api_key or getenv("FORMATION_API_KEY")
        if not self.api_key:
            logger.error("FORMATION_API_KEY not set. Please set the FORMATION_API_KEY environment variable.")

        self.base_url = self.base_url or getenv("FORMATION_API_BASE_URL", "https://agents.formation.cloud/v1")

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

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the model.
        """
        _dict = super().to_dict()
        _dict.update(
            {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "stop": self.stop,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty,
                "seed": self.seed,
                "response_format": self.response_format,
                "tools": self._tools,
                "tool_choice": self.tool_choice
                if (self._tools is not None and self.tool_choice is not None)
                else "auto",
            }
        )
        cleaned_dict = {k: v for k, v in _dict.items() if v is not None}
        return cleaned_dict

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
            "name": message.name or message.tool_name,
            "tool_call_id": message.tool_call_id,
            "tool_calls": message.tool_calls,
        }

        message_dict = {k: v for k, v in message_dict.items() if v is not None}

        if message.tool_calls is None or len(message.tool_calls) == 0:
            message_dict["tool_calls"] = None

        return message_dict

    def invoke(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Send a chat completion request to the Formation Cloud API.

        Args:
            messages (List[Message]): A list of messages to send to the model.

        Returns:
            Dict[str, Any]: The chat completion response.
        """
        try:
            client = self.get_client()
            
            request_data = {
                **self.request_kwargs,
                "messages": [self._format_message(m) for m in messages],
            }
            
            response = client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except Exception as e:
            logger.error(f"Unexpected error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e

    async def ainvoke(self, messages: List[Message]) -> Dict[str, Any]:
        """
        Sends an asynchronous chat completion request to the Formation Cloud API.

        Args:
            messages (List[Message]): A list of messages to send to the model.

        Returns:
            Dict[str, Any]: The chat completion response.
        """
        try:
            client = self.get_async_client()
            
            request_data = {
                **self.request_kwargs,
                "messages": [self._format_message(m) for m in messages],
            }
            
            response = await client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except Exception as e:
            logger.error(f"Unexpected error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e

    def invoke_stream(self, messages: List[Message]) -> Iterator[Dict[str, Any]]:
        """
        Send a streaming chat completion request to the Formation Cloud API.

        Args:
            messages (List[Message]): A list of messages to send to the model.

        Returns:
            Iterator[Dict[str, Any]]: An iterator of chat completion chunks.
        """
        try:
            client = self.get_client()
            
            request_data = {
                **self.request_kwargs,
                "messages": [self._format_message(m) for m in messages],
                "stream": True,
            }
            
            with client.stream(
                "POST",
                "/chat/completions",
                json=request_data,
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding Formation streaming response: {data_str}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except Exception as e:
            logger.error(f"Unexpected error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e

    async def ainvoke_stream(self, messages: List[Message]) -> AsyncIterator[Dict[str, Any]]:
        """
        Sends an asynchronous streaming chat completion request to the Formation Cloud API.

        Args:
            messages (List[Message]): A list of messages to send to the model.

        Returns:
            AsyncIterator[Dict[str, Any]]: An asynchronous iterator of chat completion chunks.
        """
        try:
            client = self.get_async_client()
            
            request_data = {
                **self.request_kwargs,
                "messages": [self._format_message(m) for m in messages],
                "stream": True,
            }
            
            async with client.stream(
                "POST",
                "/chat/completions",
                json=request_data,
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding Formation streaming response: {data_str}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e
        except Exception as e:
            logger.error(f"Unexpected error invoking Formation model: {e}")
            raise ModelProviderError(message=str(e), model_name=self.name, model_id=self.id) from e

    @staticmethod
    def parse_tool_calls(tool_calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build tool calls from streamed tool call data.

        Args:
            tool_calls_data (List[Dict[str, Any]]): The tool call data to build from.

        Returns:
            List[Dict[str, Any]]: The built tool calls.
        """
        tool_calls: List[Dict[str, Any]] = []
        
        for tool_call in tool_calls_data:
            index = tool_call.get("index", 0)
            tool_call_id = tool_call.get("id")
            tool_call_type = tool_call.get("type", "function")
            
            function_data = tool_call.get("function", {})
            function_name = function_data.get("name", "")
            function_arguments = function_data.get("arguments", "")
            
            if len(tool_calls) <= index:
                tool_calls.extend([{}] * (index - len(tool_calls) + 1))
                
            tool_call_entry = tool_calls[index]
            
            if not tool_call_entry:
                tool_call_entry["id"] = tool_call_id
                tool_call_entry["type"] = tool_call_type
                tool_call_entry["function"] = {
                    "name": function_name,
                    "arguments": function_arguments,
                }
            else:
                if function_name:
                    tool_call_entry["function"]["name"] += function_name
                if function_arguments:
                    tool_call_entry["function"]["arguments"] += function_arguments
                if tool_call_id:
                    tool_call_entry["id"] = tool_call_id
                if tool_call_type:
                    tool_call_entry["type"] = tool_call_type
                    
        return tool_calls

    def parse_provider_response(self, response: Dict[str, Any]) -> ModelResponse:
        """
        Parse the provider response into a ModelResponse.
        
        Args:
            response (Dict[str, Any]): The raw response from the provider.
            
        Returns:
            ModelResponse: A structured model response object.
        """
        model_response = ModelResponse()
        
        if "choices" in response and len(response["choices"]) > 0:
            response_message = response["choices"][0].get("message", {})
            
            model_response.role = response_message.get("role")
            
            if "content" in response_message and response_message["content"] is not None:
                model_response.content = response_message["content"]
                
            if "tool_calls" in response_message and response_message["tool_calls"] is not None:
                tool_calls = response_message["tool_calls"]
                model_response.tool_calls = tool_calls
                
                # Ensure tool call arguments are strings, not dictionaries
                for tool_call in model_response.tool_calls:
                    if isinstance(tool_call.get("function", {}).get("arguments"), dict):
                        tool_call["function"]["arguments"] = json.dumps(tool_call["function"]["arguments"])
        
        if "usage" in response:
            model_response.response_usage = response["usage"]
            
        return model_response

    def parse_provider_response_delta(self, response_delta: Dict[str, Any]) -> ModelResponse:
        """
        Parse the provider response delta into a ModelResponse.
        
        Args:
            response_delta (Dict[str, Any]): The raw delta response from the provider.
            
        Returns:
            ModelResponse: A structured model response object.
        """
        model_response = ModelResponse()
        
        if "choices" in response_delta and len(response_delta["choices"]) > 0:
            delta = response_delta["choices"][0].get("delta", {})
            
            model_response.role = delta.get("role")
            
            if "content" in delta and delta["content"] is not None:
                model_response.content = delta["content"]
                
            if "tool_calls" in delta and delta["tool_calls"] is not None:
                model_response.tool_calls = delta["tool_calls"]
                
        if "usage" in response_delta:
            model_response.response_usage = response_delta["usage"]
            
        return model_response


@dataclass
class FormationChat(Formation):
    """
    Formation Chat model for agno.
    
    Specialized for chat-based interactions with Formation models.
    """
    
    def __init__(
        self,
        id: str = "best-quality",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize the Formation Chat model.
        
        Args:
            id: Model ID to use or "best-x" for Formation routing
            api_key: API key for Formation Cloud
            base_url: Base URL for Formation Cloud API
            temperature: Temperature for the model
            max_tokens: Maximum tokens to generate
            top_p: Top-p value for sampling
            **kwargs: Additional parameters to pass to the API
        """
        super().__init__(
            id=id,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            **kwargs,
        )
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the model.
        
        Returns:
            Dictionary containing model metadata.
        """
        metadata = super().get_metadata()
        metadata["type"] = "chat"
        return metadata 