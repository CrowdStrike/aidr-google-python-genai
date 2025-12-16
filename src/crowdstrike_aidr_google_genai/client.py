from __future__ import annotations

from typing import Optional, Union

import google.auth
from crowdstrike_aidr import AIGuard
from google import genai
from google.genai._api_client import BaseApiClient
from google.genai.client import AsyncClient, DebugConfig
from google.genai.types import HttpOptions, HttpOptionsDict
from typing_extensions import override

from crowdstrike_aidr_google_genai.models import AsyncCrowdStrikeAidrModels, CrowdStrikeAidrModels

__all__ = ("CrowdStrikeAidrClient",)


class CrowdStrikeAidrClient(genai.Client):
    @override
    def __init__(
        self,
        *,
        vertexai: Optional[bool] = None,
        api_key: Optional[str] = None,
        credentials: Optional[google.auth.credentials.Credentials] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
        debug_config: Optional[DebugConfig] = None,
        http_options: Optional[Union[HttpOptions, HttpOptionsDict]] = None,
        crowdstrike_aidr_api_token: str,
        crowdstrike_aidr_base_url_template: str,
    ):
        super().__init__(
            vertexai=vertexai,
            api_key=api_key,
            credentials=credentials,
            project=project,
            location=location,
            debug_config=debug_config,
            http_options=http_options,
        )
        self._aio = AsyncCrowdStrikeAidrClient(
            self._api_client,
            crowdstrike_aidr_api_token=crowdstrike_aidr_api_token,
            crowdstrike_aidr_base_url_template=crowdstrike_aidr_base_url_template,
        )
        self._models = CrowdStrikeAidrModels(
            self._api_client,
            ai_guard_client=AIGuard(
                token=crowdstrike_aidr_api_token, base_url_template=crowdstrike_aidr_base_url_template
            ),
        )


class AsyncCrowdStrikeAidrClient(AsyncClient):
    @override
    def __init__(
        self, api_client: BaseApiClient, *, crowdstrike_aidr_api_token: str, crowdstrike_aidr_base_url_template: str
    ):
        super().__init__(api_client)
        self._models = AsyncCrowdStrikeAidrModels(
            self._api_client,
            ai_guard_client=AIGuard(
                token=crowdstrike_aidr_api_token, base_url_template=crowdstrike_aidr_base_url_template
            ),
        )
