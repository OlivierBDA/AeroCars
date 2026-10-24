"""
aero_math.py - Moteur Mathématique et Aérodynamique 2D (AeroCars v1.0)
======================================================================
Objectif pédagogique :
Ce module traduit les concepts du programme de Terminale (Spécialité Mathématiques
et Option Maths Expertes) en un moteur de simulation de soufflerie 2D lisible,
explicite et sans "boîte noire".

Chapitres de Terminale mobilisés dans ce code (Palier 1) :
1. Dérivation & Approximation affine : Taux d'accroissement f'(x) = (f(x+dx) - f(x))/dx
2. Géométrie vectorielle & Trigonométrie : Rotation plane d'angle alpha, vecteurs tangents
   et normaux unitaires, produit scalaire (u . v = u_x*v_x + u_y*v_y).
3. Physique-Mathématiques : Pression dynamique (q = 1/2 * rho * v^2), théorème de Bernoulli,
   modèle des panneaux d'impact + succion de courbure.
4. Calcul Intégral : Sommes de Riemann / Méthode des trapèzes sur N segments discrets
   pour calculer la Traînée (Fx) et l'Appui / Déportance (Fz).
"""

import math
from typing import Dict, Any, List, Tuple
from aero_profiles import get_presets


# ==============================================================================
# 1. CONSTANTES PHYSIQUES & ATMOSPHÉRIQUES (Modèle ISA)
# ==============================================================================

R_SPECIFIC_DRY_AIR = 287.058  # Constante spécifique de l'air sec en J/(kg.K)
STD_PRESSURE_PA = 101325.0    # Pression atmosphérique standard au niveau de la mer (Pa)


def compute_air_density(temp_celsius: float = 20.0, pressure_pa: float = STD_PRESSURE_PA) -> float:
    """
    Calcule la masse volumique de l'air rho (en kg/m^3) selon la loi des gaz parfaits.
    Formule : rho = P / (R_specifique * T_kelvin)
    À 20°C (293.15 K) et 101325 Pa, rho ≈ 1.204 kg/m^3.
    À 15°C (288.15 K), rho ≈ 1.225 kg/m^3.
    """
    temp_kelvin = temp_celsius + 273.15
    return pressure_pa / (R_SPECIFIC_DRY_AIR * temp_kelvin)


def kmh_to_ms(speed_kmh: float) -> float:
    """
    Convertit la vitesse du flux d'air de km/h en m/s.
    Formule : v (m/s) = V (km/h) / 3.6
    """
    return speed_kmh / 3.6


def compute_dynamic_pressure(rho: float, v_ms: float) -> float:
    """
    Calcule la pression dynamique q (en Pascals, Pa ou N/m^2).
    Formule : q = 1/2 * rho * v^2
    C'est l'énergie cinétique volumique du fluide en mouvement.
    """
    return 0.5 * rho * (v_ms ** 2)


# ==============================================================================
# 2. GÉOMÉTRIE VECTORIELLE : ÉCHANTILLONNAGE & ROTATION D'ANGLE D'ATTAQUE
# ==============================================================================

def rotate_point_2d(
    x: float, y: float, angle_deg: float, pivot_x: float = 0.25, pivot_y: float = 0.0
) -> Tuple[float, float]:
    """
    Applique une rotation géométrique plane d'angle d'attaque alpha (AoA) autour du
    foyer aérodynamique (situé à 25% de la corde : pivot_x = 0.25 * L).

    Lien Terminale (Trigonométrie & Maths Expertes - Nombres complexes / Matrices) :
    Un angle d'attaque positif en sport automobile incline le bord d'attaque (avant)
    vers le BAS (piqué) et relève le bord de fuite (arrière) vers le HAUT pour créer de l'appui.
    Soit theta = +alpha (en radians) :
      Pour x < pivot_x (bord d'attaque), dx < 0 => y' descend (piqué vers le sol).
      Pour x > pivot_x (bord de fuite), dx > 0 => y' monte (relevé vers le haut).
        x' = x_0 + (x - x_0)*cos(theta) - (y - y_0)*sin(theta)
        y' = y_0 + (x - x_0)*sin(theta) + (y - y_0)*cos(theta)
    """
    theta_rad = math.radians(angle_deg)
    cos_t = math.cos(theta_rad)
    sin_t = math.sin(theta_rad)

    dx = x - pivot_x
    dy = y - pivot_y

    x_rot = pivot_x + dx * cos_t - dy * sin_t
    y_rot = pivot_y + dx * sin_t + dy * cos_t
    return x_rot, y_rot


def discretize_profile(
    preset_id: str,
    chord_m: float = 1.0,
    aoa_deg: float = 5.0,
    num_segments: int = 80
) -> Dict[str, List[Tuple[float, float]]]:
    """
    Subdivise l'intervalle [0, chord_m] en N segments (N+1 points) pour l'extrados
    et l'intrados, puis applique la rotation correspondant à l'angle d'attaque.
    """
    presets = get_presets()
    if preset_id not in presets:
        raise ValueError(f"Profil inconnu : {preset_id}. Choix possibles : {list(presets.keys())}")

    preset = presets[preset_id]
    f_up = preset["y_up"]
    f_low = preset["y_low"]

    pivot_x = 0.25 * chord_m
    pivot_y = 0.0

    upper_points: List[Tuple[float, float]] = []
    lower_points: List[Tuple[float, float]] = []

    for i in range(num_segments + 1):
        # Coordonnée normalisée t dans [0, 1]
        t = i / num_segments
        # Mise à l'échelle selon la longueur réelle de corde L (chord_m)
        x_phys = t * chord_m
        y_up_phys = f_up(t) * chord_m
        y_low_phys = f_low(t) * chord_m

        # Rotation de l'angle d'attaque alpha
        x_u, y_u = rotate_point_2d(x_phys, y_up_phys, aoa_deg, pivot_x, pivot_y)
        x_l, y_l = rotate_point_2d(x_phys, y_low_phys, aoa_deg, pivot_x, pivot_y)

        upper_points.append((x_u, y_u))
        lower_points.append((x_l, y_l))

    return {
        "upper_points": upper_points,
        "lower_points": lower_points,
    }


# ==============================================================================
# 3. DÉRIVATION NUMÉRIQUE, VECTEURS NORMAUX ET PRODUIT SCALAIRE (Spé Maths)
# ==============================================================================

def analyze_surface_panels(
    points: List[Tuple[float, float]],
    surface_type: str,
    aoa_deg: float,
    v_inf_ms: float,
    q_dyn_pa: float
) -> List[Dict[str, float]]:
    """
    Analyse chaque segment [M_i, M_{i+1}] d'une surface (extrados ou intrados).

    Étapes mathématiques explicites (Programme de Terminale Spécialité) :
    -------------------------------------------------------------------
    1. Vecteur directeur du segment (Approximation affine) :
       dx = x_{i+1} - x_i
       dy = y_{i+1} - y_i
       Longueur élémentaire : ds = sqrt(dx^2 + dy^2)

    2. Taux d'accroissement (Nombre dérivé local f'(x_i)) :
       f'(x_i) ≈ dy / dx

    3. Vecteur unitaire tangent T et vecteur unitaire normal extérieur n :
       T = (dx / ds, dy / ds)
       - Pour l'extrados (surface supérieure, normale pointant vers le HAUT +y) :
         n_ext = (-dy / ds, dx / ds)
       - Pour l'intrados (surface inférieure, normale pointant vers le BAS -y) :
         n_ext = (dy / ds, -dx / ds)

    4. Produit scalaire avec la direction du vent incident u_vent = (1, 0) :
       cos(phi_i) = u_vent . (-n_ext) = -n_x
       (mesure l'angle d'incidence local entre le filet d'air et la paroi).

    5. Calcul du Coefficient de Pression local Cp_i :
       Combine l'impact newtonien (2 * sin^2(theta_local)) sur les faces exposées au flux
       et l'effet Venturi/Bernoulli lié à la pente et à la cambrure (circulation).
    """
    panels: List[Dict[str, float]] = []
    aoa_rad = math.radians(aoa_deg)

    # Facteur de décrochage aérodynamique (Stall) au-delà de 15° d'angle d'attaque :
    # En physique réelle, si l'angle est trop fort, les filets d'air se décollent !
    # On le modélise par une fonction exponentielle de perte de succion.
    stall_angle_deg = 15.0
    if abs(aoa_deg) > stall_angle_deg:
        stall_efficiency = math.exp(-0.08 * ((abs(aoa_deg) - stall_angle_deg) ** 2))
    else:
        stall_efficiency = 1.0

    num_panels = len(points) - 1
    for i in range(num_panels):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        # Milieu du segment (point d'application de la force élémentaire)
        x_mid = 0.5 * (x1 + x2)
        y_mid = 0.5 * (y1 + y2)

        # Accroissements différentiels dx et dy
        dx = x2 - x1
        dy = y2 - y1

        # Longueur d'arc élémentaire ds = sqrt(dx^2 + dy^2)
        ds = math.hypot(dx, dy)
        if ds < 1e-9:
            continue

        # Nombre dérivé f'(x) = dy / dx (pente de la tangente locale)
        derivative = dy / dx if abs(dx) > 1e-7 else math.copysign(999.0, dy)
        slope_angle_rad = math.atan2(dy, dx)

        # Vecteur normal unitaire extérieur n = (nx, ny)
        if surface_type == "upper":
            # Normale extérieure vers le haut (+y)
            nx = -dy / ds
            ny = dx / ds
        else:
            # Normale extérieure vers le bas (-y)
            nx = dy / ds
            ny = -dx / ds

        # Produit scalaire entre le vecteur vitesse unitaire u_inf = (1, 0)
        # et la normale rentrante (-nx, -ny) :
        # dot_product = 1 * (-nx) + 0 * (-ny) = -nx
        dot_impact = -nx

        # Calcul du Coefficient de Pression Cp = (P - P_inf) / q_inf
        if surface_type == "upper":
            # Extrados : lorsque la surface monte face au vent (dot_impact > 0),
            # l'air est comprimé (Cp > 0 -> surpression sur le dessus qui plaque vers le sol).
            cp_impact = 1.8 * (dot_impact ** 2) if dot_impact > 0 else -0.35 * (dot_impact ** 2)
            cp_circulation = 0.55 * math.sin(aoa_rad) * stall_efficiency * math.sqrt(max(0.05, 1.0 - (i / num_panels)))
            cp = cp_impact + cp_circulation
        else:
            # Intrados : l'air accélère sous le profil bombé (Effet Venturi / Bernoulli)
            # La vitesse locale v_local est supérieure à v_inf, donc Cp < 0 (Dépression / Succion vers le sol !)
            venturi_suction = -1.25 * math.sin(math.pi * (i / num_panels)) * (0.35 + 0.85 * math.sin(aoa_rad + 0.12))
            cp_impact = 1.5 * (dot_impact ** 2) if dot_impact > 0 else -0.45 * (dot_impact ** 2)
            cp = (venturi_suction * stall_efficiency) + cp_impact

        # Bornage physique réaliste du Cp en écoulement subsonique [-2.5, +1.0]
        cp = max(-2.5, min(1.0, cp))

        # Théorème de Bernoulli : Cp = 1 - (v_local / v_inf)^2
        # D'où : v_local = v_inf * sqrt(max(0.05, 1 - Cp))
        local_speed_ms = v_inf_ms * math.sqrt(max(0.05, 1.0 - cp))

        # Surpression ou dépression relative delta_P (en Pascals) : delta_P = Cp * q_dyn
        delta_p_pa = cp * q_dyn_pa

        # Force aérodynamique élémentaire exercée par la pression sur le segment (par mètre d'envergure) :
        # La pression pousse vers l'intérieur de la paroi, soit selon (-nx, -ny) :
        # dF_pression = delta_P * ds * (-n_ext)
        # De plus, la viscosité de l'air crée un frottement tangentiel (Cf) le long de T = (dx/ds, dy/ds).
        cf_skin = 0.009 + (0.045 * (1.0 - stall_efficiency))
        df_x_per_m = (abs(delta_p_pa * nx) * 0.35 + q_dyn_pa * cf_skin * (dx / ds)) * ds
        df_z_per_m = (delta_p_pa * (-ny) + q_dyn_pa * cf_skin * (dy / ds)) * ds

        panels.append({
            "index": i,
            "x_mid": round(x_mid, 5),
            "y_mid": round(y_mid, 5),
            "dx": round(dx, 5),
            "dy": round(dy, 5),
            "ds": round(ds, 5),
            "derivative_f_prime": round(derivative, 4),
            "slope_angle_deg": round(math.degrees(slope_angle_rad), 2),
            "nx": round(nx, 4),
            "ny": round(ny, 4),
            "cp": round(cp, 4),
            "delta_p_pa": round(delta_p_pa, 2),
            "local_speed_ms": round(local_speed_ms, 2),
            "local_speed_kmh": round(local_speed_ms * 3.6, 1),
            "df_x_per_m": df_x_per_m,
            "df_z_per_m": df_z_per_m,
        })

    return panels


# ==============================================================================
# 4. INTÉGRATION NUMÉRIQUE (Sommes de Riemann) & BILAN DES FORCES
# ==============================================================================

def integrate_aerodynamic_forces(
    upper_panels: List[Dict[str, float]],
    lower_panels: List[Dict[str, float]],
    chord_m: float,
    span_m: float,
    aoa_deg: float,
    q_dyn_pa: float
) -> Dict[str, float]:
    """
    Intègre les forces élémentaires sur l'ensemble du contour (Extrados + Intrados)
    par sommation discrète (Somme de Riemann : Integrale(dF) ≈ Somme(dF_i)).

    Conventions d'ingénierie de course automobile :
    - F_drag (Traînée, N) : Force horizontale s'opposant à l'avancement (+x vers l'arrière).
    - F_downforce (Appui, N) : Force verticale plaquant la voiture VERS LE SOL (-y).
      Un F_downforce POSITIF signifie que la voiture est aspirée/plaquée au bitume.
    """
    # Somme de Riemann sur l'extrados et l'intrados (par mètre d'envergure)
    fx_per_m = sum(p["df_x_per_m"] for p in upper_panels) + sum(p["df_x_per_m"] for p in lower_panels)
    fy_per_m = sum(p["df_z_per_m"] for p in upper_panels) + sum(p["df_z_per_m"] for p in lower_panels)

    # Surface de référence aérodynamique S_ref = chord_m * span_m
    s_ref_m2 = max(0.01, chord_m * span_m)

    # L'appui (Downforce) est l'opposé de la résultante verticale ascendante Fy :
    downforce_profile_n = -fy_per_m * span_m

    # Coefficients adimensionnels :
    # Cz (Coefficient d'appui) = F_downforce / (q_dyn * S_ref)
    cz = downforce_profile_n / (q_dyn_pa * s_ref_m2) if q_dyn_pa > 0 else 0.0

    # Traînée totale = Traînée de forme/frottement 2D + Traînée induite par les tourbillons
    # de bout d'aileron (Vortex induits : Cd_induced = Cz^2 / (pi * Aspect_Ratio * e))
    aspect_ratio = span_m / chord_m if chord_m > 0 else 4.0
    cd_induced = (cz ** 2) / (math.pi * max(1.5, aspect_ratio) * 0.80)

    drag_profile_n = abs(fx_per_m * span_m)
    drag_induced_n = cd_induced * q_dyn_pa * s_ref_m2
    total_drag_n = drag_profile_n + drag_induced_n

    cx = total_drag_n / (q_dyn_pa * s_ref_m2) if q_dyn_pa > 0 else 0.0

    # Finesse aérodynamique (Efficacité L/D = Appui / Traînée = Cz / Cx)
    aero_efficiency = cz / cx if cx > 1e-5 else 0.0

    return {
        "s_ref_m2": round(s_ref_m2, 3),
        "cx": round(cx, 4),
        "cz": round(cz, 4),
        "aero_efficiency_l_d": round(aero_efficiency, 2),
        "drag_force_n": round(total_drag_n, 1),
        "drag_force_kgf": round(total_drag_n / 9.81, 1),
        "downforce_n": round(downforce_profile_n, 1),
        "downforce_kgf": round(downforce_profile_n / 9.81, 1),
    }


# ==============================================================================
# 5. GÉNÉRATION DES LIGNES DE COURANT (STREAMLINES) POUR LE CANVAS HTML5
# ==============================================================================

def generate_streamlines(
    upper_points: List[Tuple[float, float]],
    lower_points: List[Tuple[float, float]],
    chord_m: float,
    aoa_deg: float,
    v_inf_ms: float,
    cz: float,
    num_lines: int = 18,
    num_steps: int = 60
) -> List[Dict[str, Any]]:
    """
    Génère les trajectoires (x, y) et vitesses locales des filets d'air (streamlines)
    autour du profil pour l'animation de fumée dans la soufflerie Canvas 2D.
    """
    x_min = -0.35 * chord_m
    x_max = 1.45 * chord_m
    y_span = 0.55 * chord_m

    streamlines = []
    for line_idx in range(num_lines):
        frac = (line_idx / (num_lines - 1)) * 2.0 - 1.0
        if abs(frac) < 0.04:
            frac = 0.04 if frac >= 0 else -0.04
        y0 = frac * y_span

        points_line = []
        for s in range(num_steps + 1):
            x = x_min + (x_max - x_min) * (s / num_steps)

            if 0.0 <= x <= chord_m:
                idx = min(len(upper_points) - 1, max(0, int((x / chord_m) * (len(upper_points) - 1))))
                _, y_surf_up = upper_points[idx]
                _, y_surf_low = lower_points[idx]

                decay = math.exp(-3.2 * abs(y0) / chord_m)
                if y0 >= 0:
                    y = y0 + (y_surf_up + 0.02 * chord_m) * decay
                    v_ratio = max(0.5, 1.0 - 0.25 * cz * decay)
                else:
                    y = y0 + (y_surf_low - 0.02 * chord_m) * decay
                    v_ratio = min(1.85, 1.0 + 0.45 * cz * decay)
            elif x > chord_m:
                wake_dist = (x - chord_m) / chord_m
                decay = math.exp(-2.5 * abs(y0) / chord_m) * math.exp(-1.2 * wake_dist)
                upwash = 0.08 * cz * math.sin(4.0 * wake_dist) * decay
                y = y0 + upwash * chord_m
                v_ratio = 1.0 - 0.15 * decay
            else:
                lead_dist = abs(x) / chord_m
                decay = math.exp(-4.0 * lead_dist) * math.exp(-3.0 * abs(y0) / chord_m)
                y = y0 - (0.04 * cz * chord_m * decay)
                v_ratio = 1.0 - 0.10 * decay

            points_line.append({
                "x": round(x, 4),
                "y": round(y, 4),
                "v_ms": round(v_inf_ms * v_ratio, 2),
                "v_ratio": round(v_ratio, 3),
            })

        streamlines.append({
            "line_index": line_idx,
            "region": "extrados" if y0 >= 0 else "intrados",
            "points": points_line,
        })

    return streamlines


# ==============================================================================
# 6. FONCTION PRINCIPALE D'ORCHESTRATION (Appelée par FastAPI /api/simulate)
# ==============================================================================

def run_wind_tunnel_simulation(
    preset_id: str = "gt3_wing",
    speed_kmh: float = 200.0,
    aoa_deg: float = 8.0,
    chord_m: float = 0.35,
    span_m: float = 1.80,
    temp_celsius: float = 20.0,
    num_segments: int = 60
) -> Dict[str, Any]:
    """
    Point d'entrée unique de la soufflerie 2D (Palier 1 : Spécialité Mathématiques).
    Exécute toute la chaîne mathématique et retourne un dictionnaire JSON complet :
    - Chiffres clés (KPIs de télémétrie)
    - Formules LaTeX théoriques ET applications numériques injectées avec les valeurs réelles
    - Géométrie et panneaux pour le rendu HTML5 Canvas
    """
    presets = get_presets()
    if preset_id not in presets:
        preset_id = "gt3_wing"
    preset = presets[preset_id]

    # 1. Grandeurs physiques de l'écoulement
    v_ms = kmh_to_ms(speed_kmh)
    rho = compute_air_density(temp_celsius)
    q_dyn = compute_dynamic_pressure(rho, v_ms)

    # 2. Discrétisation géométrique & Rotation d'angle d'attaque
    geom = discretize_profile(preset_id, chord_m, aoa_deg, num_segments)
    upper_pts = geom["upper_points"]
    lower_pts = geom["lower_points"]

    # 3. Calcul des dérivées, normales et pressions sur chaque segment
    upper_panels = analyze_surface_panels(upper_pts, "upper", aoa_deg, v_ms, q_dyn)
    lower_panels = analyze_surface_panels(lower_pts, "lower", aoa_deg, v_ms, q_dyn)

    # 4. Intégration numérique (Sommes de Riemann)
    kpis = integrate_aerodynamic_forces(
        upper_panels, lower_panels, chord_m, span_m, aoa_deg, q_dyn
    )

    # Puissance absorbée par la traînée : P = F_x * v
    power_drag_watts = kpis["drag_force_n"] * v_ms
    power_drag_hp = power_drag_watts / 735.49875

    # Extraction d'un segment témoin à mi-corde (x ≈ 50%) pour illustrer le calcul de dérivée au lycéen
    mid_idx = len(lower_panels) // 2
    sample_panel = lower_panels[mid_idx]
    v_max_intrados_kmh = max(p["local_speed_kmh"] for p in lower_panels)
    cp_min_intrados = min(p["cp"] for p in lower_panels)

    # 5. Préparation des formules LaTeX (Théorie vs Application Numérique en direct)
    math_steps = [
        {
            "step": 1,
            "title": "Fonction du profil & Dérivée locale (Spé Maths)",
            "chapter": preset["math_chapter"],
            "theory_latex": (
                preset["latex_up"] + r" \quad ; \quad " + preset["latex_low"] +
                r" \implies f'(x_i) \approx \frac{y_{i+1} - y_i}{x_{i+1} - x_i}"
            ),
            "numeric_latex": (
                rf"\text{{Au point milieu intrados }} (x = {sample_panel['x_mid']:.2f}\text{{ m}}) : "
                rf"f'(x) \approx \frac{{{sample_panel['dy']:.4f}}}{{{sample_panel['dx']:.4f}}} "
                rf"= {sample_panel['derivative_f_prime']:.3f} "
                rf"\implies \vec{{n}}_{{\text{{ext}}}} = \begin{{pmatrix}} {sample_panel['nx']:.2f} \\ {sample_panel['ny']:.2f} \end{{pmatrix}}"
            ),
        },
        {
            "step": 2,
            "title": "Pression Dynamique & Théorème de Bernoulli",
            "chapter": "Second degré & Fonction Racine Carrée",
            "theory_latex": (
                r"q_{\infty} = \frac{1}{2}\rho v_{\infty}^2 \quad \text{et} \quad "
                r"v_{\text{local}} = v_{\infty}\sqrt{1 - C_p}"
            ),
            "numeric_latex": (
                rf"q_{{\infty}} = \frac{{1}}{{2}} \times {rho:.3f} \times ({v_ms:.1f})^2 = {q_dyn:.0f}\text{{ Pa}} "
                rf"\quad ; \quad v_{{\max\text{{ (intrados)}}}} = {speed_kmh:.0f}\sqrt{{1 - ({cp_min_intrados:.2f})}} "
                rf"= {v_max_intrados_kmh:.1f}\text{{ km/h}}"
            ),
        },
        {
            "step": 3,
            "title": "Intégration des forces par Sommes de Riemann (Calcul Intégral)",
            "chapter": "Intégration sur un segment subdivisé en N panneaux",
            "theory_latex": (
                r"F_{\text{appui}} = L_{\text{envergure}} \int_{\text{profil}} -\Delta P(s) \, n_y \, ds "
                r"\approx L_{\text{envergure}} \sum_{i=1}^{N} -\left(C_{p,i} \cdot q_{\infty} \cdot n_{y,i}\right) \Delta s_i"
            ),
            "numeric_latex": (
                rf"F_{{\text{{appui}}}} = {kpis['downforce_n']:.0f}\text{{ N}} \,\, ({kpis['downforce_kgf']:.1f}\text{{ kgf}}) "
                rf"\quad | \quad F_{{\text{{traînée}}}} = {kpis['drag_force_n']:.0f}\text{{ N}} \,\, ({kpis['drag_force_kgf']:.1f}\text{{ kgf}})"
            ),
        },
        {
            "step": 4,
            "title": "Coefficients Aérodynamiques & Puissance Absorbée",
            "chapter": "Analyse dimensionnelle & Fonction cube (P = F . v)",
            "theory_latex": (
                r"C_z = \frac{F_{\text{appui}}}{q_{\infty} S_{\text{ref}}} \quad ; \quad "
                r"C_x = \frac{F_{\text{traînée}}}{q_{\infty} S_{\text{ref}}} \quad ; \quad "
                r"P_{\text{aéro}} = F_{\text{traînée}} \cdot v_{\infty} = \frac{1}{2}\rho S_{\text{ref}} C_x v_{\infty}^3"
            ),
            "numeric_latex": (
                rf"C_z = {kpis['cz']:.3f} \quad ; \quad C_x = {kpis['cx']:.3f} \quad ; \quad "
                rf"\text{{Finesse }} E = \frac{{C_z}}{{C_x}} = {kpis['aero_efficiency_l_d']:.2f} \quad ; \quad "
                rf"P_{{\text{{absorbée}}}} = {power_drag_hp:.1f}\text{{ ch}}"
            ),
        },
    ]

    # 6. Lignes de courant pour l'animation Canvas
    streamlines = generate_streamlines(
        upper_pts, lower_pts, chord_m, aoa_deg, v_ms, kpis["cz"]
    )

    return {
        "preset": {
            "id": preset["id"],
            "name": preset["name"],
            "inspiration": preset["inspiration"],
            "category": preset["category"],
            "description": preset["description"],
            "math_chapter": preset["math_chapter"],
        },
        "inputs": {
            "speed_kmh": speed_kmh,
            "speed_ms": round(v_ms, 2),
            "aoa_deg": aoa_deg,
            "chord_m": chord_m,
            "span_m": span_m,
            "temp_celsius": temp_celsius,
            "air_density_kg_m3": round(rho, 4),
            "dynamic_pressure_pa": round(q_dyn, 1),
            "num_segments": num_segments,
        },
        "kpis": {
            **kpis,
            "power_drag_watts": round(power_drag_watts, 0),
            "power_drag_hp": round(power_drag_hp, 1),
            "v_max_intrados_kmh": round(v_max_intrados_kmh, 1),
            "cp_min_intrados": round(cp_min_intrados, 3),
            "stall_warning": abs(aoa_deg) > 15.0,
        },
        "math_steps": math_steps,
        "geometry": {
            "upper_points": [{"x": round(x, 5), "y": round(y, 5)} for x, y in upper_pts],
            "lower_points": [{"x": round(x, 5), "y": round(y, 5)} for x, y in lower_pts],
            "upper_panels": upper_panels,
            "lower_panels": lower_panels,
            "streamlines": streamlines,
        },
    }


# Alias pour conformité avec PLAN.md et SPECIFICATIONS.md
run_simulation_tier1 = run_wind_tunnel_simulation


if __name__ == "__main__":
    # Auto-test rapide en ligne de commande pour vérifier les calculs sur les 5 profils
    print("=== TEST DU MOTEUR MATHÉMATIQUE AEROCARS (Palier 1 - Spé Maths) ===")
    for pid, pdata in get_presets().items():
        res = run_wind_tunnel_simulation(
            preset_id=pid,
            speed_kmh=250.0,
            aoa_deg=pdata["default_aoa_deg"],
            chord_m=pdata["default_chord_m"],
            span_m=pdata["default_span_m"],
        )
        k = res["kpis"]
        print(
            f"[{res['preset']['name']}] à 250 km/h (AoA={pdata['default_aoa_deg']}°) -> "
            f"Cz={k['cz']:.3f} | Cx={k['cx']:.3f} | "
            f"Appui={k['downforce_kgf']:.1f} kgf | Traînée={k['drag_force_kgf']:.1f} kgf | "
            f"Finesse={k['aero_efficiency_l_d']:.2f} | Puissance={k['power_drag_hp']:.1f} ch"
        )
