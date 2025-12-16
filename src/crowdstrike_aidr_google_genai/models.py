from __future__ import annotations

from typing import Optional, Union

from crowdstrike_aidr import AIGuard
from google.genai import types
from google.genai._api_client import BaseApiClient
from google.genai._transformers import t_contents
from google.genai.models import AsyncModels, Models
from pydantic import BaseModel, ConfigDict
from typing_extensions import override

from crowdstrike_aidr_google_genai.errors import CrowdStrikeAidrBlockedError

__all__ = ("CrowdStrikeAidrModels", "AsyncCrowdStrikeAidrModels")


class PangeaMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Optional[str] = None
    content: str


class CrowdStrikeAidrModels(Models):
    _ai_guard_client: AIGuard

    @override
    def __init__(
        self,
        api_client_: BaseApiClient,
        *,
        ai_guard_client: AIGuard,
    ):
        super().__init__(api_client_)

        self._ai_guard_client = ai_guard_client

    @override
    def generate_content(
        self,
        *,
        model: str,
        contents: types.ContentListUnionDict,
        config: Optional[types.GenerateContentConfigOrDict] = None,
    ) -> types.GenerateContentResponse:
        """Makes an API request to generate content using a model.

        For the `model` parameter, supported formats for Vertex AI API include:
        - The Gemini model ID, for example: 'gemini-2.0-flash'
        - The full resource name starts with 'projects/', for example:
          'projects/my-project-id/locations/us-central1/publishers/google/models/gemini-2.0-flash'
        - The partial resource name with 'publishers/', for example:
          'publishers/google/models/gemini-2.0-flash' or
        - `/` separated publisher and model name, for example:
          'google/gemini-2.0-flash'

        For the `model` parameter, supported formats for Gemini API include:
        - The Gemini model ID, for example: 'gemini-2.0-flash'
        - The model name starts with 'models/', for example:
          'models/gemini-2.0-flash'
        - For tuned models, the model name starts with 'tunedModels/',
          for example:
          'tunedModels/1234567890123456789'

        Some models support multimodal input and output.

        Built-in MCP support is an experimental feature.

        Usage:

        .. code-block:: python

          from google.genai import types
          from google import genai

          client = genai.Client(
              vertexai=True, project='my-project-id', location='us-central1'
          )

          response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='''What is a good name for a flower shop that specializes in
              selling bouquets of dried flowers?'''
          )
          print(response.text)
          # **Elegant & Classic:**
          # * The Dried Bloom
          # * Everlasting Florals
          # * Timeless Petals

          response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
              types.Part.from_text(text='What is shown in this image?'),
              types.Part.from_uri(file_uri='gs://generativeai-downloads/images/scones.jpg',
              mime_type='image/jpeg')
            ]
          )
          print(response.text)
          # The image shows a flat lay arrangement of freshly baked blueberry
          # scones.
        """
        normalized_contents = t_contents(contents)
        pangea_messages = [
            (PangeaMessage(role=content.role, content=part.text), (content_idx, part_idx))
            for content_idx, content in enumerate(normalized_contents)
            if content.role and content.parts
            for part_idx, part in enumerate(content.parts)
            if part.text
        ]

        guard_input_response = self._ai_guard_client.guard_chat_completions(
            guard_input={"messages": [message for message, _ in pangea_messages]}, event_type="input"
        )

        assert guard_input_response.result is not None

        if guard_input_response.result.blocked:
            raise CrowdStrikeAidrBlockedError()

        if guard_input_response.result.transformed and guard_input_response.result.guard_output is not None:
            for idx, (_message, (content_idx, part_idx)) in enumerate(pangea_messages):
                transformed = guard_input_response.result.guard_output["messages"][idx]
                parts = normalized_contents[content_idx].parts
                if parts is not None:
                    parts[part_idx] = types.Part.from_text(text=transformed.content)

        genai_response = super().generate_content(model=model, contents=normalized_contents, config=config)

        if genai_response.text is None:
            return genai_response

        output_messages = [PangeaMessage(role="assistant", content=genai_response.text)]

        # TODO: reintroduce.
        # FPE decryption.
        # if guard_input_response.result.fpe_context is not None:
        #     redact_response = self._redact_client.unredact(
        #         output_messages,
        #         fpe_context=guard_input_response.result.fpe_context,
        #     )
        #     assert redact_response.result is not None
        #     output_messages = redact_response.result.data

        guard_output_response = self._ai_guard_client.guard_chat_completions(
            # The LLM response must be contained within a single "assistant"
            # message to AI Guard. Splitting up the content parts into
            # multiple "assistant" messages will result in only the last
            # message being processed.
            guard_input={"messages": [message for message, _ in pangea_messages] + output_messages},
            event_type="output",
        )

        assert guard_output_response.result is not None

        if guard_output_response.result.blocked:
            raise CrowdStrikeAidrBlockedError()

        if (
            guard_output_response.result.transformed
            and guard_output_response.result.guard_output is not None
            and genai_response.candidates
            and genai_response.candidates[0].content is not None
            and genai_response.candidates[0].content.parts is not None
        ):
            transformed_assistant_message = guard_output_response.result.guard_output["messages"][-1]
            genai_response.candidates[0].content.parts = [
                types.Part.from_text(text=transformed_assistant_message.content)
            ]

        return genai_response


class AsyncCrowdStrikeAidrModels(AsyncModels):
    _ai_guard_client: AIGuard

    @override
    def __init__(self, api_client_: BaseApiClient, *, ai_guard_client: AIGuard):
        super().__init__(api_client_)

        self._ai_guard_client = ai_guard_client

    @override
    async def generate_content(
        self,
        *,
        model: str,
        contents: Union[types.ContentListUnion, types.ContentListUnionDict],
        config: Optional[types.GenerateContentConfigOrDict] = None,
    ) -> types.GenerateContentResponse:
        """Makes an API request to generate content using a model.

        Some models support multimodal input and output.

        Built-in MCP support is an experimental feature.

        Usage:

        .. code-block:: python

        from google.genai import types
        from google import genai

        client = genai.Client(
            vertexai=True, project='my-project-id', location='us-central1'
        )

        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents='User input: I like bagels. Answer:',
            config=types.GenerateContentConfig(
                system_instruction=
                    [
                    'You are a helpful language translator.',
                    'Your mission is to translate text in English to French.'
                    ]
            ),
        )
        print(response.text)
        # J'aime les bagels.
        """
        normalized_contents = t_contents(contents)
        pangea_messages = [
            (PangeaMessage(role=content.role, content=part.text), (content_idx, part_idx))
            for content_idx, content in enumerate(normalized_contents)
            if content.role and content.parts
            for part_idx, part in enumerate(content.parts)
            if part.text
        ]

        guard_input_response = self._ai_guard_client.guard_chat_completions(
            guard_input={"messages": [message for message, _ in pangea_messages]}, event_type="input"
        )

        assert guard_input_response.result is not None

        if guard_input_response.result.blocked:
            raise CrowdStrikeAidrBlockedError()

        if guard_input_response.result.transformed and guard_input_response.result.guard_output is not None:
            for idx, (_message, (content_idx, part_idx)) in enumerate(pangea_messages):
                transformed = guard_input_response.result.guard_output["messages"][idx]
                parts = normalized_contents[content_idx].parts
                if parts is not None:
                    parts[part_idx] = types.Part.from_text(text=transformed.content)

        genai_response = await super().generate_content(model=model, contents=normalized_contents, config=config)

        if genai_response.text is None:
            return genai_response

        output_messages = [PangeaMessage(role="assistant", content=genai_response.text)]

        # TODO: reintroduce.
        # FPE decryption.
        # if guard_input_response.result.fpe_context is not None:
        #     redact_response = await self._redact_client.unredact(
        #         output_messages,
        #         fpe_context=guard_input_response.result.fpe_context,
        #     )
        #     assert redact_response.result is not None
        #     output_messages = redact_response.result.data

        guard_output_response = self._ai_guard_client.guard_chat_completions(
            # The LLM response must be contained within a single "assistant"
            # message to AI Guard. Splitting up the content parts into
            # multiple "assistant" messages will result in only the last
            # message being processed.
            guard_input={"messages": [message for message, _ in pangea_messages] + output_messages},
            event_type="output",
        )

        assert guard_output_response.result is not None

        if guard_output_response.result.blocked:
            raise CrowdStrikeAidrBlockedError()

        if (
            guard_output_response.result.transformed
            and guard_output_response.result.guard_output is not None
            and genai_response.candidates
            and genai_response.candidates[0].content is not None
            and genai_response.candidates[0].content.parts is not None
        ):
            transformed_assistant_message = guard_output_response.result.guard_output["messages"][-1]
            genai_response.candidates[0].content.parts = [
                types.Part.from_text(text=transformed_assistant_message.content)
            ]

        return genai_response
