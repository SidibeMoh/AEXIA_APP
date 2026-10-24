"""
AEXIA™ v3.2 — Moteur de scoring
================================
Implémente les règles du framework AEXIA™ v3.2
(Mohamadou SIDIBE, AI BIAIS INITIATIVE, DOI 10.5281/zenodo.23126471).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

PILLARS: tuple[str, ...] = ("F", "A", "G", "C", "O", "M")
PILLAR_WEIGHTS: dict[str, float] = {
    "F": 0.20, "A": 0.15, "G": 0.20, "C": 0.20, "O": 0.15, "M": 0.10,
}

ORG_LEVEL_NAMES: dict[int, str] = {
    0: "Inexistant", 1: "Initial", 2: "Défini", 3: "Géré", 4: "Avancé", 5: "Excellence",
}

SYS_LEVEL_NAMES: dict[int, str] = {
    0: "Premiers principes", 1: "Recherche orientée", 2: "Preuve de principe",
    3: "Développement système", 4: "Preuve de concept", 5: "Capacité démontrée",
    6: "Développement applicatif", 7: "Intégration", 8: "Qualifié", 9: "En service surveillé",
}

RISK_LEVELS: tuple[str, ...] = ("minimal", "limite", "haut_risque", "inacceptable")

def org_published_level(pillar_levels: dict[str, int]) -> int:
    _validate_pillars(pillar_levels)
    return min(pillar_levels.values())

def org_weighted_average(pillar_levels: dict[str, int]) -> float:
    _validate_pillars(pillar_levels)
    return round(sum(PILLAR_WEIGHTS[p] * pillar_levels[p] for p in PILLARS), 3)

def org_profile(pillar_levels: dict[str, int]) -> dict:
    _validate_pillars(pillar_levels)
    published = org_published_level(pillar_levels)
    weakest = min(pillar_levels, key=pillar_levels.get)
    return {
        "pillars": dict(pillar_levels), "published_level": published,
        "published_label": ORG_LEVEL_NAMES[published], "weighted_average": org_weighted_average(pillar_levels),
        "weakest_pillar": weakest, "weakest_level": pillar_levels[weakest],
        "display_drift": round(org_weighted_average(pillar_levels) - published, 3),
    }

def _validate_pillars(pillar_levels: dict[str, int]) -> None:
    missing = set(PILLARS) - set(pillar_levels)
    extra = set(pillar_levels) - set(PILLARS)
    if missing: raise ValueError(f"Piliers manquants : {sorted(missing)}")
    if extra: raise ValueError(f"Piliers inconnus : {sorted(extra)}")
    for p, lvl in pillar_levels.items():
        if not isinstance(lvl, int) or not 0 <= lvl <= 5:
            raise ValueError(f"Pilier {p} : niveau {lvl} invalide (attendu 0-5)")

def system_published_level(component_levels: Sequence[int]) -> int:
    if not component_levels: raise ValueError("Au moins un composant est requis")
    for lvl in component_levels:
        if not isinstance(lvl, int) or not 0 <= lvl <= 9:
            raise ValueError(f"Niveau composant {lvl} invalide (attendu 0-9)")
    return min(component_levels)

def system_profile(component_levels: Sequence[int]) -> dict:
    published = system_published_level(component_levels)
    return {"components": list(component_levels), "published_level": published, "published_label": SYS_LEVEL_NAMES[published]}

@dataclass(frozen=True)
class Decision:
    code: str
    label: str
    authorized: bool
    conditions: list[str] = field(default_factory=list)

def _sys_band(sys_level: int) -> str:
    if sys_level <= 5: return "S0-S5"
    if sys_level <= 7: return "S6-S7"
    return "S8-S9"

def _org_band(org_level: int) -> str:
    if org_level <= 1: return "N0-N1"
    return f"N{org_level}" if org_level <= 3 else "N4-N5"

def deployment_decision(org_level: int, sys_level: int, risk: str = "limite") -> Decision:
    if not 0 <= org_level <= 5: raise ValueError(f"org_level {org_level} invalide (0-5)")
    if not 0 <= sys_level <= 9: raise ValueError(f"sys_level {sys_level} invalide (0-9)")
    if risk not in RISK_LEVELS: raise ValueError(f"risk '{risk}' invalide — attendu {RISK_LEVELS}")

    org, sysb = _org_band(org_level), _sys_band(sys_level)

    if org == "N0-N1" and sysb == "S0-S5": return Decision("TOLERE_EXPLORATOIRE", "Toléré — phase exploratoire", True)
    if org == "N0-N1" and sysb == "S6-S7": return Decision("INTERDIT", "Interdit — l'organisation n'a pas les contrôles", False)
    if org == "N0-N1" and sysb == "S8-S9": return Decision("ALERTE_MAJEURE", "Alerte majeure — système en production sans gouvernance", False)
    if org == "N2" and sysb == "S0-S5": return Decision("TOLERE_TRACE", "Toléré avec traçabilité", True, ["Journalisation des explications obligatoire"])
    if org == "N2" and sysb == "S6-S7": return Decision("CONDITIONNEL", "Autorisé sous condition — porte franchie en comité", True, ["Décision formelle DGC requise"])
    if org == "N2" and sysb == "S8-S9":
        if risk in ("minimal", "limite"): return Decision("LIMITE_OK", "Autorisé pour risque limité", True)
        return Decision("HAUT_RISQUE_NON", "Refusé — haut risque interdit à ce niveau de maturité", False)
    if org == "N3" and sysb in ("S0-S5", "S6-S7"): return Decision("NORMAL", "Normal", True)
    if org == "N3" and sysb == "S8-S9": return Decision("HAUT_RISQUE_SURVEILLE", "Autorisé, y compris haut risque, sous surveillance mesurée", True, ["Surveillance art. 72 active"])
    if sysb in ("S0-S5", "S6-S7"): return Decision("NORMAL", "Normal", True)
    return Decision("NORMAL_AUTO", "Normal — rétrogradation automatisée sur dérive", True, ["Seuils de dérive armés", "Procédure de rétrogradation testée"])

HALF_LIFE_MONTHS = 7.0
LAMBDA = math.log(2) / HALF_LIFE_MONTHS
S_MAX = 9
BETA_MAX = 4

def rad_system(t_months: Sequence[float], s_att: Sequence[float], s_eff: Sequence[float], beta: int) -> float:
    if not (len(t_months) == len(s_att) == len(s_eff)): raise ValueError("t, s_att, s_eff doivent avoir la même longueur")
    if len(t_months) < 2: raise ValueError("Au moins 2 points temporels requis")
    if beta not in (1, 2, 3, 4): raise ValueError("beta doit être dans {1,2,3,4}")
    T = t_months[-1]
    integral = 0.0
    for k in range(len(t_months) - 1):
        t0, t1 = t_months[k], t_months[k + 1]
        dt = t1 - t0
        gap0, gap1 = max(0.0, s_att[k] - s_eff[k]), max(0.0, s_att[k + 1] - s_eff[k + 1])
        f0, f1 = math.exp(-LAMBDA * (T - t0)) * gap0, math.exp(-LAMBDA * (T - t1)) * gap1
        integral += 0.5 * (f0 + f1) * dt
    return integral * beta

def rad_portfolio(rad_values: Iterable[float]) -> float:
    return float(sum(rad_values))

def rad_normalized(rad_portfolio_value: float, n_systems: int, T_months: float) -> float:
    if n_systems <= 0: raise ValueError("n_systems doit être > 0")
    denominator = n_systems * BETA_MAX * S_MAX * (1 - math.exp(-LAMBDA * T_months)) / LAMBDA
    return max(0.0, min(1.0, rad_portfolio_value / denominator))

def rad_interpretation(rad_norm: float) -> str:
    if rad_norm < 0.10: return "Organisation alignée"
    if rad_norm < 0.25: return "Écarts modérés — plan d'amélioration"
    return "Dette critique — arbitrage budgétaire nécessaire"

def ecs(phi_x: Sequence[float], neighbour_phis: Sequence[Sequence[float]]) -> float:
    if not neighbour_phis: raise ValueError("Au moins un voisin requis")
    norm_x = sum(abs(v) for v in phi_x)
    delta = 1e-6 * max(norm_x, 1.0)
    n = len(neighbour_phis)
    total = 0.0
    for phi_k in neighbour_phis:
        if len(phi_k) != len(phi_x): raise ValueError("Dimensions d'explications incompatibles")
        l1 = sum(abs(a - b) for a, b in zip(phi_x, phi_k))
        total += l1 / (norm_x + delta)
    return max(0.0, 1.0 - min(1.0, total / n))

def ecs_model(scores: Sequence[float]) -> float:
    if not scores: raise ValueError("Liste de scores vide")
    return sum(scores) / len(scores)

# ==========================================
# RAD-lite (V3.1) - Indicateur principal
# ==========================================
def rad_lite(s_att: Sequence[float], s_eff: Sequence[float], beta: Sequence[int]) -> dict:
    """
    Calcule le RAD-lite (V3.1) : part pondérée du chemin de maturité restant.
    
    Formule : RAD-lite = Σᵢ βᵢ · max(0, S_att,i − S_eff,i) / Σᵢ βᵢ · S_att,i
    
    Args:
        s_att: niveaux attendus (1 à 5)
        s_eff: niveaux effectifs (1 à 5)
        beta: coefficients de criticité (1 à 4), alignés sur s_att/s_eff
    
    Returns:
        dict avec rad_lite (0-1), total_gap, total_expected, worst_share
    """
    if not (len(s_att) == len(s_eff) == len(beta)):
        raise ValueError("s_att, s_eff et beta doivent avoir la même longueur")
    if len(s_att) == 0:
        raise ValueError("Au moins un système est requis")
    for b in beta:
        if b not in (1, 2, 3, 4):
            raise ValueError(f"beta doit être dans {{1,2,3,4}}, reçu {b}")
    
    num = 0.0  # Σ βᵢ · max(0, S_att,i − S_eff,i)
    den = 0.0  # Σ βᵢ · S_att,i
    per_system_gap = []
    
    for i in range(len(s_att)):
        gap = max(0.0, s_att[i] - s_eff[i])
        weighted_gap = beta[i] * gap
        num += weighted_gap
        den += beta[i] * s_att[i]
        per_system_gap.append(weighted_gap)
    
    rad_lite_value = num / den if den > 0 else 0.0
    
    # Share du pire système (celui qui explique le plus grand écart pondéré)
    worst_share = (max(per_system_gap) / num) if num > 0 else 0.0
    
    return {
        "rad_lite": round(rad_lite_value, 4),
        "total_gap": round(num, 2),
        "total_expected": round(den, 2),
        "worst_share": round(worst_share, 4),
    }