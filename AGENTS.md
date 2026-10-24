# AGENTS.md — Directives de Développement pour Google Antigravity

## Contexte du Projet
Tu développes **AeroCars**, une application éducative de soufflerie aérodynamique 2D en Python (FastAPI) et Vanilla JS (Canvas HTML5).
L'utilisateur final est un lycéen de 17 ans en **Terminale (Spécialité Mathématiques et Option Maths Expertes)** passionné par l'ingénierie des voitures de sport et le pilotage, qui lira directement le code Python pour étudier comment les mathématiques de son programme scolaire s'appliquent à l'aérodynamique automobile.

---

## Règles d'Or d'Implémentation (CRITIQUES)

### 1. Pédagogie et Lisibilité du Code Mathématique (`aero_math.py`)
* **INTERDICTION d'utiliser des bibliothèques boîtes noires** (`scipy`, `numpy.trapz`, solveurs matriciels complexes) pour le Palier 1. Utilise uniquement le module standard `math` de Python (`math.sin`, `math.cos`, `math.sqrt`, `math.pi`).
* **Privilégie les boucles `for` explicites** aux compréhensions de listes cryptiques lors du calcul des dérivées et des intégrales. L'élève doit pouvoir suivre pas à pas l'itération $i$ de $0$ à $N-1$.
* **Commentaires Mathématiques :** Chaque étape de calcul dans `aero_math.py` doit être précédée d'un commentaire expliquant la notion de Terminale utilisée :
  * Taux de variation et nombre dérivé : $f'(x) \approx \frac{y_{i+1} - y_i}{x_{i+1} - x_i}$
  * Vecteur normal et produit scalaire : $\vec{u} \cdot \vec{n} = u_x n_x + u_y n_y$
  * Intégration par somme de Riemann : $\int_0^L f(x)dx \approx \sum_{i=0}^{N-1} f(x_i) \Delta s_i$

### 2. Architecture Frontend Sans Build Node.js
* **NE CRÉE PAS** de `package.json`, `node_modules`, ni de configuration Webpack/Vite/React.
* Tout le frontend doit résider dans le dossier `static/` (`index.html`, `style.css`, `app.js`) et être servi directement par FastAPI.
* Utilise des liens CDN fiables pour :
  * **TailwindCSS** (`https://cdn.tailwindcss.com`)
  * **KaTeX** (`https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js` et son CSS) pour le rendu des équations mathématiques.
  * **Marked.js** (`https://cdn.jsdelivr.net/npm/marked/marked.min.js`) pour formater les explications de Gemini.

### 3. Gestion Stricte des Modèles LLM et du Fallback (`llm_client.py`)
* Utilise exclusivement le nouveau SDK officiel **`google-genai`** (`from google import genai`). N'utilise pas l'ancien package déprécié `google-generativeai`.
* Respecte scrupuleusement les identifiants des deux modèles demandés :
  * Modèle par défaut : `"gemini-3.8-flash"`
  * Modèle de secours (fallback) : `"gemini-3.5-flash-lite"`
* Implémente un limiteur de débit local (ex. max 5 RPM / 50 RPD configurables pour le modèle primaire) **ET** un bloc `try / except Exception` autour de `client.models.generate_content(...)`.
* Si `gemini-3.8-flash` dépasse son quota local ou renvoie une erreur API (429 ResourceExhausted, 404, 503, etc.), bascule immédiatement et silencieusement sur `gemini-3.5-flash-lite`.
* Si aucune clé `GEMINI_API_KEY` n'est présente dans l'environnement (`.env`), l'application ne doit pas planter : renvoie un message pédagogique simulé expliquant comment configurer la clé API dans le fichier `.env`.

### 4. Respect du Périmètre Version 1.0 (Évolutivité)
* **Pas d'outil de dessin à main levée en v1.0 :** Implémente uniquement le sélecteur des 5 éléments aérodynamiques prédéfinis dans `aero_profiles.py`.
* **Structure à 3 Paliers Mathématiques :**
  * Le **Palier 1** (Géométrie, Dérivées, Intégrales) doit être $100\%$ fonctionnel.
  * Les **Paliers 2** (Nombres Complexes / Joukowski) et **Palier 3** (Équations Différentielles / Vitesse max) doivent apparaître sous forme d'onglets dans l'interface utilisateur, mais afficher un écran d'aperçu pédagogique indiquant *"Module prévu pour la Phase 2 du projet"* avec un aperçu des formules qui y seront codées.

### 5. Design & Expérience Utilisateur (Cockpit Sport Auto)
* Adopte une esthétique **Ingénierie de Course / Télémétrie** (fond gris très sombre `#0b0f19`, panneaux `#111827`, bordures subtiles `#1f2937`, accents Rouge Course `#ef4444`, Cyan Aérodynamique `#06b6d4` et Vert Performance `#10b981`).
* Utilise une police à chasse fixe (`font-mono`) pour tous les chiffres clés ($C_x$, $C_z$, forces en $\text{N}$, appui en $\text{kg}$, puissance en $\text{ch}$) afin que les valeurs ne sautent pas visuellement lorsqu'on déplace les curseurs.
* Le Canvas 2D doit être fluide ($60\text{ FPS}$) et redimensionnable proprement.

### 6. Gestion du Dépôt Git & Déploiement Distant
* **Pousser vers GitHub uniquement sur demande explicite :** Ne JAMAIS exécuter de `git push` vers le dépôt distant de manière proactive ou autonome. Un push vers GitHub ne doit être réalisé QUE lorsque l'utilisateur le demande explicitement.
* **Sécurité des données sensibles :** S'assurer impérativement que les fichiers d'environnement (`.env`), les clés d'API, les dossiers virtuels (`.venv/`) et les caches (`__pycache__/`) sont toujours exclus via `.gitignore` et ne sont jamais commités.

---

## Commandes de Lancement Cibles (Windows)
Le projet généré doit pouvoir être lancé sur Windows en 3 commandes simples :
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Puis ouverture dans Google Chrome sur `http://127.0.0.1:8000`.