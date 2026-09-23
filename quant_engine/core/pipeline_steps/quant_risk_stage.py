import time

from crewai import LLM, Crew, Process, Task
from crewai_tools import SerperDevTool

from quant_engine.core.agent_factory import AgentFactory
from quant_engine.core.json_extractor import extract_json_response
from quant_engine.core.probability_engine import ProbabilityEngine
from quant_engine.risk.portfolio_mc import simular_portfolio_var_cvar_student_t
from quant_engine.risk.position_sizing import calcular_stake_kelly


def ejecutar_etapa_quant_risk(
    match_name: str,
    sport_league: str,
    bankroll: float,
    scout_res: dict,
    rule_res: dict,
    api_key: str,
    custom_tools: dict = None,
) -> dict:
    llm = LLM(model="gemini/gemini-3.1-flash-lite", api_key=api_key, temperature=0.0)
    search_tool = SerperDevTool()

    factory = AgentFactory(llm, search_tool, custom_tools)
    quant_agent = factory.crear_quant_agent()
    risk_agent = factory.crear_risk_agent()

    task_quant = Task(
        description="Calcular EV y ajustar con Rule Engine.",
        expected_output="JSON con selection, market_type y estimated_true_probability.",
        agent=quant_agent,
    )
    task_risk = Task(
        description="Evaluar riesgo y stake.",
        expected_output="JSON con final_verdict y recommended_stake_units.",
        agent=risk_agent,
    )

    t_start = time.time()
    Crew(
        agents=[quant_agent, risk_agent],
        tasks=[task_quant, task_risk],
        process=Process.sequential,
    ).kickoff()
    t_duration = (time.time() - t_start) * 1000

    scout_json = scout_res["scout_json"]
    opening_odds = float(scout_json.get("opening_odds", 1.90))

    quant_fallback = {
        "selection": "Home",
        "market_type": "1X2",
        "estimated_true_probability": 0.55,
        "bookmaker_odds": opening_odds,
    }
    risk_fallback = {"final_verdict": "APPROVED", "recommended_stake_units": 1.0}

    quant_json = extract_json_response(task_quant.output.raw, quant_fallback)
    risk_json = extract_json_response(task_risk.output.raw, risk_fallback)

    odds = float(quant_json.get("bookmaker_odds", opening_odds))
    prob_base = float(quant_json.get("estimated_true_probability", 1.0 / odds))

    # Motor de Probabilidades y EV
    prob_final = ProbabilityEngine.ajustar_probabilidad_logit(
        prob_base, rule_res["total_adjustment"]
    )
    ev = ProbabilityEngine.calcular_expected_value(prob_final, odds)

    triggered_rules_list = rule_res["rule_audit"]["triggered"]
    triggered_codes = [r["rule"] for r in triggered_rules_list]

    # Position Sizing (Kelly)
    kelly_res = calcular_stake_kelly(
        prob_final,
        odds,
        int(scout_json.get("data_quality_score", 0.95) * 100),
        triggered_rules_list,
    )
    stake_final = kelly_res["stake_final_pct"]

    # Simulación de Riesgo (VaR / CVaR con Student-t Copula y Ledoit-Wolf)
    from quant_engine.config.settings import DB_PATH

    mc_sim = simular_portfolio_var_cvar_student_t(
        prob_final, odds, stake_final, bankroll, triggered_codes, DB_PATH
    )

    if not mc_sim["safe"]:
        return {
            "success": False,
            "reason": f"VaR (${mc_sim['var_95_amount']} / {mc_sim['var_95_pct']}%) o CVaR (${mc_sim['cvar_95_amount']} / {mc_sim['cvar_95_pct']}%) superan límites institucionales.",
        }

    monto_apuesta = round((stake_final / 100.0) * bankroll, 2)
    risk_json["recommended_stake_units"] = stake_final
    risk_json["final_verdict"] = "APPROVED" if stake_final > 0 else "REJECTED"
    quant_json["rule_engine_audit"] = rule_res

    return {
        "success": True,
        "quant_json": quant_json,
        "risk_json": risk_json,
        "odds": odds,
        "ev": ev,
        "stake_final": stake_final,
        "monto_apuesta": monto_apuesta,
        "var_amount": mc_sim["var_95_amount"],
        "var_pct": mc_sim["var_95_pct"],
        "cvar_amount": mc_sim["cvar_95_amount"],
        "cvar_pct": mc_sim["cvar_95_pct"],
        "sigma_snapshot": mc_sim["sigma_snapshot"],
        "triggered_rules_list": triggered_rules_list,
        "cluster_hits": rule_res["cluster_hits"],
        "duration_ms": t_duration,
    }
