from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import RealDictCursor
from ..database import get_cursor
from ..schemas import OrganizationCreate, OrganizationResponse, OScoreCreate, OScoreResponse

router = APIRouter()

@router.post("/organizations", response_model=OrganizationResponse, status_code=201)
def create_organization(org: OrganizationCreate, cursor: RealDictCursor = Depends(get_cursor)):
    """Créer une nouvelle organisation"""
    cursor.execute(
        """
        INSERT INTO aexia.organizations (name, sector, country)
        VALUES (%s, %s, %s)
        RETURNING org_id, name, sector, country, subscription_tier, created_at
        """,
        (org.name, org.sector, org.country)
    )
    return cursor.fetchone()


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(cursor: RealDictCursor = Depends(get_cursor)):
    """Lister toutes les organisations"""
    cursor.execute("SELECT * FROM aexia.organizations ORDER BY created_at DESC")
    return cursor.fetchall()


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: str, cursor: RealDictCursor = Depends(get_cursor)):
    """Récupérer une organisation par son ID"""
    cursor.execute("SELECT * FROM aexia.organizations WHERE org_id = %s", (org_id,))
    org = cursor.fetchone()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


@router.post("/organizations/{org_id}/aexia-o", response_model=OScoreResponse, status_code=201)
def create_o_score(org_id: str, score: OScoreCreate, cursor: RealDictCursor = Depends(get_cursor)):
    """Évaluer la maturité AEXIA-O d'une organisation"""
    cursor.execute(
        """
        INSERT INTO aexia.o_scores
        (org_id, score_f, score_a, score_g, score_c, score_o, score_m, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (org_id, score.score_f, score.score_a, score.score_g,
         score.score_c, score.score_o, score.score_m, score.notes)
    )
    return cursor.fetchone()


@router.get("/organizations/{org_id}/aexia-o/latest", response_model=OScoreResponse)
def get_latest_o_score(org_id: str, cursor: RealDictCursor = Depends(get_cursor)):
    """Dernière évaluation AEXIA-O d'une organisation"""
    cursor.execute(
        """
        SELECT * FROM aexia.o_scores
        WHERE org_id = %s
        ORDER BY evaluated_at DESC LIMIT 1
        """,
        (org_id,)
    )
    score = cursor.fetchone()
    if not score:
        raise HTTPException(404, "Aucune évaluation trouvée pour cette organisation")
    return score


@router.get("/organizations/{org_id}/aexia-o", response_model=list[OScoreResponse])
def list_o_scores(org_id: str, cursor: RealDictCursor = Depends(get_cursor)):
    """Récupérer l'historique de tous les scores O pour une organisation"""
    cursor.execute(
        "SELECT * FROM aexia.o_scores WHERE org_id = %s ORDER BY evaluated_at DESC", 
        (org_id,)
    )
    return cursor.fetchall()