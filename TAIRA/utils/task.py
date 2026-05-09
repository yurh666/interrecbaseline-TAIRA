# utils/task.py
import os
import re

import yaml
from openai import OpenAI

with open('system_config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

model = config['MODEL']


def _resolve_api_settings():
    """Resolve API settings from env first, then fallback to config."""
    base_url = os.getenv('OPENAI_BASE_URL') or config.get('OPENAI_BASE_URL', '')
    api_key = os.getenv('OPENAI_API_KEY') or config.get('OPENAI_API_KEY', '')
    return base_url, api_key


def _build_client():
    base_url, api_key = _resolve_api_settings()
    kwargs = {}
    if base_url:
        kwargs['base_url'] = base_url
    if api_key:
        kwargs['api_key'] = api_key
    return OpenAI(**kwargs)


def get_completion(messages, llm=None, temperature=0):  # claude-3-5-sonnet-20240620 gpt-4o-2024-08-06 qwen-plus
    client = _build_client()
    tokens = 5000
    response = client.chat.completions.create(
        model=llm or model,
        messages=messages,
        temperature=temperature,
        timeout=50,
        max_tokens=tokens,
        top_p=0.1,
    )
    return response.choices[0].message.content


def get_json(messages, json_format, llm=model, temperature=0):
    client = _build_client()
    response = client.beta.chat.completions.parse(
        model=llm,
        messages=messages,
        temperature=temperature,
        timeout=50,
        max_tokens=1000,
        response_format=json_format,
    )
    return response.choices[0].message.content


def extract_braces_content(s):
    s = s.replace("\\'", "'")
    match = re.search(r'\{.*\}', s, re.DOTALL)
    if match:
        return match.group(0)
    return None
