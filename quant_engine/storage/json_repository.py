import json
import os


class JSONRepository:
    @staticmethod
    def cargar_json(filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error cargando JSON desde {filepath}: {e}")
            return {}

    @staticmethod
    def guardar_json(filepath: str, data: dict):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error guardando JSON en {filepath}: {e}")
