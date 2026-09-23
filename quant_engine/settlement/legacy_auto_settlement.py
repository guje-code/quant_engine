from quant_engine.settlement.result_resolver import ResultResolver
from quant_engine.settlement.settlement_facade import SettlementFacade


def ejecutar_auto_settlement_masivo():
    """
    Busca apuestas pendientes, resuelve sus marcadores mediante ESPN o Web Fallback,
    evalúa el mercado y ejecuta SettlementFacade.close_pick para cerrar el ciclo completo
    (actualización de base de datos, feedback bayesiano, ROIs, estados y post-mortem).
    """
    pendientes = SettlementFacade.get_pending_picks()

    if not pendientes:
        print("ℹ️ No hay apuestas pendientes por liquidar.")
        return 0

    liquidadas = 0

    for pick in pendientes:
        pick_id = pick["id"]
        match = pick["match_name"]
        league = pick["sport_league"]
        selection = pick["selection"]
        mkt_type = pick.get("market_type", "Moneyline")
        created_at = pick["created_at"]

        # 1. Obtener resultado del evento usando los proveedores dedicados
        info_marcador = ResultResolver.obtener_resultado_evento(
            match, league, str(created_at)
        )

        if info_marcador.get("status") == "FINAL":
            # 2. Evaluar el resultado del pick
            res_eval = ResultResolver.evaluar_pick(
                selection, mkt_type, info_marcador["scores"]
            )

            if res_eval in ["WIN", "LOSS", "PUSH"]:
                # 3. Delegar la liquidación maestra a SettlementFacade
                SettlementFacade.close_pick(
                    pick_id=pick_id,
                    result=res_eval,
                    run_postmortem=True,
                    marcador_real=str(info_marcador["scores"]),
                )
                liquidadas += 1

    print(f"✨ Proceso de auto-settlement finalizado. Picks liquidados: {liquidadas}")
    return liquidadas


if __name__ == "__main__":
    ejecutar_auto_settlement_masivo()
