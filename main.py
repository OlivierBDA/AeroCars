"""
main.py - Serveur FastAPI pour l'application AeroCars (v1.0)
============================================================
Expose l'API REST pour la simulation aérodynamique 2D (Palier 1),
l'explication par le modèle LLM Gemini, et sert l'interface web statique.
"""

import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from aero_profiles import get_presets, list_presets_metadata
from aero_math import run_wind_tunnel_simulation
from llm_client import explain_aerodynamics

app = FastAPI(
    title="AeroCars — Soufflerie Aérodynamique 2D",
    description="Application éducative de soufflerie 2D pour lycéens de Terminale (Spé Maths & Maths Expertes)",
    version="1.0.0",
)

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modèles Pydantic pour la validation des requêtes
class SimulationRequest(BaseModel):
    preset_id: Optional[str] = Field(None, description="Identifiant de l'élément aérodynamique")
    profile_id: Optional[str] = Field(None, description="Alias pour preset_id")
    speed_kmh: float = Field(200.0, ge=30.0, le=450.0, description="Vitesse du vent en km/h")
    aoa_deg: float = Field(8.0, ge=-15.0, le=35.0, description="Angle d'attaque en degrés")
    chord_m: Optional[float] = Field(None, gt=0.0, le=5.0, description="Longueur de corde en mètres")
    span_m: Optional[float] = Field(None, gt=0.0, le=5.0, description="Envergure en mètres")
    num_segments: int = Field(60, ge=10, le=200, description="Finesse de discrétisation N")
    temp_celsius: float = Field(20.0, ge=-20.0, le=50.0, description="Température de l'air en °C")


class ExplainRequest(BaseModel):
    simulation_data: Optional[Dict[str, Any]] = None
    # Si les paramètres bruts sont fournis plutôt que l'objet complet
    preset_id: Optional[str] = "gt3_wing"
    speed_kmh: Optional[float] = 200.0
    aoa_deg: Optional[float] = 8.0
    num_segments: Optional[int] = 60


@app.get("/api/presets")
@app.get("/api/profiles")
def get_profiles() -> List[Dict[str, Any]]:
    """
    Retourne la liste des 5 éléments aérodynamiques prédéfinis et leurs métadonnées.
    """
    return list_presets_metadata()


@app.post("/api/simulate")
def simulate(req: SimulationRequest) -> Dict[str, Any]:
    """
    Exécute la simulation numérique du Palier 1 (Sommes de Riemann, dérivées, pressions).
    Retourne les KPIs de télémétrie, les points de discrétisation, les vecteurs et les streamlines.
    """
    selected_id = req.preset_id or req.profile_id or "gt3_wing"
    presets = get_presets()
    if selected_id not in presets:
        raise HTTPException(status_code=404, detail=f"Profil inconnu: '{selected_id}'")

    preset = presets[selected_id]
    chord = req.chord_m if req.chord_m is not None else preset["default_chord_m"]
    span = req.span_m if req.span_m is not None else preset["default_span_m"]

    try:
        results = run_wind_tunnel_simulation(
            preset_id=selected_id,
            speed_kmh=req.speed_kmh,
            aoa_deg=req.aoa_deg,
            chord_m=chord,
            span_m=span,
            temp_celsius=req.temp_celsius,
            num_segments=req.num_segments,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de calcul aérodynamique: {str(e)}")


@app.post("/api/explain")
def explain(req: ExplainRequest) -> Dict[str, Any]:
    """
    Génère l'explication pédagogique pour un lycéen via l'API Google Gemini
    (avec fallback automatique gemini-3.8-flash -> gemini-3.5-flash-lite).
    """
    if req.simulation_data:
        sim_data = req.simulation_data
    else:
        # Exécute la simulation avec les paramètres fournis
        pid = req.preset_id or "gt3_wing"
        presets = get_presets()
        preset = presets.get(pid, presets["gt3_wing"])
        sim_data = run_wind_tunnel_simulation(
            preset_id=pid,
            speed_kmh=req.speed_kmh or 200.0,
            aoa_deg=req.aoa_deg or preset["default_aoa_deg"],
            chord_m=preset["default_chord_m"],
            span_m=preset["default_span_m"],
            num_segments=req.num_segments or 60,
        )

    try:
        explanation = explain_aerodynamics(sim_data)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse IA: {str(e)}")


# Montage des fichiers statiques (Frontend Vanilla JS sans Node.js)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    """Sert la page d'accueil de l'application."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AeroCars API opérationnelle. Interface web en cours de chargement..."}
