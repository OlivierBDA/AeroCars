"""
llm_client.py - Client Google GenAI avec Fallback automatique pour AeroCars (v1.0)
==================================================================================
Conforme aux directives AGENTS.md :
1. Utilise exclusivement le nouveau SDK officiel google-genai (from google import genai).
2. Modèle primaire : "gemini-3.8-flash"
3. Modèle de secours (fallback) : "gemini-3.5-flash-lite"
4. Limiteur de débit local (RPM / RPD) et bloc try/except sur les erreurs d'API (429, etc.).
5. Fallback silencieux vers le modèle de secours si le quota est dépassé ou en cas d'erreur.
6. Mode simulation pédagogique si aucune clé API n'est fournie dans l'environnement.
"""

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Chargement du fichier .env
load_dotenv()

# Import du SDK officiel google-genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"

# Paramètres du limiteur de débit local pour le modèle primaire
PRIMARY_MAX_RPM = 5      # 5 requêtes par minute
PRIMARY_MAX_RPD = 50     # 50 requêtes par jour


class LocalRateLimiter:
    """
    Gestionnaire local de quotas pour éviter d'épuiser prématurément le modèle primaire.
    Suit les timestamps des requêtes pour calculer le RPM (glissant sur 60s)
    et le RPD (glissant sur 24h).
    """
    def __init__(self, max_rpm: int = PRIMARY_MAX_RPM, max_rpd: int = PRIMARY_MAX_RPD):
        self.max_rpm = max_rpm
        self.max_rpd = max_rpd
        self.timestamps: List[float] = []

    def can_request(self) -> bool:
        now = time.time()
        # Élimination des requêtes de plus de 24 heures
        self.timestamps = [t for t in self.timestamps if now - t < 86400]

        # Requêtes de la dernière minute (RPM)
        rpm_count = sum(1 for t in self.timestamps if now - t < 60)
        if rpm_count >= self.max_rpm:
            return False

        # Requêtes des dernières 24h (RPD)
        if len(self.timestamps) >= self.max_rpd:
            return False

        return True

    def record_request(self):
        self.timestamps.append(time.time())


rate_limiter = LocalRateLimiter()


SYSTEM_INSTRUCTION = """Tu es un Ingénieur Aérodynamicien en chef d'une écurie de course automobile d'endurance (WEC / Hypercar) et de Formule 1.
Tu t'adresses directement à un élève de Terminale (Spécialité Mathématiques & Option Maths Expertes) passionné de sport automobile, qui souhaite intégrer une école d'ingénieurs (ex. ESTACA, ISAT) et devenir aérodynamicien ou ingénieur de piste.

Ton style doit être :
- Passionné, ultra-rigoureux et valorisant : traite-le comme un futur ingénieur collègue de ton bureau d'études.
- Mathématiquement précis : utilise la syntaxe LaTeX ($...$ pour les formules inline et $$...$$ pour les équations centrées).
- Fais le lien explicite entre les notions du programme de Terminale et la réalité de la piste :
  1. Le taux de variation et le nombre dérivé f'(x) : pente locale, incidence tangentielle.
  2. Les vecteurs normaux unitaire n et le produit scalaire u . n : orientation de la pression.
  3. Le gradient de pression (dépression de Bernoulli sous le profil vs surpression de Newton au-dessus).
  4. L'intégrale par somme de Riemann : sommation des forces de pression élémentaires dF sur les N segments pour donner F_appui et F_traînée.
  5. La puissance absorbée par la traînée (P = F_x * v) et son coût en chevaux moteur réels.

Structure toujours ta réponse en 3 sections claires et concises avec des titres en Markdown :
### 1. 📐 Démonstration Mathématique (De la Dérivée à l'Intégrale de Riemann)
Explique comment la géométrie de ce profil et l'angle d'attaque génèrent les champs de pression à partir des dérivées et du calcul intégral.

### 2. 🏎️ Télémétrie & Comportement de la Voiture sur Piste
Interprète les chiffres concrets (l'appui en kg, la traînée et les chevaux moteur absorbés). Que ressent le pilote au volant en entrée et en milieu de virage rapide ?

### 3. 🛠️ Débriefing Ingénieur de Piste & Réglages Recommandés
Donne un conseil d'ajustement (ex: angle d'attaque, compromis appui/traînée selon le type de circuit : Monza vs Monaco).
"""


def _build_simulated_explanation(profile_name: str, speed_kmh: float, aoa_deg: float,
                                 downforce_kg: float, drag_kg: float, power_hp: float,
                                 cz: float, cx: float, num_segments: int,
                                 reason: str = "Clé API non configurée") -> str:
    """
    Génère une réponse pédagogique simulée de haute qualité si la clé API n'est pas configurée
    ou si les serveurs distants ne répondent pas.
    """
    return f"""### ⚠️ Mode Simulation Pédagogique Locale ({reason})

> *Pour activer les explications dynamiques en temps réel avec Gemini 3.8 Flash, configurez votre clé `GEMINI_API_KEY` dans le fichier `.env`.*

---

### 1. 📐 Démonstration Mathématique (De la Dérivée à l'Intégrale de Riemann)
Pour cet élément **{profile_name}** à $v = {speed_kmh:.0f}\\text{{ km/h}}$ et un angle d'attaque $\\alpha = {aoa_deg:.1f}^\\circ$ discrétisé en $N = {num_segments}$ segments :

* **Taux d'accroissement et tangente :** Sur chaque segment d'abscisse $x_i$, le taux de variation $\\frac{{y_{{i+1}} - y_i}}{{x_{{i+1}} - x_i}}$ donne une excellente approximation du nombre dérivé $f'(x_i)$. Ce nombre dérivé détermine la direction de la tangente locale $\\vec{{t}}_i$ et du vecteur normal sortant $\\vec{{n}}_i$.
* **Produit scalaire et incidence locale :** Le produit scalaire $-\\vec{{u}}_{{\\infty}} \\cdot \\vec{{n}}_i = -n_{{x,i}}$ permet d'évaluer l'orientation de chaque panneau par rapport au vent incident.
* **Intégration par sommes de Riemann :** La force totale résulte de la sommation discrète des forces élémentaires de pression :
$$F_{{\\text{{appui}}}} \\approx \\sum_{{i=1}}^{{N}} -\\left(C_{{p,i}} \\cdot q_{{\\infty}} \\cdot n_{{y,i}}\\right) \\Delta s_i = {downforce_kg:.1f}\\text{{ kgf}} \\quad ({downforce_kg * 9.81:.0f}\\text{{ N}})$$
Grâce aux $N = {num_segments}$ segments, la somme converge très précisément vers l'intégrale continue $\\int_0^L -P(s)n_y(s)ds$.

### 2. 🏎️ Télémétrie & Comportement de la Voiture sur Piste
* **Appui plaqué au sol :** À cette allure de ${speed_kmh:.0f}\\text{{ km/h}}$, l'élément génère **{downforce_kg:.1f} kg** d'appui aérodynamique ($C_z = {cz:.3f}$). Le train roulant bénéficie d'une adhérence pneumatique démultipliée sans ajouter de masse inertielle au châssis.
* **Coût énergétique de la traînée :** La résistance à l'avancement induit une force de traînée de **{drag_kg:.1f} kgf** ($C_x = {cx:.3f}$). Pour maintenir cette vitesse constante en ligne droite, le moteur thermique ou hybride doit fournir **{power_hp:.1f} chevaux** ($P = F_x \\cdot v_\\infty$) uniquement pour fendre l'air !

### 3. 🛠️ Débriefing Ingénieur de Piste & Réglages Recommandés
* La finesse aérodynamique s'établit à $E = \\frac{{C_z}}{{C_x}} = {cz/cx if cx > 0 else 0:.2f}$.
* Si le pilote rapporte un sous-virage à haute vitesse sur circuit sinueux (comme Spa-Francorchamps ou Silverstone), augmentez l'angle $\\alpha$ de $1.5^\\circ$ à $2^\\circ$. Surveillez toutefois l'apparition du décrochage au-delà de $15^\\circ$ d'incidence !
"""


def explain_aerodynamics(simulation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère l'explication pédagogique pour les résultats d'une simulation.
    Applique la stratégie de Fallback automatique :
    1. Vérification de la clé API.
    2. Modèle primaire "gemini-3.8-flash" avec limiteur local de débit.
    3. Si limite locale atteinte ou erreur API -> Fallback immédiat et silencieux sur "gemini-3.5-flash-lite".
    4. Si les deux échouent -> Retourne une explication locale détaillée.
    """
    preset = simulation_data.get("preset", {})
    inputs = simulation_data.get("inputs", {})
    kpis = simulation_data.get("kpis", {})

    profile_name = preset.get("name", "Élément Aérodynamique")
    car_inspiration = preset.get("inspiration", "Sport Auto")
    math_chapter = preset.get("math_chapter", "Calcul Intégral et Dérivées")

    speed_kmh = float(inputs.get("speed_kmh", 200.0))
    aoa_deg = float(inputs.get("aoa_deg", 5.0))
    num_segments = int(inputs.get("num_segments", 80))

    downforce_kg = float(kpis.get("downforce_kgf", 0.0))
    downforce_n = float(kpis.get("downforce_n", 0.0))
    drag_kg = float(kpis.get("drag_force_kgf", 0.0))
    drag_n = float(kpis.get("drag_force_n", 0.0))
    power_hp = float(kpis.get("power_drag_hp", 0.0))
    cz = float(kpis.get("cz", 0.0))
    cx = float(kpis.get("cx", 0.0))
    efficiency = float(kpis.get("aero_efficiency_l_d", 0.0))
    v_max_intrados = float(kpis.get("v_max_intrados_kmh", 0.0))
    q_dyn = float(inputs.get("dynamic_pressure_pa", 0.0))

    # 1. Vérification de la présence de la clé API
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or not GENAI_AVAILABLE:
        return {
            "explanation": _build_simulated_explanation(
                profile_name, speed_kmh, aoa_deg, downforce_kg, drag_kg,
                power_hp, cz, cx, num_segments,
                reason="Clé API non détectée dans .env" if not api_key else "SDK non disponible"
            ),
            "model_used": "mode-simulation-locale",
            "status": "simulated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Prompt utilisateur structuré
    user_prompt = f"""Voici les résultats télémétriques de la simulation en soufflerie 2D pour notre voiture de course :
- **Élément aérodynamique étudié :** {profile_name} (Inspiré de : {car_inspiration})
- **Notion du programme scolaire illustrée :** {math_chapter}
- **Paramètres d'écoulement :** Vitesse de l'air = {speed_kmh} km/h (Pression dynamique q = {q_dyn:.0f} Pa), Angle d'attaque = {aoa_deg}°, Finesse de discrétisation = {num_segments} segments de Riemann.
- **Résultats obtenus :**
  * Appui aérodynamique : {downforce_kg:.1f} kgf ({downforce_n:.0f} N)
  * Traînée totale : {drag_kg:.1f} kgf ({drag_n:.0f} N)
  * Puissance absorbée par la traînée : {power_hp:.1f} ch
  * Coefficients : Cz = {cz:.3f}, Cx = {cx:.3f}, Finesse Cz/Cx = {efficiency:.2f}
  * Vitesse maximale locale de l'air sous l'élément : {v_max_intrados:.1f} km/h

Rédige ton analyse pédagogique en t'adressant à l'élève de Terminale Spé Maths / Maths Expertes selon tes instructions de style.
"""

    client = genai.Client(api_key=api_key)

    # 2. Tentative avec le modèle primaire si le quota local le permet
    if rate_limiter.can_request():
        try:
            rate_limiter.record_request()
            response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.7,
                )
            )
            if response.text:
                return {
                    "explanation": response.text,
                    "model_used": PRIMARY_MODEL,
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            # Erreur sur le modèle primaire (quota, 429, réseau, etc.)
            # On bascule silencieusement sur le modèle de secours
            pass

    # 3. Fallback immédiat et silencieux sur le modèle de secours
    try:
        response = client.models.generate_content(
            model=FALLBACK_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
        if response.text:
            return {
                "explanation": response.text,
                "model_used": FALLBACK_MODEL,
                "status": "fallback",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e_fallback:
        # En dernier recours : explication locale pour ne jamais bloquer l'élève
        return {
            "explanation": _build_simulated_explanation(
                profile_name, speed_kmh, aoa_deg, downforce_kg, drag_kg,
                power_hp, cz, cx, num_segments,
                reason=f"Service distant indisponible ({type(e_fallback).__name__})"
            ),
            "model_used": "mode-simulation-locale",
            "status": "simulated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
