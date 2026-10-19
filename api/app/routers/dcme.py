from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.dcme import generate_synthetic_data, build_causal_graph, DCMEngine

router = APIRouter()

# Initialisation unique du moteur DCME au démarrage du serveur
print("Initialisation du moteur DCME (Génération des données et entraînement)...")
try:
    df = generate_synthetic_data(1000)
    graph = build_causal_graph()
    dcme_engine = DCMEngine(df, graph)
    print("Moteur DCME prêt !")
except Exception as e:
    print(f"Erreur d'initialisation du DCME : {e}")
    dcme_engine = None

# Schéma d'entrée
class DCMEInput(BaseModel):
    Age: int = Field(..., ge=18, le=100, description="Âge de la personne")
    Gender: int = Field(..., ge=0, le=1, description="0 pour Femme, 1 pour Homme")
    Salary: float = Field(..., ge=0, description="Salaire annuel")

@router.post("/scoring/dcme")
def compute_dcme(instance: DCMEInput):
    """
    Calcule la décomposition DCME pour une prédiction de prêt.
    """
    if not dcme_engine:
        raise HTTPException(status_code=500, detail="Moteur DCME non initialisé.")
    
    try:
        # Conversion du modèle Pydantic en dictionnaire
        inst_dict = instance.model_dump()
        
        # Appel du moteur
        result = dcme_engine.calculate_dcme(inst_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))