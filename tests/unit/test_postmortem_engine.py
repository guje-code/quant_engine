from unittest.mock import Mock, patch

from quant_engine.settlement.postmortem_engine import (
    PostMortemEngine,
    analizar_post_mortem,
)


class TestPostMortemEngine:

    # ==========================================
    # SUCCESS CASE
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_successful_postmortem(self, mock_agent, mock_task, mock_crew):

        fake_result = Mock()

        fake_result.raw = """
        {
            "classification": "BAD_BEAT",
            "root_cause": "Bullpen collapse",
            "finding": "Late inning volatility",
            "rule_candidate": "Reduce exposure",
            "confidence": 0.84
        }
        """

        mock_crew.return_value.kickoff.return_value = fake_result

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Boston vs Yankees",
            sport_league="MLB",
            selection="Boston",
            odds=2.0,
            resultado="LOSS",
        )

        assert result["classification"] == "BAD_BEAT"
        assert result["confidence"] == 0.84

    # ==========================================
    # MARKDOWN JSON
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_markdown_json_response(self, mock_agent, mock_task, mock_crew):

        fake_result = Mock()

        fake_result.raw = """
        ```json
        {
            "classification": "MODEL_ERROR",
            "root_cause": "Bad feature",
            "finding": "Calibration issue",
            "rule_candidate": "Retrain model",
            "confidence": 0.90
        }
        ```
        """

        mock_crew.return_value.kickoff.return_value = fake_result

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        assert result["classification"] == "MODEL_ERROR"

    # ==========================================
    # INVALID JSON
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_invalid_json_triggers_fallback(self, mock_agent, mock_task, mock_crew):

        fake_result = Mock()

        fake_result.raw = """
        invalid json
        """

        mock_crew.return_value.kickoff.return_value = fake_result

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        assert "classification" in result
        assert result["classification"] == "BAD_BEAT"

    # ==========================================
    # NON DICT JSON
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_non_dict_json_triggers_fallback(self, mock_agent, mock_task, mock_crew):

        fake_result = Mock()

        fake_result.raw = """
        [1,2,3]
        """

        mock_crew.return_value.kickoff.return_value = fake_result

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        assert result["classification"] == "BAD_BEAT"

    # ==========================================
    # EXCEPTION FALLBACK
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_exception_triggers_fallback(self, mock_agent, mock_task, mock_crew):

        mock_crew.return_value.kickoff.side_effect = Exception("LLM Failure")

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        assert result["classification"] == "BAD_BEAT"

    # ==========================================
    # RETURN CONTRACT
    # ==========================================

    @patch("quant_engine.settlement.postmortem_engine.Crew")
    @patch("quant_engine.settlement.postmortem_engine.Task")
    @patch("quant_engine.settlement.postmortem_engine.Agent")
    def test_return_contract(self, mock_agent, mock_task, mock_crew):

        fake_result = Mock()

        fake_result.raw = """
        {
            "classification": "DATA_ERROR",
            "root_cause": "Missing data",
            "finding": "Injury report",
            "rule_candidate": "Add injury filter",
            "confidence": 0.75
        }
        """

        mock_crew.return_value.kickoff.return_value = fake_result

        result = PostMortemEngine.analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        expected = {
            "classification",
            "root_cause",
            "finding",
            "rule_candidate",
            "confidence",
        }

        assert expected.issubset(result.keys())

    # ==========================================
    # WRAPPER FUNCTION
    # ==========================================

    @patch(
        "quant_engine.settlement.postmortem_engine.PostMortemEngine.analizar_post_mortem"
    )
    def test_wrapper_function(self, mock_engine):

        mock_engine.return_value = {"classification": "BAD_BEAT"}

        result = analizar_post_mortem(
            pick_id=1,
            match_name="Match",
            sport_league="MLB",
            selection="A",
            odds=2.0,
            resultado="LOSS",
        )

        assert result["classification"] == "BAD_BEAT"
