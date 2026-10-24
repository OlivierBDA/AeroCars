# Spécifications Fonctionnelles et Techniques — Projet "AeroCars" (v1.0)

## 1. Vision et Objectif Pédagogique
**AeroCars** est une application web locale de simulation de soufflerie aérodynamique 2D dédiée aux éléments de voitures de sport et de compétition. 
Elle s'adresse à un élève de Terminale (Spécialité Mathématiques & Option Maths Expertes) passionné d'ingénierie automobile et de pilotage.

L'objectif principal du projet est double :
1. **Compréhension physique et mathématique :** Relier directement les concepts du programme de Terminale (fonctions, dérivées, vecteurs normaux, trigonométrie, calcul intégral) aux phénomènes aérodynamiques réels (pression dynamique, traînée $F_x$, appui/déportance $F_z$, finesse aérodynamique).
2. **Lisibilité du code :** Le cœur mathématique en Python doit être écrit de manière ultra-pédagogique, privilégiant la clarté des formules mathématiques (boucles explicites, variables nommées selon la physique) plutôt que l'optimisation matricielle opaque.

---

## 2. Architecture Technique (Zéro Build Node.js)
L'application tourne sur Windows et s'affiche dans Google Chrome. Pour garantir une simplicité maximale de déploiement et de maintenance :

* **Backend :** Python 3.11+ avec **FastAPI** et **Uvicorn**.
  * Sert les fichiers statiques (HTML, CSS, JS).
  * Expose les endpoints API REST pour les calculs mathématiques et l'explication pédagogique via LLM.
* **Cœur Mathématique (`aero_math.py`) :** Python pur (module `math` standard uniquement, pas de `scipy` ou de solveur boîte noire).
* **Client LLM (`llm_client.py`) :** SDK officiel `google-genai` avec mécanisme de bascule automatique (Fallback) :
  * Modèle primaire : `gemini-3.8-flash`
  * Modèle de secours (si dépassement RPM/RPD ou erreur HTTP 429) : `gemini-3.5-flash-lite`
* **Frontend :** HTML5 + Vanilla JavaScript (ES6+) servis directement par FastAPI.
  * **Style :** TailwindCSS (via CDN) avec un thème sombre inspiré de la télémétrie de course automobile (WEC / F1).
  * **Visualisation 2D :** HTML5 `<canvas>` pour le rendu de l'élément aérodynamique, des vecteurs de force et de l'animation des lignes de flux d'air.
  * **Rendu Mathématique :** KaTeX (via CDN) pour afficher de vraies formules LaTeX dynamiques dans l'interface.

---

## 3. Périmètre Fonctionnel de la Version 1.0 (MVP)

### 3.1. Sélection d'Éléments Aérodynamiques Prédéfinis (Pas d'éditeur de dessin en v1)
Dans cette première version, l'utilisateur ne dessine pas librement la forme. Il sélectionne un élément aérodynamique précis parmi **5 profils prédéfinis** inspirés de voitures de sport iconiques. Chaque profil est défini mathématiquement par une fonction pour sa surface supérieure (extrados, $y_{\text{sup}}(x)$) et une fonction pour sa surface inférieure (intrados, $y_{\text{inf}}(x)$) sur un intervalle $x \in [0, L]$ (où $L$ est la corde en mètres) :

1. **Aileron Arrière GT3 (inspiré Porsche 911 GT3 RS) :**
   * Profil cambré inversé conçu pour générer un fort appui ($F_z$ vers le bas).
2. **Lame Avant / Splitter Haute Vitesse (inspiré Ferrari Daytona SP3 / GT) :**
   * Fond plat horizontal sur l'intrados et rampe progressive sur l'extrados pour plaquer le train avant.
3. **Diffuseur Arrière à Effet de Sol (inspiré McLaren Senna / Hypercars WEC) :**
   * Canal inférieur divergent (qui remonte vers l'arrière) créant une dépression sous la voiture (effet Venturi) et accélérant l'extraction d'air.
4. **Profil "Goutte d'eau" Basse Traînée / Longtail (inspiré McLaren Speedtail / Porsche 917 LH) :**
   * Profil quasi-symétrique très effilé maximisant la pénétration dans l'air (faible $C_x$).
5. **Aileron Mobile de Freinage / Airbrake (inspiré Bugatti Chiron) :**
   * Profil présentant une forte inclinaison pour maximiser simultanément l'appui et la traînée aérodynamique lors des phases de décélération.

### 3.2. Paramètres de Simulation Réglables par l'Utilisateur
Avant ou pendant la simulation, l'utilisateur peut faire varier 3 paramètres physiques via des curseurs (sliders) :
1. **Vitesse du flux d'air ($v_{\infty}$) :** de $50\text{ km/h}$ à $350\text{ km/h}$ (convertie en $\text{m/s}$ dans les équations : $v = \frac{v_{\text{km/h}}}{3.6}$).
2. **Angle d'attaque ($\alpha$) :** de $-5^{\circ}$ à $+25^{\circ}$ (converti en radians : $\alpha_{\text{rad}} = \alpha_{\text{deg}} \times \frac{\pi}{180}$).
3. **Finesse de discrétisation ($N$) :** Nombre de segments (de $10$ à $200$) utilisés pour approximer la courbe et calculer l'intégrale. Permet de visualiser concrètement la convergence d'une somme de Riemann / méthode des trapèzes vers l'intégrale exacte !

*Constantes fixées (affichées à l'écran) :*
* Masse volumique de l'air ($\rho$) = $1.225\text{ kg/m}^3$ (à $15^{\circ}\text{C}$ au niveau de la mer).
* Envergure unitaire en 2D ($b$) = $1.0\text{ m}$ (pour exprimer des forces en Newtons par mètre d'envergure).

---

## 4. Structure en 3 Paliers Mathématiques

L'interface affiche une barre de navigation permettant de choisir le **Palier Mathématique** de la soufflerie :

* **Palier 1 (ACTIF EN V1) : Géométrie, Dérivées & Calcul Intégral (Spécialité Maths)**
  * Modélisation par discrétisation géométrique de la courbe, calcul des tangentes (dérivées), des vecteurs normaux, de la pression locale et intégration numérique sur la surface.
* **Palier 2 (MENU VERROUILLÉ / PLACEHOLDER EN V1) : Nombres Complexes & Transformation de Joukowski (Maths Expertes)**
  * Affichera un panneau informatif expliquant que ce module utilisera le plan complexe $Z = z + \frac{c^2}{z}$ et le théorème de Kutta-Joukowski dans la v2.0.
* **Palier 3 (MENU VERROUILLÉ / PLACEHOLDER EN V1) : Équations Différentielles & Dynamique Véhicule (Spécialité Maths)**
  * Affichera un panneau informatif expliquant que ce module résoudra l'équation différentielle $m \frac{dv}{dt} = F_{\text{moteur}} - F_x(v)$ pour calculer la vitesse de pointe et la vitesse de passage en courbe dans la v2.0.

---

## 5. Modèle Mathématique Détaillé du Palier 1 (Spécialité Maths)

Pour que le code Python soit $100\%$ aligné avec le programme de Terminale Spécialité Maths, voici la chaîne de calcul exacte à implémenter dans `aero_math.py` :

### Étape 1 : Discrétisation et Rotation (Angle d'attaque $\alpha$)
Le profil de longueur $L$ est découpé en $N$ sous-intervalles de largeur $\Delta x = \frac{L}{N}$.
Pour chaque point $x_i = i \cdot \Delta x$ (avec $i \in \{0, \dots, N\}$), on calcule l'ordonnée $y(x_i)$ et on applique la rotation d'angle d'attaque $\alpha$ (en radians) :
$$x'_i = x_i \cos(\alpha) - y_i \sin(\alpha)$$
$$y'_i = x_i \sin(\alpha) + y_i \cos(\alpha)$$

### Étape 2 : Dérivée, Pente et Vecteur Normal sur chaque segment
Sur chaque segment $i$ reliant $M_i(x'_i, y'_i)$ à $M_{i+1}(x'_{i+1}, y'_{i+1})$ :
* **Taux de variation (approximation de la dérivée $f'(x)$) :**
  $$\Delta X_i = x'_{i+1} - x'_i \quad ; \quad \Delta Y_i = y'_{i+1} - y'_i$$
  $$f'(x_i) \approx \frac{\Delta Y_i}{\Delta X_i}$$
* **Longueur du segment (élément différentiel d'arc $ds$) :**
  $$\Delta s_i = \sqrt{(\Delta X_i)^2 + (\Delta Y_i)^2}$$
* **Vecteur tangent unitaire $\vec{t}_i$ et vecteur normal unitaire sortant $\vec{n}_i$ :**
  $$\vec{t}_i = \begin{pmatrix} \frac{\Delta X_i}{\Delta s_i} \\ \frac{\Delta Y_i}{\Delta s_i} \end{pmatrix} \quad \implies \quad \vec{n}_i = \begin{pmatrix} n_{x,i} \\ n_{y,i} \end{pmatrix}$$
  *(orienté vers le haut pour l'extrados et vers le bas pour l'intrados).*

### Étape 3 : Pression Dynamique et Coefficient de Pression ($C_p$)
L'air arrive horizontalement avec un vecteur vitesse unitaire $\vec{u}_{\infty} = \begin{pmatrix} 1 \\ 0 \end{pmatrix}$.
* **Pression dynamique du flux libre ($q_{\infty}$) :**
  $$q_{\infty} = \frac{1}{2} \rho v_{\infty}^2$$
* **Angle local d'incidence $\theta_i$ entre le flux et le segment (via le produit scalaire) :**
  $$\sin(\theta_i) = -\left( \vec{u}_{\infty} \cdot \vec{n}_i \right) = -n_{x,i}$$
* **Coefficient de pression local $C_{p,i}$ (Modèle d'impact de Newton combiné à l'effet de succion de Bernoulli simplifié) :**
  * Si la surface fait face au vent ($\sin(\theta_i) > 0$, zone de surpression / impact) :
    $$C_{p,i} = 2 \sin^2(\theta_i)$$
  * Si la surface accélère et dévie le flux ($\sin(\theta_i) < 0$, zone de dépression / succion) :
    $$C_{p,i} = -k_{\text{succion}} \cdot \sin(\theta_i) \quad (\text{avec } k_{\text{succion}} = 1.5)$$
* **Pression relative locale exercée sur le segment :**
  $$P_i = q_{\infty} \cdot C_{p,i}$$

### Étape 4 : Calcul Intégral des Forces Aérodynamiques (Somme de Riemann)
La force élémentaire $\vec{dF}_i$ exercée par la pression sur le segment de longueur $\Delta s_i$ est opposée au vecteur normal sortant :
$$\vec{dF}_i = -P_i \cdot \Delta s_i \cdot \vec{n}_i$$

En intégrant sur tous les segments de l'extrados et de l'intrados :
* **Force de Traînée (Drag $F_x$, résistance à l'avancement) :**
  $$F_x = \int_{\text{profil}} -P(s) n_x(s) \, ds \approx \sum_{i=0}^{N-1} \left( -P_i \cdot n_{x,i} \cdot \Delta s_i \right) + F_{x,\text{friction}}$$
  *(où $F_{x,\text{friction}} = \frac{1}{2} \rho v_{\infty}^2 L C_f$ avec $C_f = 0.015$ représente le frottement visqueux de peau).*
* **Force Verticale ($F_z$) et Appui Aérodynamique (Downforce) :**
  $$F_z = \int_{\text{profil}} -P(s) n_y(s) \, ds \approx \sum_{i=0}^{N-1} \left( -P_i \cdot n_{y,i} \cdot \Delta s_i \right)$$
  *(Convention affichage automobile : on définit l'**Appui** $F_{\text{appui}} = -F_z$, positif lorsque la voiture est plaquée au sol).*

### Étape 5 : Chiffres Clés (KPIs Télémétrie)
* **Coefficient de traînée ($C_x$) :** $C_x = \frac{F_x}{q_{\infty} \cdot L}$
* **Coefficient d'appui ($C_z$) :** $C_z = \frac{F_{\text{appui}}}{q_{\infty} \cdot L}$
* **Finesse / Efficacité Aérodynamique ($E$) :** $E = \frac{C_z}{C_x}$
* **Équivalent Masse Plaquée au Sol (en kg) :** $M_{\text{appui}} = \frac{F_{\text{appui}}}{g}$ (avec $g = 9.81\text{ m/s}^2$).

---

## 6. Interface Utilisateur (UI / UX) dans Chrome

L'écran est divisé en **4 zones principales** (Layout Grille Responsive en Dark Mode) :

1. **Barre Latérale Gauche (Contrôles & Profils) :**
   * Sélecteur des 3 Paliers Mathématiques (Palier 1 actif, Paliers 2 et 3 avec badge *"Bientôt disponible - v2"*).
   * Liste déroulante ou cartes pour choisir parmi les **5 éléments aérodynamiques prédéfinis** (avec une courte description de la voiture de sport associée).
   * Sliders interactifs pour la **Vitesse ($v_{\infty}$)**, l'**Angle d'attaque ($\alpha$)** et le **Nombre de segments d'intégration ($N$)**.
   * Bouton d'action principal : **"Lancer l'analyse IA (Gemini)"**.

2. **Zone Centrale Haute (Visualisation Soufflerie 2D - Canvas HTML5) :**
   * Dessin du profil géométrique discret (les $N$ segments) au centre de la soufflerie.
   * Option (case à cocher) pour afficher les **vecteurs normaux $\vec{n}_i$ et vecteurs de pression $\vec{dF}_i$** directement sur la surface du profil (colorés en rouge pour la surpression et en bleu/cyan pour la dépression/succion).
   * Animation fluide de particules / lignes de flux d'air (streamlines) traversant l'écran de gauche à droite et déviées par le profil.
   * Vecteur résultant global au centre de poussée montrant $\vec{F}_x$ (Traînée) et $\vec{F}_{\text{appui}}$ (Appui).

3. **Zone Centrale Basse (Télémétrie & Chiffres Clés) :**
   * 5 cartes de style tableau de bord d'hypercar affichant en grand :
     * **Appui ($F_{\text{appui}}$)** en $\text{N}$ et son équivalent en **$\text{kg}$ plaqués au sol**.
     * **Traînée ($F_x$)** en $\text{N}$ (et la puissance moteur nécessaire pour vaincre cette traînée : $P_{\text{aero}} = F_x \cdot v_{\infty}$ convertie en **Chevaux (ch)** via $1\text{ ch} = 735.5\text{ W}$ !).
     * **Coefficient d'Appui ($C_z$)**.
     * **Coefficient de Traînée ($C_x$)**.
     * **Finesse Aérodynamique ($C_z / C_x$)**.

4. **Panneau Droit (Laboratoire Mathématique & Explications Gemini) :**
   * **Onglet 1 : Équations en Direct (KaTeX) :** Affiche les formules mathématiques du Palier 1 (Dérivée, Produit scalaire, Intégrale de Riemann) avec l'injection en temps réel des valeurs numériques de la simulation actuelle.
   * **Onglet 2 : Tuteur Math & Ingénieur IA (Gemini) :** Affiche l'explication générée par l'API Google Gemini, structurée de façon claire (voir section 7) et affiche un badge indiquant quel modèle a répondu (`gemini-3.8-flash` ou fallback `gemini-3.5-flash-lite`).

---

## 7. Intégration de l'API Google Gemini & Gestion du Fallback

### 7.1. Rôle de l'appel LLM en v1.0
Lorsque l'utilisateur clique sur **"Expliquer les équations et résultats (Gemini)"**, le backend envoie un prompt structuré contenant :
* Le nom de l'élément aérodynamique étudié,
* Les paramètres choisis ($v_{\infty}$, $\alpha$, $N$),
* Les résultats numériques obtenus ($F_{\text{appui}}$, $F_x$, $C_z$, $C_x$, puissance absorbée en chevaux).

Le LLM (endossant le rôle d'un **Ingénieur Aérodynamicien de Course s'adressant à un élève de Terminale Spé Maths**) doit expliquer :
1. **Le lien mathématique :** Comment la dérivée (pente du profil) et le produit scalaire (angle avec le vent) ont créé la différence de pression entre le dessus et le dessous, et comment l'intégrale (somme sur les $N$ segments) a permis de calculer la force totale.
2. **L'interprétation physique et pilotage :** Ce que signifient concrètement ces chiffres pour le pilote d'essais (ex. : combien de kilos d'appui supplémentaires sur le train avant/arrière en virage, et combien de chevaux moteur sont "consommés" par la traînée à cette vitesse).

### 7.2. Logique de Bascule (Fallback) Obligatoire
Le module `llm_client.py` doit implémenter la logique suivante :
1. Tenter l'appel avec le modèle par défaut : `gemini-3.8-flash`.
2. Gérer un compteur local de requêtes (RPM / RPD) ET intercepter toute exception liée aux quotas (`429 Too Many Requests` / `ResourceExhausted` ou indisponibilité du modèle).
3. En cas de dépassement de limite ou d'erreur sur le modèle primaire, basculer **automatiquement et sans erreur visible pour l'utilisateur** sur le modèle de secours : `gemini-3.5-flash-lite`.
4. Retourner dans la réponse JSON le texte généré ainsi que le nom du modèle effectivement utilisé (`model_used`) pour l'afficher dans l'interface.