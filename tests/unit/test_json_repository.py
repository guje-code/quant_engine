import json
import tempfile
from pathlib import Path

from quant_engine.storage.json_repository import JSONRepository


class TestJSONRepository:

    # ==========================================
    # LOAD EXISTING JSON
    # ==========================================

    def test_load_existing_json(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "test.json"

            payload = {"name": "CLV", "weight": 1.5}

            file_path.write_text(json.dumps(payload), encoding="utf-8")

            result = JSONRepository.cargar_json(str(file_path))

            assert result["name"] == "CLV"
            assert result["weight"] == 1.5

    # ==========================================
    # LOAD MISSING FILE
    # ==========================================

    def test_load_missing_file_returns_empty_dict(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "missing.json"

            result = JSONRepository.cargar_json(str(file_path))

            assert result == {}

    # ==========================================
    # LOAD INVALID JSON
    # ==========================================

    def test_load_invalid_json_returns_empty_dict(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "broken.json"

            file_path.write_text("{ broken json }", encoding="utf-8")

            result = JSONRepository.cargar_json(str(file_path))

            assert result == {}

    # ==========================================
    # SAVE JSON
    # ==========================================

    def test_save_json(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "saved.json"

            payload = {"alpha": 50, "beta": 50}

            JSONRepository.guardar_json(str(file_path), payload)

            assert file_path.exists()

            loaded = json.loads(file_path.read_text(encoding="utf-8"))

            assert loaded["alpha"] == 50
            assert loaded["beta"] == 50

    # ==========================================
    # SAVE THEN LOAD
    # ==========================================

    def test_save_then_load_roundtrip(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "roundtrip.json"

            payload = {
                "PERFORMANCE": {"CLV": {"alpha_success": 55, "beta_failures": 40}}
            }

            JSONRepository.guardar_json(str(file_path), payload)

            loaded = JSONRepository.cargar_json(str(file_path))

            assert loaded == payload

    # ==========================================
    # NESTED STRUCTURES
    # ==========================================

    def test_nested_json_structure(self):

        with tempfile.TemporaryDirectory() as tmp:

            file_path = Path(tmp) / "nested.json"

            payload = {"CLUSTERS": {"VALUE_CLUSTER": {"rules": ["BFI", "CLV"]}}}

            JSONRepository.guardar_json(str(file_path), payload)

            loaded = JSONRepository.cargar_json(str(file_path))

            assert loaded["CLUSTERS"]["VALUE_CLUSTER"]["rules"] == ["BFI", "CLV"]
