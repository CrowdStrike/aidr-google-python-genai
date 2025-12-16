# CrowdStrike AIDR + Google Gen AI SDK

A wrapper around the Google Gen AI SDK that wraps the Gemini API with
CrowdStrike AIDR. Supports Python v3.12 and greater.

## Installation

```bash
pip install -U crowdstrike-aidr-google-genai
```

## Usage

```python
import os

import crowdstrike_aidr_google_genai as genai

client = genai.CrowdStrikeAidrClient(
    api_key=os.environ.get("GEMINI_API_KEY"),
    crowdstrike_aidr_api_token=os.environ.get("CROWDSTRIKE_AIDR_API_TOKEN"),
    crowdstrike_aidr_base_url_template=os.environ.get("CROWDSTRIKE_AIDR_BASE_URL_TEMPLATE"),
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)
print(response.text)
```
