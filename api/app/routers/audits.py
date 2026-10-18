from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import RealDictCursor
from psycopg2.extras import Json
from ..database import get_cursor
from ..schemas import AuditCreate, AuditResponse

router = APIRouter()

@router.post("/audits", response_model=AuditResponse, status_code=201)
def create_audit(audit: AuditCreate, cursor: RealDictCursor = Depends(get_cursor)):
    """Creer un nouvel audit"""
    cursor.execute(
        """
        INSERT INTO aexia.audits 
        (card_id, status, dcm_e_results, ecs_score, rad_value)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        (audit.card_id, audit.status,
         Json(audit.dcm_e_results) if audit.dcm_e_results else None,
         audit.ecs_score, audit.rad_value)
    )
    return cursor.fetchone()

@router.get("/audits", response_model=list[AuditResponse])
def list_audits(card_id: str = None, cursor: RealDictCursor = Depends(get_cursor)):
    """Lister les audits (filtrable par card)"""
    if card_id:
        cursor.execute("SELECT * FROM aexia.audits WHERE card_id = %s ORDER BY audit_date DESC", (card_id,))
    else:
        cursor.execute("SELECT * FROM aexia.audits ORDER BY audit_date DESC")
    return cursor.fetchall()

@router.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(audit_id: str, cursor: RealDictCursor = Depends(get_cursor)):
    """Recuperer un audit par son ID"""
    cursor.execute("SELECT * FROM aexia.audits WHERE audit_id = %s", (audit_id,))
    audit = cursor.fetchone()
    if not audit:
        raise HTTPException(404, "Audit non trouve")
    return audit