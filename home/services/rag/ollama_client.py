import json
import re
from urllib import error as urllib_error
from urllib import request as urllib_request


def extract_json_object(text):
    if not text:
        return None

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def call_ollama_json(prompt, ollama_url, model):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    req = urllib_request.Request(
        ollama_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return extract_json_object(body.get("response", ""))
    except (urllib_error.URLError, TimeoutError, json.JSONDecodeError):
        return None
