import json
import logging
import re


def extract_json_response(raw_text: str, fallback_dict: dict) -> dict:
    if not raw_text:
        fallback_copy = fallback_dict.copy()
        fallback_copy["_fallback_used"] = True
        return fallback_copy

    try:
        # 1. Búsqueda estricta dentro de bloques de código markdown ```json ... ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                return parsed

        # 2. Búsqueda genérica no greedy (no ambiciosa) de llaves JSON en texto libre
        match_direct = re.search(r"(\{.*?\})", raw_text, re.DOTALL)
        if match_direct:
            parsed = json.loads(match_direct.group(1))
            if isinstance(parsed, dict):
                return parsed

    except Exception as e:
        logging.warning(
            f"Error parseando respuesta JSON de agente: {e}. Usando fallback."
        )

    # Si falla el parseo, no se encuentra JSON válido o el resultado no es un dict,
    # retornamos una copia del fallback con la marca de auditoría de depuración.
    fallback_copy = fallback_dict.copy()
    fallback_copy["_fallback_used"] = True
    return fallback_copy
