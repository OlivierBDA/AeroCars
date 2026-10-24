# Plan de Développement Étape par Étape — Projet "AeroCars" (v1.0)

Ce plan guide l'implémentation séquentielle du projet par Google Antigravity. Chaque étape doit être validée avant de passer à la suivante.

---

## Phase 1 : Initialisation et Structure du Projet
1. Créer l'arborescence suivante :
   ```text
   aerocars/
   ├── .env.example
   ├── requirements.txt
   ├── main.py                # Serveur FastAPI et routes API
   ├── aero_profiles.py       # Définition mathématique des 5 profils prédéfinis
   ├── aero_math.py           # Cœur mathématique Palier 1 (Spé Maths Terminale)
   ├── llm_client.py          # Client Google GenAI avec fallback 3.8-flash -> 3.5-flash-lite
   └── static/
       ├── index.html         # Interface principale (Tailwind + KaTeX via CDN)
       ├── style.css          # Styles personnalisés (Thème sombre télémétrie)
       └── app.js             # Logique Frontend, Canvas 2D et appels API
   ```
2. Rédiger `requirements.txt` avec les dépendances strictement nécessaires :
   * `fastapi`
   * `uvicorn`
   * `pydantic`
   * `python-dotenv`
   * `google-genai`

---

## Phase 2 : Définition des 5 Profils Aérodynamiques (`aero_profiles.py`)
1. Implémenter un dictionnaire ou des classes de profils contenant pour chacun des 5 éléments :
   * `id`, `name`, `car_inspiration`, `description`, `chord_length` ($L$ en mètres).
   * Une fonction explicite `y_upper(x)` (extrados) et `y_lower(x)` (intrados) utilisant des polynômes, des fonctions racines carrées ou trigonométriques simples (niveau Terminale) ainsi que l'expression LaTeX correspondante pour l'affichage.
2. Les 5 profils à coder :
   * `gt3_wing` : Aileron Arrière GT3 (inspiré Porsche 911 GT3 RS).
   * `front_splitter` : Lame Avant / Splitter (inspiré Ferrari Daytona SP3).
   * `rear_diffuser` : Diffuseur Arrière à Effet de Sol (inspiré Hypercar WEC / McLaren Senna).
   * `longtail_teardrop` : Profil Goutte d'Eau Basse Traînée (inspiré McLaren Speedtail).
   * `airbrake_wing` : Aileron Frein Aérodynamique (inspiré Bugatti Chiron).

---

## Phase 3 : Cœur Mathématique Pédagogique (`aero_math.py`)
1. Coder la fonction `run_simulation_tier1(profile_id: str, velocity_kmh: float, angle_deg: float, num_segments: int) -> dict`.
2. Structurer le code avec des commentaires pédagogiques clairs faisant référence au programme de Terminale Spécialité Maths :
   * **Fonction 1 :** Conversion des unités ($\text{km/h} \to \text{m/s}$, $\text{degrés} \to \text{radians}$) et calcul de la pression dynamique $q_{\infty} = \frac{1}{2} \rho v^2$.
   * **Fonction 2 :** Discrétisation de l'intervalle $[0, L]$ en $N$ segments et application de la rotation d'angle $\alpha$.
   * **Fonction 3 :** Calcul sur chaque segment du taux de variation (dérivée $\frac{\Delta y}{\Delta x}$), de la longueur d'arc $\Delta s$, du vecteur normal unitaire $\vec{n}$ et du produit scalaire avec le vecteur vitesse du vent $\vec{u}_{\infty}$.
   * **Fonction 4 :** Calcul du coefficient de pression $C_{p,i}$, de la force élémentaire $\vec{dF}_i$ et **intégration numérique par somme de Riemann** ($\sum \vec{dF}_i$).
   * **Fonction 5 :** Calcul des KPIs finaux ($F_{\text{appui}}$, $F_x$, $C_z$, $C_x$, Finesse $E$, Masse d'appui équivalente en $\text{kg}$, Puissance absorbée par la traînée en chevaux $\text{ch}$).
3. Retourner un dictionnaire complet incluant les coordonnées des segments, les vecteurs normaux et les pressions locales pour que le Canvas 2D puisse les dessiner.

---

## Phase 4 : Client LLM avec Fallback Automatique (`llm_client.py`)
1. Configurer le client `google.genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))`.
2. Implémenter un gestionnaire de requêtes avec :
   * Modèle primaire : `gemini-3.8-flash`
   * Modèle de secours : `gemini-3.5-flash-lite`
3. Ajouter un suivi local des appels (compteur glissant RPM par minute et RPD par jour) et un bloc `try...except` autour de l'appel API :
   * Si le quota local est atteint ou si l'API lève une erreur (notamment `429` / `ResourceExhausted` ou `NotFound`), basculer immédiatement sur `gemini-3.5-flash-lite`.
4. Rédiger le prompt système pour que Gemini réponde en Markdown avec des formules LaTeX (`$...$` et `$$...$$`), en adoptant le ton d'un ingénieur de course pédagogue s'adressant à un futur étudiant d'école d'ingénieur automobile (ESTACA).

---

## Phase 5 : Serveur Backend FastAPI (`main.py`)
1. Créer les endpoints suivants :
   * `GET /api/profiles` : Retourne la liste des 5 profils prédéfinis et leurs métadonnées.
   * `POST /api/simulate` : Exécute `run_simulation_tier1` et renvoie tous les points géométriques, vecteurs, pressions et KPIs en temps réel.
   * `POST /api/explain` : Appelle `llm_client.py` avec les résultats de la simulation courante et renvoie l'explication pédagogique ainsi que le modèle utilisé.
2. Monter le dossier `static/` sur la route racine `/` pour servir l'interface web.

---

## Phase 6 : Interface Graphique "Cockpit Télémétrie" (`static/`)
1. **`index.html` :**
   * Intégrer TailwindCSS, KaTeX (avec `auto-render`) et Marked.js (pour le rendu Markdown de Gemini) via CDN.
   * Construire la grille en 4 zones (Contrôles à gauche, Soufflerie Canvas au centre-haut, Cartes KPIs au centre-bas, Panneau Math & IA à droite).
   * Ajouter le sélecteur des 3 Paliers Mathématiques en haut (Palier 1 actif, Paliers 2 et 3 affichant une modale ou un bandeau *"En préparation pour la v2 : Nombres Complexes (Joukowski) & Équations Différentielles"*).
2. **`app.js` :**
   * Déclencher `/api/simulate` automatiquement dès qu'un slider ($v_{\infty}$, $\alpha$, $N$) ou le profil change (temps de réponse $< 20\text{ ms}$).
   * **Moteur de rendu Canvas 2D :**
     * Dessiner la grille de la soufflerie.
     * Dessiner le profil aérodynamique (polygone fermé + segments visibles pour illustrer la discrétisation $N$).
     * Dessiner sur chaque segment le vecteur force de pression $\vec{dF}_i$ (flèches rouges pour la surpression, cyan pour la succion/dépression).
     * Animer en boucle (`requestAnimationFrame`) un flux de particules / lignes de courant qui s'incurvent autour du profil et accélèrent dans les zones de dépression.
   * Mettre à jour les formules KaTeX du panneau droit avec les vraies valeurs numériques de la simulation.
   * Gérer le clic sur le bouton **"Expliquer avec Gemini"** avec un indicateur de chargement et le rendu formaté de la réponse (Markdown + LaTeX).

---

## Phase 7 : Tests et Vérification
1. Vérifier que la modification du nombre de segments $N$ (de $10$ à $200$) montre bien la convergence des intégrales $F_x$ et $F_z$.
2. Vérifier que l'augmentation de la vitesse $v_{\infty}$ multiplie bien les forces de manière quadratique ($v^2$).
3. Tester le mécanisme de fallback Gemini (en simulant une limite atteinte ou en vérifiant la réponse du modèle de secours).