"""Endpoints de scoring AEXIA™ v3.2."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services import scoring
from ..services.card_validator import validate_card

router = APIRouter(prefix="/scoring", tags=["Scoring"])

class OrgPillars(BaseModel):
    F: int = Field(..., ge=0, le=5)
    A: int = Field(..., ge=0, le=5)
    G: int = Field(..., ge=0, le=5)
    C: int = Field(..., ge=0, le=5)
    O: int = Field(..., ge=0, le=5)
    M: int = Field(..., ge=0, le=5)

@router.post("/org")
def score_org(body: OrgPillars):
    try: return scoring.org_profile(body.model_dump())
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))

class SysComponents(BaseModel):
    components: list[int] = Field(..., min_length=1)

@router.post("/system")
def score_system(body: SysComponents):
    try: return scoring.system_profile(body.components)
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))

class DecisionInput(BaseModel):
    org_level: int = Field(..., ge=0, le=5)
    sys_level: int = Field(..., ge=0, le=9)
    risk: str = "limite"

@router.post("/decision")
def decide(body: DecisionInput):
    try: d = scoring.deployment_decision(body.org_level, body.sys_level, body.risk)
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))
    return {"code": d.code, "label": d.label, "authorized": d.authorized, "conditions": d.conditions}

class RADInput(BaseModel):
    t_months: list[float]
    s_att: list[float]
    s_eff: list[float]
    beta: int = Field(..., ge=1, le=4)

@router.post("/rad/system")
def rad_system(body: RADInput):
    try: value = scoring.rad_system(body.t_months, body.s_att, body.s_eff, body.beta)
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))
    return {"rad": value}

class RADPortfolioInput(BaseModel):
    rad_values: list[float]
    T_months: float = Field(..., gt=0)

@router.post("/rad/portfolio")
def rad_portfolio(body: RADPortfolioInput):
    total = scoring.rad_portfolio(body.rad_values)
    norm = scoring.rad_normalized(total, len(body.rad_values), body.T_months)
    return {"rad_portfolio": total, "rad_normalized": norm, "interpretation": scoring.rad_interpretation(norm)}

class ECSInput(BaseModel):
    phi_x: list[float]
    neighbour_phis: list[list[float]]

@router.post("/ecs")
def compute_ecs(body: ECSInput):
    try: value = scoring.ecs(body.phi_x, body.neighbour_phis)
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))
    return {"ecs": value}

class CardPayload(BaseModel):
    card: dict

@router.post("/card/validate")
def card_validate(body: CardPayload):
    ok, errors = validate_card(body.card)
    return {"valid": ok, "errors": errors}

# ==========================================
# RAD-lite (V3.1) - Route principale
# ==========================================
class RADLiteInput(BaseModel):
    s_att: list[float] = Field(..., min_length=1)
    s_eff: list[float] = Field(..., min_length=1)
    beta: list[int] = Field(..., min_length=1)


@router.post("/rad-lite/system")
def compute_rad_lite(body: RADLiteInput):
    """Calcule le RAD-lite (V3.1) - indicateur principal."""
    try:
        result = scoring.rad_lite(body.s_att, body.s_eff, body.beta)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result