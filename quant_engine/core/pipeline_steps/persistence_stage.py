from quant_engine.storage.persistence import guardar_pick_en_db_citadel


def ejecutar_etapa_persistencia(qr_res: dict, db_path: str):
    quant_json = qr_res["quant_json"]
    risk_json = qr_res["risk_json"]

    if risk_json.get("final_verdict") == "APPROVED":
        guardar_pick_en_db_citadel(
            data_quant=quant_json,
            data_risk=risk_json,
            match_name=quant_json.get("match_name", "Unknown Match"),
            league=quant_json.get("sport_league", "GENERIC"),
            bankroll=0.0,  # El monto ya va calculado en stake_amount
            line_movement_pct=0.0,  # Capturado previamente
            steam_detected=False,
            triggered_rules=qr_res["triggered_rules_list"],
            cluster_hits=qr_res["cluster_hits"],
            var_amount=qr_res["var_amount"],
            cvar_amount=qr_res["cvar_amount"],
            sigma_snapshot=qr_res["sigma_snapshot"],
            db_path=db_path,
        )
