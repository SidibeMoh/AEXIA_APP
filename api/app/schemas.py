from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# === ORGANIZATIONS ===
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sector: Optional[str] = None
    country: Optional[str] = Field(None, max_length=3)

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    org_id: UUID
    subscription_tier: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# === O_SCORES ===
class OScoreBase(BaseModel):
    score_f: Optional[int] = Field(None, ge=0, le=5, alias="F")
    score_a: Optional[int] = Field(None, ge=0, le=5, alias="A")
    score_g: Optional[int] = Field(None, ge=0, le=5, alias="G")
    score_c: Optional[int] = Field(None, ge=0, le=5, alias="C")
    score_o: Optional[int] = Field(None, ge=0, le=5, alias="O")
    score_m: Optional[int] = Field(None, ge=0, le=5, alias="M")
    notes: Optional[Dict[str, Any]] = None

    # Cette ligne permet à Pydantic de faire le lien entre "F" et "score_f"
    model_config = ConfigDict(populate_by_name=True)

class OScoreCreate(OScoreBase):
    pass  # On supprime org_id d'ici, car il est déjà dans l'URL !

class OScoreResponse(OScoreBase):
    id: UUID
    org_id: UUID
    evaluated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# === CARDS ===
class CardBase(BaseModel):
    system_name: str = Field(..., min_length=1, max_length=255)
    classification_ai_act: str = Field(..., pattern="^(minimal|limite|haut_risque|inacceptable)$")
    level_s: int = Field(..., ge=0, le=9)
    xai_method: str = Field(..., max_length=50)
    data: Dict[str, Any]
    version: Optional[str] = "1.0.0"

class CardCreate(CardBase):
    org_id: UUID

class CardResponse(CardBase):
    card_id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# === AUDITS ===
class AuditBase(BaseModel):
    status: str = Field(..., pattern="^(draft|completed|certified)$")
    dcm_e_results: Optional[Dict[str, Any]] = None
    ecs_score: Optional[float] = Field(None, ge=0, le=1)
    rad_value: Optional[float] = Field(None, ge=0)

class AuditCreate(AuditBase):
    card_id: UUID

class AuditResponse(AuditBase):
    audit_id: UUID
    card_id: UUID
    audit_date: datetime
    model_config = ConfigDict(from_attributes=True)

# === AUTH ===
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None