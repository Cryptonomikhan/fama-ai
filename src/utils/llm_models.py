import os
import logging
from typing import Any, Optional, Dict, Union
from textwrap import dedent

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default settings - Formation is the default provider
DEFAULT_LLM_PROVIDER = "formation"
DEFAULT_LLM_MODEL_ID = "best-quality"  # Formation's best quality model
FORMATION_API_BASE_URL = "https://agents.formation.cloud/v1"

def get_llm_model(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """
    Dynamically loads and returns an LLM model instance based on provider and model ID.

    Reads provider and model_id from environment variables if not provided explicitly.
    Requires necessary API keys to be set as environment variables (e.g., FORMATION_API_KEY).

    Args:
        provider: The LLM provider (e.g., 'formation', 'openai', 'anthropic'). Reads from LLM_PROVIDER env var if None.
        model_id: The specific model ID (e.g., 'best-quality', 'gpt-4o', 'claude-3-sonnet'). Reads from LLM_MODEL_ID env var if None.
        api_key: Optional API key. Reads from provider-specific env var if None.
        base_url: Optional base URL for API endpoint. Reads from provider-specific env var if None.
        **kwargs: Additional keyword arguments to pass to the model constructor.

    Returns:
        An instance of the specified LLM model.

    Raises:
        ValueError: If the provider is unsupported or required API keys are missing.
        ImportError: If the required provider library is not installed.
    """
    effective_provider = provider or os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).lower()
    effective_model_id = model_id or os.environ.get("LLM_MODEL_ID", DEFAULT_LLM_MODEL_ID)

    logger.info(f"Attempting to load model: Provider='{effective_provider}', Model ID='{effective_model_id}'")

    try:
        # Formation is our primary provider
        if effective_provider == "formation":
            try:
                # Import our Formation implementation
                from models.formation import Formation
                # API key is read from FORMATION_API_KEY env var by default
                formation_api_key = api_key or os.environ.get("FORMATION_API_KEY")
                if not formation_api_key:
                    raise ValueError("FORMATION_API_KEY environment variable not set.")
                effective_base_url = base_url or os.environ.get("FORMATION_API_BASE_URL", FORMATION_API_BASE_URL)
                return Formation(
                    id=effective_model_id,
                    api_key=formation_api_key,
                    base_url=effective_base_url,
                    **kwargs
                )
            except ImportError:
                logger.warning("Formation model class not found. Using OpenAI-compatible interface.")
                # Fall back to OpenAI-compatible interface
                from agno.models.openai import OpenAIChat
                formation_api_key = api_key or os.environ.get("FORMATION_API_KEY")
                if not formation_api_key:
                    raise ValueError("FORMATION_API_KEY environment variable not set.")
                effective_base_url = base_url or os.environ.get("FORMATION_API_BASE_URL", FORMATION_API_BASE_URL)
                return OpenAIChat(
                    id=effective_model_id,
                    api_key=formation_api_key,
                    base_url=effective_base_url,
                    **kwargs
                )
        # Standard providers supported by Agno
        elif effective_provider == "openai":
            from agno.models.openai import OpenAIChat
            # API key is read automatically by the library from OPENAI_API_KEY
            openai_api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            openai_base_url = base_url or os.environ.get("OPENAI_BASE_URL")
            return OpenAIChat(
                id=effective_model_id, 
                api_key=openai_api_key, 
                base_url=openai_base_url,
                **kwargs
            )
        elif effective_provider == "anthropic":
            from agno.models.anthropic import AnthropicChat
            anthropic_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            return AnthropicChat(
                id=effective_model_id, 
                api_key=anthropic_api_key,
                **kwargs
            )
        elif effective_provider == "groq":
            from agno.models.groq import GroqChat
            groq_api_key = api_key or os.environ.get("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable not set.")
            return GroqChat(
                id=effective_model_id, 
                api_key=groq_api_key,
                **kwargs
            )
        elif effective_provider == "gemini":
            from agno.models.gemini import GeminiChat
            gemini_api_key = api_key or os.environ.get("GOOGLE_API_KEY")
            if not gemini_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            return GeminiChat(
                id=effective_model_id, 
                api_key=gemini_api_key,
                **kwargs
            )
        elif effective_provider == "mistral":
            from agno.models.mistral import MistralChat
            mistral_api_key = api_key or os.environ.get("MISTRAL_API_KEY")
            if not mistral_api_key:
                raise ValueError("MISTRAL_API_KEY environment variable not set.")
            return MistralChat(
                id=effective_model_id, 
                api_key=mistral_api_key,
                **kwargs
            )
        elif effective_provider == "together":
            from agno.models.together import TogetherChat
            together_api_key = api_key or os.environ.get("TOGETHER_API_KEY")
            if not together_api_key:
                raise ValueError("TOGETHER_API_KEY environment variable not set.")
            return TogetherChat(
                id=effective_model_id, 
                api_key=together_api_key,
                **kwargs
            )
        elif effective_provider == "cohere":
            from agno.models.cohere import CohereChat
            cohere_api_key = api_key or os.environ.get("COHERE_API_KEY")
            if not cohere_api_key:
                raise ValueError("COHERE_API_KEY environment variable not set.")
            return CohereChat(
                id=effective_model_id, 
                api_key=cohere_api_key,
                **kwargs
            )
        elif effective_provider == "aws":
            from agno.models.aws import BedrockChat
            aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
            aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
            aws_region = os.environ.get("AWS_REGION")
            if not (aws_key and aws_secret and aws_region):
                raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION) not set.")
            return BedrockChat(
                id=effective_model_id,
                **kwargs
            )
        elif effective_provider == "azure":
            from agno.models.azure import AzureOpenAIChat
            azure_api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
            azure_endpoint = base_url or os.environ.get("AZURE_OPENAI_ENDPOINT")
            if not (azure_api_key and azure_endpoint):
                raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set.")
            return AzureOpenAIChat(
                id=effective_model_id,
                api_key=azure_api_key,
                base_url=azure_endpoint,
                **kwargs
            )
        elif effective_provider == "ollama":
            from agno.models.ollama import OllamaChat
            ollama_base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaChat(
                id=effective_model_id,
                base_url=ollama_base_url,
                **kwargs
            )
        elif effective_provider == "litellm":
            from agno.models.litellm import LiteLLMChat
            litellm_api_key = api_key or os.environ.get("LITELLM_API_KEY")
            if not litellm_api_key:
                raise ValueError("LITELLM_API_KEY environment variable not set.")
            return LiteLLMChat(
                id=effective_model_id,
                api_key=litellm_api_key,
                **kwargs
            )
        elif effective_provider == "openrouter":
            from agno.models.openrouter import OpenRouterChat
            openrouter_api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not set.")
            return OpenRouterChat(
                id=effective_model_id,
                api_key=openrouter_api_key,
                **kwargs
            )
        else:
            logger.warning(f"Unsupported LLM provider: {effective_provider}, falling back to Formation.")
            # Fall back to Formation as our default
            try:
                from models.formation import Formation
                formation_api_key = os.environ.get("FORMATION_API_KEY")
                if not formation_api_key:
                    raise ValueError("FORMATION_API_KEY environment variable not set.")
                effective_base_url = os.environ.get("FORMATION_API_BASE_URL", FORMATION_API_BASE_URL)
                return Formation(
                    id=DEFAULT_LLM_MODEL_ID,
                    api_key=formation_api_key, 
                    base_url=effective_base_url,
                    **kwargs
                )
            except (ImportError, ValueError):
                # If Formation is also not available, try OpenAI
                logger.warning("Formation unavailable, falling back to OpenAI.")
                from agno.models.openai import OpenAIChat
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("Both FORMATION_API_KEY and OPENAI_API_KEY are not set.")
                return OpenAIChat(
                    id="gpt-4o", 
                    api_key=openai_api_key,
                    **kwargs
                )

    except ImportError as e:
        logger.error(f"Failed to import library for provider '{effective_provider}'. Please install required dependencies.")
        raise ImportError(f"Missing dependencies for provider '{effective_provider}': {e}") from e
    except Exception as e:
        logger.error(f"Error loading model for provider '{effective_provider}', model '{effective_model_id}': {e}")
        raise

def get_available_models() -> Dict[str, Any]:
    """
    Get information about available models and providers supported.
    
    Returns:
        A dictionary containing available models and providers
    """
    current_provider = os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    current_model = os.environ.get("LLM_MODEL_ID", DEFAULT_LLM_MODEL_ID)
    
    available_models = {
        "formation": ["best-quality", "best-reasoning", "best-speed", "best-rag"],
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "groq": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "mistral": ["mistral-large", "mistral-medium", "mistral-small"],
        "cohere": ["command", "command-r", "command-r-plus"],
        "together": ["llama-3-70b", "llama-3-8b", "yi-large"],
        "aws": ["anthropic.claude-3-sonnet", "amazon.titan-text", "meta.llama3-8b"],
        "azure": ["gpt-4", "gpt-35-turbo"],
        "ollama": ["llama3", "mistral", "phi3"],
        "openrouter": ["openai/gpt-4-turbo", "anthropic/claude-3-opus", "google/gemini-pro"]
    }
    
    return {
        "current_configuration": {
            "provider": current_provider,
            "model_id": current_model
        },
        "available_providers": list(available_models.keys()),
        "available_models": available_models,
        "configuration_method": "Set via API request or environment variables (LLM_PROVIDER, LLM_MODEL_ID)"
    }

# Example usage (for testing the helper function)
if __name__ == "__main__":
    # Ensure you have FORMATION_API_KEY set in your environment
    # Or uncomment and set other provider keys/vars as needed
    # os.environ["LLM_PROVIDER"] = "formation"
    # os.environ["LLM_MODEL_ID"] = "best-quality"
    # os.environ["FORMATION_API_KEY"] = "your_formation_key" # Replace with your key

    try:
        model = get_llm_model()
        print(f"Successfully loaded model: {model}")
        print(f"Model Class: {type(model)}")
        print(f"Model ID: {getattr(model, 'id', 'N/A')}")
        print(f"Available models: {get_available_models()}")

    except (ValueError, ImportError, Exception) as e:
        print(f"Failed to load model: {e}") 