import math
import numpy as np


def _dixon_coles_tau(
    home_goals: int,
    away_goals: int,
    lambda_home: float,
    lambda_away: float,
    rho: float,
) -> float:
    """Dixon-Coles-korjauskerroin matalille maalimäärille (0-0, 0-1, 1-0, 1-1)."""
    if home_goals == 0 and away_goals == 0:
        return max(0.0, 1.0 - (lambda_home * lambda_away * rho))
    if home_goals == 0 and away_goals == 1:
        return max(0.0, 1.0 + (lambda_home * rho))
    if home_goals == 1 and away_goals == 0:
        return max(0.0, 1.0 + (lambda_away * rho))
    if home_goals == 1 and away_goals == 1:
        return max(0.0, 1.0 - rho)
    return 1.0


def _fair_odds(prob: float) -> float | None:
    """Palauttaa reilun rajakertoimen (1 / p) tai None, jos todennäköisyys on <= 0."""
    if prob <= 0.0:
        return None
    return round(1.0 / prob, 2)


def laske_kaikki_todennakoisyydet(
    model_xg_home: float,
    model_xg_away: float,
    max_maalit: int = 10,
    rho: float = -0.08,
    ou_lines: tuple[float, ...] = (1.5, 2.5, 3.5, 5.5, 6.5),
) -> dict:
    """
    Laskee Dixon-Coles-korjatun Poisson-matriisin sekä 1X2-, 1X-/X2-,
    Over/Under- ja BTTS-todennäköisyydet.
    """
    if model_xg_home < 0 or model_xg_away < 0:
        raise ValueError("Odotettujen maalien (xG) tulee olla >= 0.")

    home_pmf = np.array(
        [
            math.exp(-model_xg_home) * (model_xg_home**i) / math.factorial(i)
            for i in range(max_maalit + 1)
        ],
        dtype=float,
    )
    away_pmf = np.array(
        [
            math.exp(-model_xg_away) * (model_xg_away**j) / math.factorial(j)
            for j in range(max_maalit + 1)
        ],
        dtype=float,
    )

    matriisi = np.outer(home_pmf, away_pmf)

    if rho != 0.0:
        for h in range(min(2, max_maalit + 1)):
            for a in range(min(2, max_maalit + 1)):
                matriisi[h, a] *= _dixon_coles_tau(
                    h, a, model_xg_home, model_xg_away, rho
                )

    total = float(np.sum(matriisi))
    if total > 0.0:
        matriisi = matriisi / total

    # h = kotimaalit (rivi), a = vierasmaalit (sarake)
    kotivoitto = float(np.sum(np.triu(matriisi, 1)))
    tasapeli = float(np.trace(matriisi))
    vierasvoitto = float(np.sum(np.tril(matriisi, -1)))

    over_under: dict[str, dict[str, float]] = {}
    for line in ou_lines:
        p_over = 0.0
        p_under = 0.0
        p_push = 0.0
        for h in range(max_maalit + 1):
            for a in range(max_maalit + 1):
                p = float(matriisi[h, a])
                tot_goals = h + a
                if tot_goals > line:
                    p_over += p
                elif tot_goals < line:
                    p_under += p
                else:
                    p_push += p
        over_under[str(line)] = {
            "over": p_over,
            "under": p_under,
            "push": p_push,
        }

    btts_kylla = float(np.sum(matriisi[1:, 1:])) if max_maalit >= 1 else 0.0
    btts_ei = max(0.0, 1.0 - btts_kylla)

    ou_25 = over_under.get("2.5", {"over": 0.0, "under": 0.0})

    return {
        "kv": kotivoitto,
        "tp": tasapeli,
        "vv": vierasvoitto,
        "1x": kotivoitto + tasapeli,
        "x2": vierasvoitto + tasapeli,
        "over_2.5": ou_25["over"],
        "under_2.5": ou_25["under"],
        "ou": over_under,
        "btts_kylla": btts_kylla,
        "btts_ei": btts_ei,
        "matriisi": matriisi,
    }


def calculate_match_markets(
    lambda_home: float,
    lambda_away: float,
    rho: float = -0.08,
    max_goals: int = 10,
    ou_lines: tuple[float, ...] = (1.5, 2.5, 3.5, 5.5, 6.5),
) -> dict:
    """
    Palauttaa selkeän rakenteen todennäköisyyksistä ja rajakertoimista
    1X2-, 1X-/X2- ja Over/Under-markkinoille.
    """
    raw = laske_kaikki_todennakoisyydet(
        model_xg_home=lambda_home,
        model_xg_away=lambda_away,
        max_maalit=max_goals,
        rho=rho,
        ou_lines=ou_lines,
    )

    p_home = raw["kv"]
    p_draw = raw["tp"]
    p_away = raw["vv"]
    p_1x = raw["1x"]
    p_x2 = raw["x2"]
    p_12 = p_home + p_away

    formatted_ou: dict[str, dict] = {}
    for line_key, vals in raw["ou"].items():
        formatted_ou[line_key] = {
            "over_prob": round(vals["over"], 4),
            "over_fair_odds": _fair_odds(vals["over"]),
            "under_prob": round(vals["under"], 4),
            "under_fair_odds": _fair_odds(vals["under"]),
            "push_prob": round(vals["push"], 4),
        }

    return {
        "lambdas": {
            "home": round(lambda_home, 3),
            "away": round(lambda_away, 3),
            "total": round(lambda_home + lambda_away, 3),
            "rho": rho,
        },
        "markets_1x2": {
            "1_prob": round(p_home, 4),
            "1_fair_odds": _fair_odds(p_home),
            "X_prob": round(p_draw, 4),
            "X_fair_odds": _fair_odds(p_draw),
            "2_prob": round(p_away, 4),
            "2_fair_odds": _fair_odds(p_away),
        },
        "double_chance": {
            "1X_prob": round(p_1x, 4),
            "1X_fair_odds": _fair_odds(p_1x),
            "X2_prob": round(p_x2, 4),
            "X2_fair_odds": _fair_odds(p_x2),
            "12_prob": round(p_12, 4),
            "12_fair_odds": _fair_odds(p_12),
        },
        "over_under": formatted_ou,
        "matrix": raw["matriisi"],
    }