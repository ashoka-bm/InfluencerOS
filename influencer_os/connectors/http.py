"""HTTP utilities for research-acquisition connectors (stdlib only).

Adapted from Agentic OS `str-trending-research/scripts/lib/http.py`, itself
adapted from https://github.com/Ronnie-Nutrition/last30days-skill. Kept stdlib-
only on purpose: no third-party SDKs enter the dependency tree.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0
USER_AGENT = "influencer-os-connectors/1.0"

DEBUG = os.environ.get("INFLUENCER_OS_CONNECTOR_DEBUG", "").lower() in ("1", "true", "yes")


def log(msg: str) -> None:
    if DEBUG:
        sys.stderr.write(f"[connector] {msg}\n")
        sys.stderr.flush()


class HTTPError(Exception):
    """HTTP request error carrying status code and body."""

    def __init__(self, message: str, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = MAX_RETRIES,
) -> Dict[str, Any]:
    """Make an HTTP request and return the parsed JSON body.

    Retries on 429 and 5xx with linear backoff; raises immediately on other 4xx.
    """
    headers = dict(headers or {})
    headers.setdefault("User-Agent", USER_AGENT)

    data = None
    if json_data is not None:
        data = json.dumps(json_data).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    log(f"{method} {url}")

    last_error: Optional[HTTPError] = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                log(f"{response.status} ({len(body)} bytes)")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = None
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                pass
            last_error = HTTPError(f"HTTP {exc.code}: {exc.reason}", exc.code, body)
            if 400 <= exc.code < 500 and exc.code != 429:
                raise last_error
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except urllib.error.URLError as exc:
            last_error = HTTPError(f"URL error: {exc.reason}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except json.JSONDecodeError as exc:
            raise HTTPError(f"Invalid JSON response: {exc}") from None
        except (OSError, TimeoutError) as exc:
            last_error = HTTPError(f"Connection error: {type(exc).__name__}: {exc}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    raise last_error or HTTPError("Request failed with no error details")


def get(url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
    return request("GET", url, headers=headers, **kwargs)


def post(url: str, json_data: Dict[str, Any], headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
    return request("POST", url, headers=headers, json_data=json_data, **kwargs)


def get_reddit_json(path: str) -> Dict[str, Any]:
    """Fetch public Reddit thread JSON directly (used for engagement enrichment)."""
    if not path.startswith("/"):
        path = "/" + path
    path = path.rstrip("/")
    if not path.endswith(".json"):
        path = path + ".json"
    url = f"https://www.reddit.com{path}?raw_json=1"
    return request("GET", url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
