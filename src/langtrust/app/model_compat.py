"""Ollama model Live Run compatibility preflight (G9C9).

Interprets the dict schema returned by ``get_ollama_model_metadata`` —
that helper never raises for missing models or connection failures; it
always returns a dict with ``capabilities`` (default ``[]``) and optional
``tags_error`` / ``show_error`` fields.
"""

from __future__ import annotations

from typing import Any, Callable


class ModelCompatibilityError(ValueError):
    """Selected Ollama model failed Live Run compatibility preflight."""


def check_ollama_model_tool_compatibility(
    model_name: str,
    *,
    get_metadata: Callable[[str], Any] | None = None,
) -> dict:
    """Raise ModelCompatibilityError unless model advertises native tools.

    Returns the metadata dict on success.
    """
    if get_metadata is None:
        from langtrust.app.benchmark import get_ollama_model_metadata

        get_metadata = get_ollama_model_metadata

    try:
        metadata = get_metadata(model_name)
    except Exception as exc:  # noqa: BLE001 - surface as preflight failure
        raise ModelCompatibilityError(
            f"Ollama unavailable while checking model {model_name!r}: {exc}"
        ) from exc

    if not isinstance(metadata, dict):
        raise ModelCompatibilityError(
            f"Could not retrieve metadata for model {model_name!r}: "
            f"expected dict, got {type(metadata).__name__}"
        )

    show_error = metadata.get("show_error")
    tags_error = metadata.get("tags_error")
    capabilities = metadata.get("capabilities")

    if show_error is not None:
        tags_is_missing = _is_missing_model_tags_error(tags_error)
        if tags_is_missing:
            raise ModelCompatibilityError(
                f"Model {model_name!r} not found / metadata lookup failed "
                f"(tags_error={tags_error!r}, show_error={show_error!r})"
            )
        if tags_error is not None and not tags_is_missing:
            raise ModelCompatibilityError(
                f"Ollama unavailable while checking model {model_name!r} "
                f"(tags_error={tags_error!r}, show_error={show_error!r})"
            )
        raise ModelCompatibilityError(
            f"Could not retrieve metadata / capabilities unknown for model "
            f"{model_name!r} (show_error={show_error!r})"
        )

    if not isinstance(capabilities, list):
        raise ModelCompatibilityError(
            f"Capabilities unknown for model {model_name!r}: "
            f"expected list, got {type(capabilities).__name__}"
        )

    if len(capabilities) == 0:
        raise ModelCompatibilityError(
            f"Capabilities unknown/empty for model {model_name!r}; "
            f"cannot verify native tool support"
        )

    if "tools" not in capabilities:
        raise ModelCompatibilityError(
            f"Model {model_name!r} does not advertise native tool support "
            f"(capabilities={capabilities!r})"
        )

    return metadata


def _is_missing_model_tags_error(tags_error: Any) -> bool:
    if tags_error is None:
        return False
    if tags_error == "model_not_found":
        return True
    text = str(tags_error).lower()
    return "model_not_found" in text or "not found" in text
