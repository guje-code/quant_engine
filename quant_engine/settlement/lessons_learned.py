import json
import os
import re
import uuid
from datetime import datetime

from quant_engine.config.settings import BASE_DIR

POSTMORTEM_DIR = os.path.join(BASE_DIR, "logs_postmortem")
os.makedirs(POSTMORTEM_DIR, exist_ok=True)

MASTER_JSON_PATH = os.path.join(POSTMORTEM_DIR, "lessons_master.json")


def guardar_log_postmortem(
    pick_id: int, match_name: str, sport_league: str, postmortem_data: dict
):
    """
    Guarda el análisis post-mortem de forma dual e incorpora trazabilidad
    mediante UUID (`lesson_id`) y ciclo de vida de reglas (`review_status`).
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_limpio = re.sub(r"[^\w\-_]", "_", match_name)
    lesson_uuid = str(uuid.uuid4())

    # Manejo robusto por si postmortem_data llega como dict o texto plano de emergencia
    if isinstance(postmortem_data, dict):
        classification = postmortem_data.get("classification", "UNKNOWN")
        root_cause = postmortem_data.get("root_cause", "No especificada")
        finding = postmortem_data.get("finding", "Sin hallazgo")
        rule_candidate = postmortem_data.get("rule_candidate", "N/A")
        confidence = postmortem_data.get("confidence", 0.0)
        raw_text_for_txt = f"Lesson ID   : {lesson_uuid}\nClasificación : {classification}\nCausa Raíz  : {root_cause}\nHallazgo    : {finding}\nRegla Prop. : {rule_candidate}\nConfianza   : {confidence}"
    else:
        classification = "RAW_TEXT"
        root_cause = str(postmortem_data)
        finding = str(postmortem_data)
        rule_candidate = "N/A"
        confidence = 0.5
        raw_text_for_txt = str(postmortem_data)
        postmortem_data = {
            "pick_id": pick_id,
            "classification": classification,
            "root_cause": root_cause,
            "finding": finding,
            "rule_candidate": rule_candidate,
            "confidence": confidence,
        }

    # ==========================================
    # 1. Persistencia Legible (TXT Individual y Maestro)
    # ==========================================
    txt_filename = f"postmortem_pick_{pick_id}_{nombre_limpio}_{timestamp}.txt"
    txt_filepath = os.path.join(POSTMORTEM_DIR, txt_filename)

    contenido_txt = f"""================================================================================
INFORME DE AUDITORÍA POST-MORTEM (BETGEMINI AUDIT ENGINE)
================================================================================
ID Apuesta       : #{pick_id}
Lesson ID        : {lesson_uuid}
Partido / Evento : {match_name}
Liga / Deporte   : {sport_league}
Fecha Auditoría  : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================================

--------------------------------------------------------------------------------
ANÁLISIS DE CAUSA RAÍZ Y HALLAZGO SABERMÉTRICO
--------------------------------------------------------------------------------
{raw_text_for_txt}

================================================================================
FIN DEL INFORME
================================================================================
"""

    with open(txt_filepath, "w", encoding="utf-8") as f:
        f.write(contenido_txt)

    master_txt_path = os.path.join(POSTMORTEM_DIR, "master_hallazgos.txt")
    with open(master_txt_path, "a", encoding="utf-8") as f_master:
        f_master.write(
            f"\n--- [LESSON: {lesson_uuid} | PICK #{pick_id} | {match_name} ({sport_league})] ---\n"
        )
        f_master.write(f"{raw_text_for_txt}\n")
        f_master.write(
            "--------------------------------------------------------------------------------\n"
        )

    # ==========================================
    # 2. Persistencia Estructurada (JSON Individual con UUID y Status)
    # ==========================================
    json_filename = f"postmortem_pick_{pick_id}_{nombre_limpio}_{timestamp}.json"
    json_filepath = os.path.join(POSTMORTEM_DIR, json_filename)

    payload_estructurado = {
        "lesson_id": lesson_uuid,
        "pick_id": pick_id,
        "match_name": match_name,
        "sport_league": sport_league,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_status": "PENDING",  # Estado inicial para gobernanza de reglas
        **postmortem_data,
    }

    with open(json_filepath, "w", encoding="utf-8") as f_json:
        json.dump(payload_estructurado, f_json, indent=4, ensure_ascii=False)

    # ==========================================
    # 3. Actualización de Base de Conocimiento Global (lessons_master.json)
    # ==========================================
    master_json_data = []
    if os.path.exists(MASTER_JSON_PATH):
        try:
            with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f_m_read:
                master_json_data = json.load(f_m_read)
                if not isinstance(master_json_data, list):
                    master_json_data = []
        except Exception:
            master_json_data = []

    master_json_data.append(payload_estructurado)

    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as f_m_write:
        json.dump(master_json_data, f_m_write, indent=4, ensure_ascii=False)

    print(f"📁 [KNOWLEDGE BASE] Reporte TXT individual: {txt_filepath}")
    print(
        f"📊 [KNOWLEDGE BASE] Reporte JSON estructurado (ID: {lesson_uuid}): {json_filepath}"
    )
    print(f"🧠 [KNOWLEDGE BASE] Master Knowledge Base actualizado: {MASTER_JSON_PATH}")
