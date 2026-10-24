# 🏎️ AeroCars — Soufflerie Aérodynamique 2D

**AeroCars** est une application web éducative de soufflerie aérodynamique 2D interactive, conçue pour un élève de **Terminale (Spécialité Mathématiques & Option Maths Expertes)** passionné par le sport automobile, le pilotage et l'ingénierie de course.

L'objectif est d'étudier comment les mathématiques du programme scolaire (taux d'accroissement, dérivée $f'(x)$, vecteurs normaux $\vec{n}$, produit scalaire $\vec{u}\cdot\vec{n}$, pression dynamique de Bernoulli $q_\infty = \frac{1}{2}\rho v^2$ et calcul intégral par **sommes de Riemann**) s'appliquent directement au comportement aérodynamique d'une voiture de compétition ($C_x$, $C_z$, appui en kg, puissance consommée en chevaux).

---

## ⚡ Fonctionnalités Clés (Version 1.0)

* **5 Éléments Aérodynamiques Prédéfinis :**
  1. *Aileron Arrière GT3* (inspiré Porsche 911 GT3 RS) — Profil asymétrique inversé fort appui.
  2. *Goutte d'eau Longtail* (inspiré McLaren Speedtail / 917 LH) — Pénétration d'air maximale (*Low Drag*).
  3. *Lame Avant / Splitter Wedge* (inspiré Ferrari F40 / Daytona SP3) — Guidage et appui du train avant.
  4. *Diffuseur Arrière Venturi* (inspiré Hypercars WEC / Aston Martin Valkyrie) — Effet de sol dépressionnaire.
  5. *Aileron Bi-plan avec Gurney Flap* (inspiré Ferrari 296 GT3) — Cambrure agressive à fort appui.

* **Soufflerie Virtuelle Interactive (Canvas HTML5 à 60 FPS) :**
  * Filets d'air continus et soyeux contournant le profil sans le traverser (modèle d'écoulement potentiel).
  * Particules de fumée animées accélérant dans les zones de dépression (théorème de Bernoulli).
  * Affichage commutable des vecteurs normaux $\vec{n}_i$, des forces de pression locales $\vec{dF}_i$ (rouge : surpression, cyan : dépression) et de la résultante globale ($\vec{F}_{\text{appui}}$, $\vec{F}_x$).
  * Commandes de **Zoom (`+` / `−`)**, **Cadrage automatique (`🎯 Cadrer`)**, zoom à la molette et déplacement libre (*Pan/Drag*).

* **Cockpit Télémétrie en Direct :**
  * Mise à jour instantanée des KPIs : Appui ($F_{\text{appui}}$ en kg et N), Traînée ($F_x$ en N et puissance absorbée en ch : $P = F_x \cdot v$), $C_z$, $C_x$ et Finesse ($C_z/C_x$).

* **Laboratoire Mathématique & Tuteur IA Gemini :**
  * **Équations en Direct (KaTeX) :** Injection dynamique des valeurs calculées dans les formules théoriques de Terminale.
  * **Ingénieur Aérodynamicien IA :** Analyse télémétrique détaillée par **Gemini 3.8 Flash** (avec bascule automatique de secours vers `gemini-3.5-flash-lite` et mode simulation locale hors-ligne).

* **Structure Évolutive en 3 Paliers :**
  * **Palier 1 (Actif v1.0) :** Géométrie, Dérivation et Sommes de Riemann (Spé Maths).
  * **Palier 2 (Aperçu Phase 2) :** Nombres Complexes & Transformation de Joukowski ($Z = z + c^2/z$, Maths Expertes).
  * **Palier 3 (Aperçu Phase 2) :** Équations Différentielles de Dynamique Véhicule ($m \frac{dv}{dt} = F - \frac{1}{2}\rho S C_x v^2$).

---

## 🛠️ Architecture Technique (Zéro Build Node.js)

* **Backend :** Python 3.11+ avec **FastAPI** et **Uvicorn**.
* **Moteur Mathématique (`aero_math.py`) :** Python pur sans bibliothèque "boîte noire" (uniquement le module standard `math` et des boucles `for` explicites).
* **Client LLM (`llm_client.py`) :** SDK officiel `google-genai` avec limiteur de débit local et gestion de fallback silencieux.
* **Frontend (`static/`) :** HTML5, Vanilla JavaScript et CSS servis directement par FastAPI (aucun outil de compilation requis, TailwindCSS, KaTeX et Marked.js chargés via CDN).

---

## 🚀 Installation et Lancement Rapide (Windows)

1. **Cloner le dépôt et activer l'environnement virtuel :**
   ```powershell
   git clone https://github.com/OlivierBDA/AeroCars.git
   cd AeroCars
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Installer les dépendances :**
   ```powershell
   pip install -r requirements.txt
   ```

3. **(Optionnel) Configurer la clé API Gemini :**
   Copiez `.env.example` en `.env` et ajoutez votre clé :
   ```env
   GEMINI_API_KEY=votre_cle_gemini_ici
   ```
   *(Sans clé, l'application fonctionnera en mode simulation pédagogique locale sans planter).*

4. **Démarrer le serveur :**
   ```powershell
   uvicorn main:app --reload
   ```
   Ouvrez ensuite votre navigateur sur : **http://127.0.0.1:8000**

---

## 📚 Documentation Détaillée

Pour approfondir les aspects du projet, consultez les documents de référence :
* [SPECIFICATIONS.md](file:///c:/Workplace/Devs/AeroCars/SPECIFICATIONS.md) — Spécifications fonctionnelles, physiques et formules détaillées.
* [PLAN.md](file:///c:/Workplace/Devs/AeroCars/PLAN.md) — Plan de développement étape par étape.
* [AGENTS.md](file:///c:/Workplace/Devs/AeroCars/AGENTS.md) — Directives pédagogiques et règles de développement.
