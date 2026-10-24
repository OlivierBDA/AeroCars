"""
aero_profiles.py - Définition mathématique des 5 profils aérodynamiques prédéfinis (AeroCars v1.0)
==================================================================================================
Niveau : Terminale Spécialité Mathématiques (Fonctions usuelles : polynômes, racine carrée, exponentielle, trigonométrie).

Chaque profil est défini sur l'intervalle normalisé x in [0, 1] (qui sera ensuite mis à l'échelle
selon la longueur réelle de corde L en mètres).
Pour chaque profil, on définit :
- y_up(x)   : l'extrados (surface supérieure, en mètres par mètre de corde)
- y_low(x)  : l'intrados (surface inférieure, en mètres par mètre de corde)
- latex_up  : l'expression LaTeX exacte affichée dans l'interface pour le lycéen
- latex_low : l'expression LaTeX de l'intrados
"""

import math
from typing import Dict, Any, List


def get_presets() -> Dict[str, Dict[str, Any]]:
    """
    Retourne le dictionnaire des 5 éléments aérodynamiques emblématiques.
    Les fonctions y_up(x) et y_low(x) prennent x dans [0.0, 1.0] et retournent y normalisé.
    """
    return {
        "gt3_wing": {
            "id": "gt3_wing",
            "name": "Aileron Arrière GT3 (Col de cygne)",
            "inspiration": "Porsche 911 GT3 RS (992)",
            "category": "Aileron inversé (Génération d'appui pur)",
            "description": (
                "Profil d'aile inversée asymétrique. L'extrados (dessus) est quasi-plat tandis que "
                "l'intrados (dessous) est fortement bombé pour accélérer l'air sous l'aileron "
                "(effet Venturi / Bernoulli) et aspirer l'arrière de la voiture vers le sol."
            ),
            "default_chord_m": 0.35,       # 35 cm de profondeur d'aileron
            "default_span_m": 1.80,        # 1m80 d'envergure
            "default_aoa_deg": 8.0,        # Angle d'attaque par défaut (degrés)
            "recommended_aoa_range": [-2.0, 18.0],
            "math_chapter": "Polynômes du 3e degré & Fonction racine carrée (Profil NACA inversé)",
            "latex_up": r"f_{\text{sup}}(x) = 0.04 \cdot x(1 - x)",
            "latex_low": r"f_{\text{inf}}(x) = -0.18\sqrt{x}(1 - x) - 0.05x(1 - x)^2",
            "y_up": lambda x: 0.04 * x * (1.0 - x),
            "y_low": lambda x: -0.18 * math.sqrt(max(0.0, x)) * (1.0 - x) - 0.05 * x * ((1.0 - x) ** 2),
        },
        "le_mans_teardrop": {
            "id": "le_mans_teardrop",
            "name": "Goutte d'eau Longtail (Finesse pure)",
            "inspiration": "McLaren Speedtail / Porsche 917 LH (Le Mans)",
            "category": "Carrosserie à très faible traînée (Low Drag)",
            "description": (
                "Profil symétrique en goutte d'eau allongée ('Longtail'). L'avant arrondi (racine carrée) "
                "sépare l'air en douceur et la longue queue effilée (exponentielle décroissante) "
                "évite le décollement des filets d'air et minimise le sillage turbulent."
            ),
            "default_chord_m": 1.20,
            "default_span_m": 1.90,
            "default_aoa_deg": 2.0,
            "recommended_aoa_range": [-5.0, 10.0],
            "math_chapter": "Fonction Exponentielle & Racine carrée : produit u(x)v(x)",
            "latex_up": r"f_{\text{sup}}(x) = 0.22\sqrt{x}(1 - x)e^{-1.2x}",
            "latex_low": r"f_{\text{inf}}(x) = -0.22\sqrt{x}(1 - x)e^{-1.2x}",
            "y_up": lambda x: 0.22 * math.sqrt(max(0.0, x)) * (1.0 - x) * math.exp(-1.2 * x),
            "y_low": lambda x: -0.22 * math.sqrt(max(0.0, x)) * (1.0 - x) * math.exp(-1.2 * x),
        },
        "hypercar_wedge": {
            "id": "hypercar_wedge",
            "name": "Museau & Lame Avant (Splitter)",
            "inspiration": "Ferrari F40 / Lamborghini Countach (Wedge Design)",
            "category": "Face avant & Lame de répartition (Front Splitter)",
            "description": (
                "Profil en coin ('Wedge') caractéristique des supercars. Le fond plat inférieur "
                "bloque le flux sous le pare-chocs tandis que le capot plongeant à courbure "
                "trigonométrique utilise la pression dynamique de l'air pour plaquer le train avant."
            ),
            "default_chord_m": 0.90,
            "default_span_m": 1.95,
            "default_aoa_deg": 4.0,
            "recommended_aoa_range": [-3.0, 12.0],
            "math_chapter": "Fonctions Trigonométriques (Sinus) & Polynômes du second degré",
            "latex_up": r"f_{\text{sup}}(x) = 0.16\sin\left(\frac{\pi}{2}x\right) + 0.05x(1 - x)",
            "latex_low": r"f_{\text{inf}}(x) = -0.015\sin(\pi x)",
            "y_up": lambda x: 0.16 * math.sin((math.pi / 2.0) * x) + 0.05 * x * (1.0 - x),
            "y_low": lambda x: -0.015 * math.sin(math.pi * x),
        },
        "venturi_diffuser": {
            "id": "venturi_diffuser",
            "name": "Diffuseur Arrière à Effet de Sol (Tunnel Venturi)",
            "inspiration": "Aston Martin Valkyrie / Porsche 963 LMDh",
            "category": "Extracteur de fond plat (Effet Venturi)",
            "description": (
                "Section arrière d'un fond plat d'hypercar. Le col resserré à l'entrée accélère "
                "fortement l'air sous la voiture (dépression de Bernoulli), puis la rampe "
                "polynomiale divergente ralentit le flux progressivement vers l'arrière."
            ),
            "default_chord_m": 1.10,
            "default_span_m": 1.70,
            "default_aoa_deg": 6.0,
            "recommended_aoa_range": [0.0, 14.0],
            "math_chapter": "Polynômes du 3e degré (Point d'inflexion) & Dérivée seconde",
            "latex_up": r"f_{\text{sup}}(x) = 0.08 + 0.14x^2(3 - 2x)",
            "latex_low": r"f_{\text{inf}}(x) = -0.06x(1 - x) - 0.12\sqrt{x}(1 - x)^2",
            "y_up": lambda x: 0.08 + 0.14 * (x ** 2) * (3.0 - 2.0 * x),
            "y_low": lambda x: -0.06 * x * (1.0 - x) - 0.12 * math.sqrt(max(0.0, x)) * ((1.0 - x) ** 2),
        },
        "gurney_flap_wing": {
            "id": "gurney_flap_wing",
            "name": "Aileron Bi-plan avec Gurney Flap",
            "inspiration": "Ferrari 296 GT3 / Ford GT Le Mans",
            "category": "Aileron fort appui avec braquet de bord de fuite",
            "description": (
                "Aileron de course doté d'une cambrure prononcée et d'une courbure accentuée "
                "au bord de fuite (effet Gurney Flap par terme exponentiel localisé). Génère "
                "un appui maximal pour les circuits sinueux, au prix d'une traînée plus élevée."
            ),
            "default_chord_m": 0.40,
            "default_span_m": 1.85,
            "default_aoa_deg": 10.0,
            "recommended_aoa_range": [0.0, 20.0],
            "math_chapter": "Combinaison Polynôme + Exponentielle (Croissance comparée)",
            "latex_up": r"f_{\text{sup}}(x) = 0.03\sin(\pi x) + 0.025e^{-25(x - 0.95)^2}",
            "latex_low": r"f_{\text{inf}}(x) = -0.22\sqrt{x}(1 - x)",
            "y_up": lambda x: 0.03 * math.sin(math.pi * x) + 0.025 * math.exp(-25.0 * ((x - 0.95) ** 2)),
            "y_low": lambda x: -0.22 * math.sqrt(max(0.0, x)) * (1.0 - x),
        },
    }


def list_presets_metadata() -> List[Dict[str, Any]]:
    """
    Retourne la liste des métadonnées des profils (sans les fonctions lambda)
    pour l'API JSON (/api/presets).
    """
    presets = get_presets()
    metadata_list = []
    for key, val in presets.items():
        meta = {k: v for k, v in val.items() if not callable(v)}
        metadata_list.append(meta)
    return metadata_list
