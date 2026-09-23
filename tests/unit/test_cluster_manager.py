from quant_engine.risk.cluster_manager import ClusterManager


class TestClusterManager:

    # ==========================================
    # NO CLUSTERS
    # ==========================================

    def test_no_clusters(self):

        cm = ClusterManager({})

        rules = [{"rule": "BFI", "weight_effective": 1.0}]

        cluster_hits, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert cluster_hits == {}
        assert final_rules[0]["weight_effective"] == 1.0

    # ==========================================
    # SINGLE HIT
    # ==========================================

    def test_single_rule_in_cluster_no_penalty(self):

        clusters = {
            "VALUE_CLUSTER": {"rules": ["BFI", "CLV"], "group_penalty_factor": 0.7}
        }

        cm = ClusterManager(clusters)

        rules = [{"rule": "BFI", "weight_effective": 1.0}]

        cluster_hits, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert cluster_hits["VALUE_CLUSTER"] == 1
        assert final_rules[0]["weight_effective"] == 1.0

    # ==========================================
    # DOUBLE HIT
    # ==========================================

    def test_cluster_penalty_applied(self):

        clusters = {
            "VALUE_CLUSTER": {"rules": ["BFI", "CLV"], "group_penalty_factor": 0.7}
        }

        cm = ClusterManager(clusters)

        rules = [
            {"rule": "BFI", "weight_effective": 1.0},
            {"rule": "CLV", "weight_effective": 1.0},
        ]

        cluster_hits, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert cluster_hits["VALUE_CLUSTER"] >= 2

        assert final_rules[1]["weight_effective"] <= 1.0

    # ==========================================
    # PENALTY FACTOR
    # ==========================================

    def test_penalty_factor_used(self):

        clusters = {
            "VALUE_CLUSTER": {"rules": ["BFI", "CLV"], "group_penalty_factor": 0.5}
        }

        cm = ClusterManager(clusters)

        rules = [
            {"rule": "BFI", "weight_effective": 2.0},
            {"rule": "CLV", "weight_effective": 2.0},
        ]

        _, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert final_rules[1]["weight_effective"] <= 1.0

    # ==========================================
    # NON CLUSTER RULES
    # ==========================================

    def test_non_cluster_rule_unchanged(self):

        clusters = {
            "VALUE_CLUSTER": {"rules": ["BFI", "CLV"], "group_penalty_factor": 0.5}
        }

        cm = ClusterManager(clusters)

        rules = [{"rule": "QBI", "weight_effective": 1.5}]

        _, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert final_rules[0]["weight_effective"] == 1.5

    # ==========================================
    # EMPTY INPUT
    # ==========================================

    def test_empty_rules(self):

        cm = ClusterManager({})

        cluster_hits, final_rules = cm.evaluar_penalizaciones_cluster([])

        assert cluster_hits == {}
        assert final_rules == []

    # ==========================================
    # MULTIPLE CLUSTERS
    # ==========================================

    def test_multiple_clusters(self):

        clusters = {
            "CLUSTER_A": {"rules": ["BFI", "CLV"], "group_penalty_factor": 0.7},
            "CLUSTER_B": {"rules": ["QBI", "AVR"], "group_penalty_factor": 0.8},
        }

        cm = ClusterManager(clusters)

        rules = [
            {"rule": "BFI", "weight_effective": 1.0},
            {"rule": "CLV", "weight_effective": 1.0},
            {"rule": "QBI", "weight_effective": 1.0},
            {"rule": "AVR", "weight_effective": 1.0},
        ]

        cluster_hits, final_rules = cm.evaluar_penalizaciones_cluster(rules)

        assert "CLUSTER_A" in cluster_hits
        assert "CLUSTER_B" in cluster_hits
