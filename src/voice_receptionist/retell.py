"""Small Retell HTTP client using only the Python standard library."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class RetellError(RuntimeError):
    """A sanitized Retell request failure."""


class RetellClient:
    def __init__(self, api_key: str, base_url: str = "https://api.retellai.com", timeout: int = 30):
        if not api_key:
            raise RetellError("RETELL_API_KEY is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RetellError(f"Retell returned HTTP {exc.code} for {method} {path}") from exc
        except urllib.error.URLError as exc:
            raise RetellError(f"Retell request failed for {method} {path}: {exc.reason}") from exc

    def post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, body)

    def get(self, path: str) -> dict:
        return self._request("GET", path)

    def create_location(self, config: dict, location: dict) -> dict:
        from .payloads import agent_payload, llm_payload

        llm = self.post("create-retell-llm", llm_payload(config, location))
        llm_id = llm.get("llm_id")
        if not llm_id:
            raise RetellError("Retell created an LLM without returning llm_id")
        agent = self.post("create-agent", agent_payload(location, llm_id))
        agent_id = agent.get("agent_id")
        if not agent_id:
            raise RetellError("Retell created an agent without returning agent_id")
        return {"location_id": location["id"], "llm_id": llm_id, "agent_id": agent_id}

    def fetch_location(self, agent_id: str, llm_id: str) -> dict:
        return {
            "agent": self.get(f"get-agent/{agent_id}"),
            "llm": self.get(f"get-retell-llm/{llm_id}"),
        }
