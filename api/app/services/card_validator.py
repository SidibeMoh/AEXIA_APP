"""Validation de l'AEXIA™ Card (schéma JSON Draft-07, cf. §6.2 du PDF)."""
from __future__ import annotations
import json
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

_SCHEMA: dict | None = None

def _load_schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        schema_path = Path(__file__).resolve().parents[3] / "schemas" / "aexia_card_schema.json"
        if schema_path.exists():
            _SCHEMA = json.loads(schema_path.read_text(encoding="utf-8"))
        else:
            _SCHEMA = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "AEXIA Card v3.2",
                "type": "object",
                "required": ["id", "version", "system_name", "level_s", "xai_method", "data_readiness", "compliance"],
                "properties": {
                    "id": {"type": "string", "pattern": "^AEXIA-[A-Z0-9]{8}$"},
                    "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
                    "system_name": {"type": "string", "minLength": 1},
                    "classification_ai_act": {"type": "string", "enum": ["minimal", "limite", "haut_risque", "inacceptable"]},
                    "level_s": {"type": "integer", "minimum": 0, "maximum": 9},
                    "xai_method": {"type": "string", "enum": ["SHAP", "LIME", "DCME", "ANCHORS", "DiCE", "IG"]},
                    "data_readiness": {"type": "object"},
                    "surveillance": {"type": "object"},
                    "compliance": {"type": "object"},
                },
            }
    return _SCHEMA

def validate_card(card: dict) -> tuple[bool, list[str]]:
    if jsonschema is None:
        raise RuntimeError("jsonschema non installé — ajouter à requirements.txt")
    validator = jsonschema.Draft7Validator(_load_schema())
    errors = sorted(validator.iter_errors(card), key=lambda e: list(e.path))
    return len(errors) == 0, [f"{list(e.path)}: {e.message}" for e in errors]