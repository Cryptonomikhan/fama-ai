from dataclasses import dataclass
from os import getenv
from typing import Optional

from agno.models.openai.like import OpenAILike


@dataclass
class Formation(OpenAILike):
    """
    A class for using models hosted on OpenRouter.

    Attributes:
        id (str): The model id. Defaults to "gpt-4o".
        name (str): The model name. Defaults to "OpenRouter".
        provider (str): The provider name. Defaults to "OpenRouter: " + id.
        api_key (Optional[str]): The API key. Defaults to None.
        base_url (str): The base URL. Defaults to "https://models.formation.cloud/api/v1".
        max_tokens (int): The maximum number of tokens. Defaults to 1024.
    """

    id: str = "deepseek-v3-0324"
    name: str = "Formation"
    provider: str = "Formation"

    api_key: Optional[str] = getenv("FORMATION_API_KEY")
    base_url: str = "https://models.formation.cloud/api/v1"
    max_tokens: int = 200_000
