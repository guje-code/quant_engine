import logging
import re
import time
from datetime import datetime, timedelta

import requests
from rapidfuzz import fuzz

from quant_engine.config.settings import FUZZY_MATCH_THRESHOLD

# Sesión persistente de requests para optimizar conexiones concurrentes con ESPN
_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
)

# Caché TTL en memoria para evitar llamadas repetidas: {url: (data_json, timestamp)}
_ESPN_CACHE = {}
_CACHE_TTL_SECONDS = 300  # 5 minutos


def _clean_expired_cache():
    """Purgar entradas expiradas del diccionario para evitar crecimiento desmedido en memoria."""
    now = time.time()
    expired_keys = [
        url
        for url, (_, timestamp) in _ESPN_CACHE.items()
        if now - timestamp > _CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        del _ESPN_CACHE[key]


def generar_endpoints_espn(sport_league: str, fecha_pick_str: str) -> list:
    sl = str(sport_league).lower()
    endpoints = []

    fechas = []
    try:
        dt_pick = datetime.strptime(fecha_pick_str[:10], "%Y-%m-%d")
        fechas.append(dt_pick.strftime("%Y%m%d"))
        fechas.append((dt_pick - timedelta(days=1)).strftime("%Y%m%d"))
        fechas.append((dt_pick + timedelta(days=1)).strftime("%Y%m%d"))
    except Exception:
        pass

    hoy = datetime.now().strftime("%Y%m%d")
    if hoy not in fechas:
        fechas.append(hoy)

    # Cobertura ortográfica exhaustiva (beisbol / béisbol / beísbol)
    if any(
        k in sl
        for k in ["mlb", "lmb", "lmp", "npb", "kbo", "beisbol", "béisbol", "beísbol"]
    ):
        for f in fechas:
            endpoints.append(
                f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={f}"
            )
    elif any(k in sl for k in ["nba", "wnba", "baloncesto", "basketball"]):
        for f in fechas:
            endpoints.append(
                f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={f}"
            )
    elif any(
        k in sl
        for k in ["tenis", "tennis", "atp", "wta", "open", "wimbledon", "garros"]
    ):
        for f in fechas:
            endpoints.append(
                f"https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard?dates={f}"
            )
            endpoints.append(
                f"https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard?dates={f}"
            )
        endpoints.append(
            "https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard"
        )
        endpoints.append(
            "https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard"
        )
    else:
        is_saudi = any(
            k in sl for k in ["saudi", "khaleej", "nassr", "hilal", "ittihad"]
        )
        for f in fechas:
            if is_saudi:
                endpoints.append(
                    f"https://site.api.espn.com/apis/site/v2/sports/soccer/sau.1/scoreboard?dates={f}"
                )
            endpoints.append(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={f}"
            )

    return endpoints


def coincidencia_evento(match_name: str, event_name: str, short_name: str) -> bool:
    """
    Validación avanzada de eventos utilizando Fuzzy Matching (RapidFuzz)
    con el umbral centralizado en settings.py.
    """
    equipos = re.split(r"\s+vs\.?\s+|\s+@\s+|\s+-\s+", match_name, flags=re.IGNORECASE)
    if len(equipos) < 2:
        return False

    eq_a = equipos[0].strip().lower()
    eq_b = equipos[1].strip().lower()

    texto_evento = f"{event_name} {short_name}".lower()

    # Evaluamos utilizando el umbral global FUZZY_MATCH_THRESHOLD
    similitud_a = fuzz.token_sort_ratio(eq_a, texto_evento)
    similitud_b = fuzz.token_sort_ratio(eq_b, texto_evento)

    return similitud_a >= FUZZY_MATCH_THRESHOLD and similitud_b >= FUZZY_MATCH_THRESHOLD


def consultar_espn(match_name: str, sport_league: str, created_at: str) -> dict:
    _clean_expired_cache()

    urls = generar_endpoints_espn(sport_league, created_at)
    now = time.time()

    for url in urls:
        t_start = time.perf_counter()
        events_found = 0
        match_found = False
        data = None

        try:
            if url in _ESPN_CACHE:
                cached_data, cached_time = _ESPN_CACHE[url]
                if now - cached_time < _CACHE_TTL_SECONDS:
                    data = cached_data
                    logging.info(
                        f"[ESPN CACHE HIT] Sirviendo datos en caché para URL: {url}"
                    )

            if not data:
                resp = _SESSION.get(url, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    _ESPN_CACHE[url] = (data, now)

            if data:
                events = data.get("events", [])
                events_found = len(events)

                for event in events:
                    e_name = event.get("name", "")
                    e_short = event.get("shortName", "")

                    if coincidencia_evento(match_name, e_name, e_short):
                        match_found = True
                        status_type = (
                            event.get("status", {}).get("type", {}).get("name", "")
                        )

                        if status_type in [
                            "STATUS_FINAL",
                            "STATUS_FULL_TIME",
                            "STATUS_FINISHED",
                        ]:
                            competitors = event["competitions"][0]["competitors"]
                            scores = {}
                            for comp in competitors:
                                t_name = comp.get("athlete", {}).get(
                                    "displayName",
                                    comp.get("team", {}).get("displayName", ""),
                                )
                                if "linescores" in comp:
                                    s_val = float(
                                        sum(
                                            1
                                            for ls in comp["linescores"]
                                            if ls.get("winner", False)
                                        )
                                    )
                                    if s_val == 0 and "score" in comp:
                                        s_val = float(comp.get("score", 0))
                                else:
                                    s_val = float(comp.get("score", 0))
                                scores[t_name] = s_val

                            duration_ms = (time.perf_counter() - t_start) * 1000.0
                            logging.info(
                                f"[ESPN TELEMETRY] Endpoint Hit: {url} | Tiempo: {duration_ms:.1f}ms | Eventos: {events_found} | Match Encontrado: True"
                            )
                            return {"status": "FINAL", "scores": scores}

        except Exception as e:
            logging.warning(f"Error consultando ESPN endpoint {url}: {e}")

        duration_ms = (time.perf_counter() - t_start) * 1000.0
        logging.info(
            f"[ESPN TELEMETRY] Endpoint Hit: {url} | Tiempo: {duration_ms:.1f}ms | Eventos: {events_found} | Match Encontrado: {match_found}"
        )

    return {"status": "PENDING"}
