import os
import sqlite3

from quant_engine.config.settings import DB_PATH


def listar_apuestas_pendientes() -> list:
    """Retorna una lista de diccionarios con todas las apuestas pendientes de resolver."""
    if not os.path.exists(DB_PATH):
        print(f"No se encontro la base de datos en {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, match_name, sport_league, selection, bookmaker_odds, recommended_stake_amount, created_at 
        FROM historical_picks 
        WHERE actual_result = "PENDING"
    """)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def actualizar_resultado_db(
    pick_id: int, resultado: str, profit_units: float = None
) -> dict:
    """
    Actualiza el resultado de un pick de manera transaccional en SQLite.
    Asegura el cálculo consistente de profit basado en el monto monetario apostado.
    """
    if not os.path.exists(DB_PATH):
        raise ValueError(f"No se encontro la base de datos en {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT match_name, sport_league, selection, bookmaker_odds, recommended_stake_amount 
        FROM historical_picks 
        WHERE id = ?
    """,
        (pick_id,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise ValueError(f"No se encontro la apuesta con ID #{pick_id}")

    match_name, sport_league, selection, odds, stake = row
    resultado_upper = resultado.upper()

    # Estandarización robusta: recommended_stake_amount representa el monto monetario total apostado.
    # Por tanto, el profit neto es: stake * (odds - 1.0) para WIN, y -stake para LOSS.
    if profit_units is None:
        if resultado_upper == "WIN":
            profit_units = round(stake * (odds - 1.0), 2)
        elif resultado_upper == "LOSS":
            profit_units = round(-stake, 2)
        elif resultado_upper == "PUSH":
            profit_units = 0.0
        else:
            conn.close()
            raise ValueError(
                f"Resultado '{resultado}' no valido. Usar WIN, LOSS o PUSH."
            )

    cursor.execute(
        """
        UPDATE historical_picks 
        SET actual_result = ?, profit_units = ?
        WHERE id = ?
    """,
        (resultado_upper, profit_units, pick_id),
    )

    conn.commit()
    conn.close()

    return {
        "pick_id": pick_id,
        "match_name": match_name,
        "sport_league": sport_league,
        "selection": selection,
        "odds": odds,
        "stake": stake,
        "actual_result": resultado_upper,
        "profit_units": profit_units,
    }
