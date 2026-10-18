from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import RealDictCursor
from psycopg2.extras import Json
from ..database import get_cursor
from ..schemas import CardCreate, CardResponse

router = APIRouter()

@router.post("/cards", response_model=CardResponse, status_code=201)
def create_card(card: CardCreate, cursor: RealDictCursor = Depends(get_cursor)):
    """Creer une nouvelle AEXIA Card"""
    cursor.execute(
        """
        INSERT INTO aexia.cards 
        (org_id, system_name, classification_ai_act, level_s, xai_method, data, version)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (card.org_id, card.system_name, card.classification_ai_act,
         card.level_s, card.xai_method, Json(card.data), card.version)
    )
    return cursor.fetchone()

@router.get("/cards", response_model=list[CardResponse])
def list_cards(org_id: str = None, cursor: RealDictCursor = Depends(get_cursor)):
    """Lister les AEXIA Cards (filtrable par organisation)"""
    if org_id:
        cursor.execute("SELECT * FROM aexia.cards WHERE org_id = %s ORDER BY created_at DESC", (org_id,))
    else:
        cursor.execute("SELECT * FROM aexia.cards ORDER BY created_at DESC")
    return cursor.fetchall()

@router.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: str, cursor: RealDictCursor = Depends(get_cursor)):
    """Recuperer une Card par son ID"""
    cursor.execute("SELECT * FROM aexia.cards WHERE card_id = %s", (card_id,))
    card = cursor.fetchone()
    if not card:
        raise HTTPException(404, "Card non trouvee")
    return card