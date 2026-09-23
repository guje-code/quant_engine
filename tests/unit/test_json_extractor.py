from quant_engine.core.json_extractor import extract_json_response


class TestJsonExtractor:

    # ==========================================
    # EMPTY INPUT
    # ==========================================

    def test_empty_text_uses_fallback(self):
        fallback = {"value": 1}

        result = extract_json_response(raw_text="", fallback_dict=fallback)

        assert result["value"] == 1
        assert result["_fallback_used"] is True

    # ==========================================
    # MARKDOWN JSON
    # ==========================================

    def test_markdown_json_block(self):

        raw = """
        ```json
        {
            "success": true,
            "ev": 12.5
        }
        ```
        """

        result = extract_json_response(raw, {"fallback": True})

        assert result["success"] is True
        assert result["ev"] == 12.5

    # ==========================================
    # INLINE JSON
    # ==========================================

    def test_inline_json(self):

        raw = """
        Resultado:
        {
            "selection":"Boston",
            "ev":15
        }
        """

        result = extract_json_response(raw, {"fallback": True})

        assert result["selection"] == "Boston"
        assert result["ev"] == 15

    # ==========================================
    # INVALID JSON
    # ==========================================

    def test_invalid_json_uses_fallback(self):

        raw = """
        {
            invalid json here
        }
        """

        result = extract_json_response(raw, {"safe": True})

        assert result["safe"] is True
        assert result["_fallback_used"] is True

    # ==========================================
    # NON DICT JSON
    # ==========================================

    def test_list_json_uses_fallback(self):

        raw = """
        [1,2,3]
        """

        result = extract_json_response(raw, {"fallback": True})

        assert result["fallback"] is True
        assert result["_fallback_used"] is True

    def test_string_json_uses_fallback(self):

        raw = '"hello world"'

        result = extract_json_response(raw, {"fallback": True})

        assert result["fallback"] is True
        assert result["_fallback_used"] is True

    # ==========================================
    # VALID DICT JSON
    # ==========================================

    def test_valid_dict_returns_without_fallback(self):

        raw = """
        {
            "status":"ACTIVE"
        }
        """

        result = extract_json_response(raw, {"fallback": True})

        assert result["status"] == "ACTIVE"
        assert "_fallback_used" not in result

    # ==========================================
    # FALLBACK COPY
    # ==========================================

    def test_original_fallback_not_modified(self):

        fallback = {"value": 123}

        result = extract_json_response("", fallback)

        assert "_fallback_used" not in fallback
        assert "_fallback_used" in result

    # ==========================================
    # JSON WITH EXTRA TEXT
    # ==========================================

    def test_json_surrounded_by_text(self):

        raw = """
        Inicio del mensaje

        {
            "rule":"CLV",
            "roi": 4.5
        }

        Fin del mensaje
        """

        result = extract_json_response(raw, {"fallback": True})

        assert result["rule"] == "CLV"
        assert result["roi"] == 4.5
