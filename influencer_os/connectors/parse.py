"""Shared response-parsing helpers for research-acquisition connectors.

Both the OpenAI (Reddit) and xAI (X) Responses APIs return assistant text that
carries a JSON object with an "items" array, possibly surrounded by prose or
other JSON objects. These helpers extract it robustly; a greedy first-brace to
last-brace match corrupts the payload when the model emits more than one object.
"""

import json
from typing import Any, Dict, List


def extract_output_text(response: Dict[str, Any]) -> str:
    """Pull the assistant text out of an OpenAI/xAI Responses payload."""
    output = response.get("output")
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        # Assign-then-return-if-non-empty, not return-on-first-match: the output
        # list can lead with non-message items (web_search_call, reasoning) or an
        # empty placeholder, and short-circuiting on those would drop the real
        # assistant message that follows.
        for item in output:
            text = ""
            if isinstance(item, dict):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if isinstance(c, dict) and c.get("type") == "output_text":
                            text = c.get("text", "")
                            break
                elif "text" in item:
                    text = item["text"]
            elif isinstance(item, str):
                text = item
            if text:
                return text
    for choice in response.get("choices", []):
        if "message" in choice:
            return choice["message"].get("content", "")
    return ""


def iter_balanced_objects(text: str):
    """Yield every balanced ``{...}`` substring, left to right, ignoring braces
    that appear inside JSON string literals.

    String-awareness matters: a lone ``{`` or ``}`` inside a model-supplied value
    (a title, tweet text, a code snippet, LaTeX like ``\\frac{a}``) would otherwise
    mis-balance the depth counter and truncate an otherwise-valid payload.
    """
    for start, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        in_str = False
        esc = False
        for j in range(start, len(text)):
            c = text[j]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:j + 1]
                    break


def extract_items(output_text: str) -> List[Any]:
    """Find the JSON object that carries "items", tolerating surrounding text
    or other JSON objects."""
    for candidate in iter_balanced_objects(output_text):
        if '"items"' not in candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
    return []


def safe_relevance(value: Any) -> float:
    """Coerce a model-supplied relevance to [0, 1], defaulting on bad input."""
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def safe_int(value: Any):
    """Coerce a model-supplied count to a non-negative int, or None."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None
