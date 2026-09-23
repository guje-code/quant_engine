class ClusterManager:
    def __init__(self, clusters_config: dict):
        self.clusters_config = clusters_config

    def evaluar_penalizaciones_cluster(
        self, triggered_rules_raw: list
    ) -> tuple[dict, list]:
        cluster_hits = {}
        final_rules = []

        for item in triggered_rules_raw:
            code = item["rule"]
            w_eff = item["weight_effective"]

            for cluster_name, c_info in self.clusters_config.items():
                cluster_rules = c_info.get("rules", [])
                penalty_factor = c_info.get("group_penalty_factor", 0.70)

                if code in cluster_rules:
                    cluster_hits[cluster_name] = cluster_hits.get(cluster_name, 0) + 1
                    if cluster_hits[cluster_name] >= 2:
                        w_eff = round(w_eff * penalty_factor, 4)
                        item["cluster_penalty_applied"] = cluster_name

            item["weight_effective"] = w_eff
            final_rules.append(item)

        return cluster_hits, final_rules
