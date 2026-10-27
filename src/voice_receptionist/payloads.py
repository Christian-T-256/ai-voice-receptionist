"""Build deterministic Retell payloads from validated location configuration."""

from __future__ import annotations

from .prompt import begin_message, render_prompt


def llm_payload(config: dict, location: dict) -> dict:
    return {
        "model": config["retell"]["model"],
        "general_prompt": render_prompt(location, config["retell"]["model"]),
        "begin_message": begin_message(location),
        "start_speaker": "agent",
    }


def agent_payload(location: dict, llm_id: str) -> dict:
    return {
        "response_engine": {"type": "retell-llm", "llm_id": llm_id},
        "voice_id": location["voice_id"],
        "agent_name": f"{location['practice_name']} Receptionist",
        "language": "en-US",
        "responsiveness": 0.8,
        "interruption_sensitivity": 0.7,
        "enable_backchannel": True,
    }


def dry_run_bundle(config: dict, location: dict) -> dict:
    return {
        "location_id": location["id"],
        "create_llm": {
            "method": "POST",
            "path": "/create-retell-llm",
            "body": llm_payload(config, location),
        },
        "create_agent": {
            "method": "POST",
            "path": "/create-agent",
            "body": agent_payload(location, "<created_llm_id>"),
        },
        "store_returned_ids_in": location["retell"],
    }


def desired_snapshot(config: dict, location: dict, llm_id: str = "<live_llm_id>") -> dict:
    agent = agent_payload(location, llm_id)
    agent["response_engine"] = {"type": "retell-llm"}
    return {"agent": agent, "llm": llm_payload(config, location)}
