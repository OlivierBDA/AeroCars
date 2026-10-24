/**
 * app.js - AeroCars Soufflerie Aérodynamique 2D (v1.0)
 * ===================================================
 * Logique client :
 * - Gestion réactive des paramètres physiques (Vitesse, AoA, Segments N).
 * - Moteur de rendu Canvas 2D (profil discret, vecteurs normaux et de pression, particules).
 * - Télémétrie en direct et injection numérique KaTeX.
 * - Appel à l'API LLM Gemini avec affichage Markdown/LaTeX.
 */

// ==============================================================================
// 1. ÉTAT DE L'APPLICATION
// ==============================================================================
const state = {
  presets: {},
  selectedPresetId: "gt3_wing",
  speedKmh: 200,
  aoaDeg: 8.0,
  numSegments: 60,
  showForces: true,
  showNormals: false,
  showStreamlines: true,
  simData: null,
  activeRightTab: "math", // "math" ou "ai"
  animId: null,
  particles: [],
  // Gestion du zoom et du déplacement dans la soufflerie
  zoomLevel: 1.0,
  panOffset: { x: 0, y: 0 },
  isDragging: false,
  dragStart: { x: 0, y: 0 },
};

// ==============================================================================
// 2. ÉLÉMENTS DU DOM
// ==============================================================================
const dom = {
  profileSelect: document.getElementById("profileSelect"),
  carInspirationBadge: document.getElementById("carInspirationBadge"),
  chordSpanBadge: document.getElementById("chordSpanBadge"),
  profileDescriptionText: document.getElementById("profileDescriptionText"),
  mathChapterBadge: document.getElementById("mathChapterBadge"),

  speedSlider: document.getElementById("speedSlider"),
  speedVal: document.getElementById("speedVal"),
  speedMsVal: document.getElementById("speedMsVal"),

  aoaSlider: document.getElementById("aoaSlider"),
  aoaVal: document.getElementById("aoaVal"),
  aoaRadVal: document.getElementById("aoaRadVal"),

  segmentsSlider: document.getElementById("segmentsSlider"),
  segmentsVal: document.getElementById("segmentsVal"),

  toggleForces: document.getElementById("toggleForces"),
  toggleNormals: document.getElementById("toggleNormals"),
  toggleStreamlines: document.getElementById("toggleStreamlines"),

  canvas: document.getElementById("windTunnelCanvas"),
  overlayQdyn: document.getElementById("overlayQdyn"),
  overlayVmax: document.getElementById("overlayVmax"),
  scaleIndicator: document.getElementById("scaleIndicator"),
  btnResetView: document.getElementById("btnResetView"),
  btnZoomIn: document.getElementById("btnZoomIn"),
  btnZoomOut: document.getElementById("btnZoomOut"),
  btnFitView: document.getElementById("btnFitView"),

  kpiDownforceKg: document.getElementById("kpiDownforceKg"),
  kpiDownforceN: document.getElementById("kpiDownforceN"),
  kpiDragN: document.getElementById("kpiDragN"),
  kpiPowerHp: document.getElementById("kpiPowerHp"),
  kpiCz: document.getElementById("kpiCz"),
  kpiCx: document.getElementById("kpiCx"),
  kpiEfficiency: document.getElementById("kpiEfficiency"),
  stallWarningBadge: document.getElementById("stallWarningBadge"),

  tabRightMath: document.getElementById("tabRightMath"),
  tabRightAi: document.getElementById("tabRightAi"),
  panelMathView: document.getElementById("panelMathView"),
  panelAiView: document.getElementById("panelAiView"),
  aiModelIndicator: document.getElementById("aiModelIndicator"),
  headerModelBadge: document.getElementById("headerModelBadge"),
  btnExplain: document.getElementById("btnExplain"),
  btnTriggerAiInner: document.getElementById("btnTriggerAiInner"),
  aiLoadingState: document.getElementById("aiLoadingState"),
  aiContentContainer: document.getElementById("aiContentContainer"),

  tabTier1: document.getElementById("tabTier1") || document.getElementById("tab-tier1"),
  tabTier2: document.getElementById("tabTier2") || document.getElementById("tab-tier2"),
  tabTier3: document.getElementById("tabTier3") || document.getElementById("tab-tier3"),
  tierModal: document.getElementById("tierModal"),
  modalTitle: document.getElementById("modalTitle"),
  modalIconContainer: document.getElementById("modalIconContainer"),
  modalBody: document.getElementById("modalBody"),
  btnCloseModal: document.getElementById("btnCloseModal"),
  btnConfirmModal: document.getElementById("btnConfirmModal"),
};

// ==============================================================================
// 3. INITIALISATION & CHARGEMENT DES PROFILS
// ==============================================================================
async function initApp() {
  initCanvas();
  initParticles();
  setupEventListeners();

  try {
    const res = await fetch("/api/presets");
    const presetsList = await res.json();
    
    // Remplissage du select
    if (dom.profileSelect) {
      dom.profileSelect.innerHTML = "";
      presetsList.forEach(p => {
        state.presets[p.id] = p;
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.inspiration})`;
        opt.className = "bg-[#0d1424] text-white py-1.5 px-2";
        if (p.id === state.selectedPresetId) {
          opt.selected = true;
        }
        dom.profileSelect.appendChild(opt);
      });
    }

    if (presetsList.length > 0) {
      state.selectedPresetId = presetsList[0].id;
      if (dom.profileSelect) {
        dom.profileSelect.value = state.selectedPresetId;
      }
      applyPresetDefaults(state.selectedPresetId);
    }

    // Première simulation
    await triggerSimulation();
  } catch (err) {
    console.error("Erreur lors de l'initialisation :", err);
  }

  // Rendu global KaTeX pour les titres et badges avec LaTeX inline ($...$)
  renderAllPageMath();

  // Lancement de la boucle de rendu Canvas 60 FPS
  requestAnimationFrame(canvasRenderLoop);
}

function renderAllPageMath() {
  if (typeof renderMathInElement !== "undefined") {
    try {
      renderMathInElement(document.body, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\[", right: "\\]", display: true },
          { left: "\\(", right: "\\)", display: false }
        ],
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
        throwOnError: false
      });
    } catch (e) {
      console.warn("KaTeX render error on page elements:", e);
    }
  } else {
    setTimeout(renderAllPageMath, 250);
  }
}

function applyPresetDefaults(presetId) {
  const p = state.presets[presetId];
  if (!p) return;

  if (dom.carInspirationBadge) dom.carInspirationBadge.textContent = p.inspiration;
  if (dom.chordSpanBadge) dom.chordSpanBadge.textContent = `L = ${p.default_chord_m.toFixed(2)}m | b = ${p.default_span_m.toFixed(2)}m`;
  if (dom.profileDescriptionText) dom.profileDescriptionText.textContent = p.description;
  if (dom.mathChapterBadge) dom.mathChapterBadge.textContent = p.math_chapter;

  state.aoaDeg = p.default_aoa_deg;
  if (dom.aoaSlider) dom.aoaSlider.value = state.aoaDeg;
  updateSliderLabels();
}

// ==============================================================================
// 4. APPEL À L'API DE SIMULATION (/api/simulate)
// ==============================================================================
let simDebounceTimer = null;

function debouncedSimulation() {
  clearTimeout(simDebounceTimer);
  simDebounceTimer = setTimeout(triggerSimulation, 15);
}

async function triggerSimulation() {
  updateSliderLabels();
  const currentPreset = state.presets[state.selectedPresetId];
  const payload = {
    preset_id: state.selectedPresetId,
    speed_kmh: parseFloat(state.speedKmh),
    aoa_deg: parseFloat(state.aoaDeg),
    num_segments: parseInt(state.numSegments),
    chord_m: currentPreset ? currentPreset.default_chord_m : 0.35,
    span_m: currentPreset ? currentPreset.default_span_m : 1.80,
  };

  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error("Erreur de simulation serveur");
    state.simData = await response.json();

    updateTelemetryUi(state.simData);
    updateMathFormulas(state.simData);
  } catch (err) {
    console.error("Échec de la simulation :", err);
  }
}

// ==============================================================================
// 5. MISE À JOUR DE L'INTERFACE TÉLÉMÉTRIE
// ==============================================================================
function updateSliderLabels() {
  const speedMs = (state.speedKmh / 3.6).toFixed(1);
  if (dom.speedVal) dom.speedVal.textContent = state.speedKmh;
  if (dom.speedMsVal) dom.speedMsVal.textContent = speedMs;

  const aoaRad = (state.aoaDeg * Math.PI / 180).toFixed(2);
  if (dom.aoaVal) dom.aoaVal.textContent = (state.aoaDeg >= 0 ? "+" : "") + Number(state.aoaDeg).toFixed(1);
  if (dom.aoaRadVal) dom.aoaRadVal.textContent = (aoaRad >= 0 ? "+" : "") + aoaRad;

  if (dom.segmentsVal) dom.segmentsVal.textContent = state.numSegments;
}

function updateTelemetryUi(data) {
  if (!data || !data.kpis) return;
  const k = data.kpis;

  if (dom.kpiDownforceKg) dom.kpiDownforceKg.textContent = k.downforce_kgf.toFixed(1);
  if (dom.kpiDownforceN) dom.kpiDownforceN.textContent = Math.round(k.downforce_n).toLocaleString();

  if (dom.kpiDragN) dom.kpiDragN.textContent = Math.round(k.drag_force_n).toLocaleString();
  if (dom.kpiPowerHp) dom.kpiPowerHp.textContent = k.power_drag_hp.toFixed(1);

  if (dom.kpiCz) dom.kpiCz.textContent = k.cz.toFixed(3);
  if (dom.kpiCx) dom.kpiCx.textContent = k.cx.toFixed(3);
  if (dom.kpiEfficiency) dom.kpiEfficiency.textContent = k.aero_efficiency_l_d.toFixed(2);

  if (dom.stallWarningBadge) {
    if (k.stallWarning) {
      dom.stallWarningBadge.innerHTML = `<span class="text-red-400 font-bold">⚠️ Décrochage turbulent!</span>`;
    } else {
      dom.stallWarningBadge.innerHTML = `<span class="text-emerald-400">✓ Flux attaché stable</span>`;
    }
  }

  if (dom.overlayQdyn) dom.overlayQdyn.textContent = `${Math.round(data.inputs.dynamic_pressure_pa)} Pa`;
  if (dom.overlayVmax) dom.overlayVmax.textContent = `${k.v_max_intrados_kmh.toFixed(0)} km/h`;
  if (dom.scaleIndicator) dom.scaleIndicator.textContent = `L = ${data.inputs.chord_m.toFixed(2)} m (${state.numSegments} segments)`;
}

// ==============================================================================
// 6. INJECTION NUMÉRIQUE DYNAMIQUE DANS KATEX
// ==============================================================================
function renderKatexSafe(elementId, latexStr, isBlock = false) {
  const el = document.getElementById(elementId);
  if (!el || typeof katex === "undefined") return;
  try {
    katex.render(latexStr, el, {
      displayMode: isBlock,
      throwOnError: false
    });
  } catch (e) {
    el.textContent = latexStr;
  }
}

function updateMathFormulas(data) {
  if (!data || !data.math_steps) return;
  const steps = data.math_steps;

  steps.forEach(step => {
    const idTheory = `mathStep${step.step}Theory`;
    const idNumeric = `mathStep${step.step}Numeric`;
    renderKatexSafe(idTheory, step.theory_latex, false);
    renderKatexSafe(idNumeric, step.numeric_latex, false);
  });
}

// ==============================================================================
// 7. MOTEUR DE RENDU DU CANVAS 2D (SOUFFLERIE AÉRODYNAMIQUE)
// ==============================================================================
let ctx = null;
let canvasWidth = 800;
let canvasHeight = 450;

function initCanvas() {
  if (!dom.canvas) return;
  ctx = dom.canvas.getContext("2d");
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
}

function resizeCanvas() {
  if (!dom.canvas) return;
  const parent = dom.canvas.parentElement;
  if (!parent) return;

  const rect = parent.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvasWidth = Math.max(rect.width, 300);
  canvasHeight = Math.max(rect.height, 250);

  dom.canvas.width = canvasWidth * dpr;
  dom.canvas.height = canvasHeight * dpr;
  dom.canvas.style.width = `${canvasWidth}px`;
  dom.canvas.style.height = `${canvasHeight}px`;

  // Réinitialisation de la matrice avant application du DPR
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
}

function initParticles() {
  state.particles = [];
  const numLines = 16;
  const particlesPerLine = 4;
  for (let l = 0; l < numLines; l++) {
    // Fraction verticale de la ligne dans [-1, +1]
    const lineFrac = (l / (numLines - 1)) * 2.0 - 1.0;
    for (let p = 0; p < particlesPerLine; p++) {
      state.particles.push({
        lineFrac: lineFrac,
        u: (p / particlesPerLine) + Math.random() * (0.8 / particlesPerLine),
        speedMult: 0.95 + Math.random() * 0.1,
        length: 16 + Math.random() * 8,
        opacity: 0.35 + Math.random() * 0.55
      });
    }
  }
}

/**
 * Modèle aérodynamique d'écoulement potentiel continu C-infini :
 * Déplacement fluide régulier par distribution gaussienne d'obstacle,
 * circulation de Kutta-Joukowski (downwash lisse) et gradient de vitesse de Bernoulli.
 * Zéro discontinuité, zéro angle droit, zéro traversée du profil.
 */
function getAirflowPoint(xScreen, lineFrac, w, h, chordLength, scale, originX, originY) {
  // Coordonnées physiques du point d'entrée non perturbé
  const xPhys = (xScreen - originX) / scale;
  const ySpanPhys = (h * 0.44) / scale;
  const y0Phys = lineFrac * ySpanPhys;

  if (!state.simData || !state.simData.geometry) {
    return { x: xScreen, y: originY - y0Phys * scale, vRatio: 1.0 };
  }

  const geom = state.simData.geometry;
  const upper = geom.upper_points || [];
  const lower = geom.lower_points || [];
  const cz = (state.simData.kpis && state.simData.kpis.cz !== undefined) ? state.simData.kpis.cz : 0.58;

  if (upper.length === 0 || lower.length === 0) {
    return { x: xScreen, y: originY - y0Phys * scale, vRatio: 1.0 };
  }

  const pLead = upper[0];
  const pTrail = upper[upper.length - 1];

  // Vecteur corde et repère orthonormé associé au profil
  const chordVecX = pTrail.x - pLead.x;
  const chordVecY = pTrail.y - pLead.y;
  const actualChordLen = Math.max(0.01, Math.sqrt(chordVecX * chordVecX + chordVecY * chordVecY));

  // Vecteur tangent unitaire t_c (du bord d'attaque vers le bord de fuite)
  const tx = chordVecX / actualChordLen;
  const ty = chordVecY / actualChordLen;

  // Vecteur normal unitaire n_c (orienté vers l'extrados)
  const nx = -ty;
  const ny = tx;

  // Position relative par rapport au bord d'attaque
  const dx = xPhys - pLead.x;
  const dy = y0Phys - pLead.y;

  // Coordonnée s le long de la corde et distance h perpendiculaire à la corde
  const s = dx * tx + dy * ty;
  const hDist = dx * nx + dy * ny;

  // Hauteurs maximales physiques de l'extrados et de l'intrados
  let maxUpH = 0.04 * actualChordLen;
  let maxLowH = 0.04 * actualChordLen;
  for (let pt of upper) {
    const curH = (pt.x - pLead.x) * nx + (pt.y - pLead.y) * ny;
    if (curH > maxUpH) maxUpH = curH;
  }
  for (let pt of lower) {
    const curH = -((pt.x - pLead.x) * nx + (pt.y - pLead.y) * ny);
    if (curH > maxLowH) maxLowH = curH;
  }

  // Marge de sécurité aérodynamique
  const clearance = 0.016 * actualChordLen;
  const isExtrados = hDist >= 0;
  const peakThickness = (isExtrados ? maxUpH : maxLowH) + clearance;

  // 1. Déplacement régulier de l'obstacle (bosse gaussienne en cloche sur la corde)
  const sigmaS = 0.36 * actualChordLen;
  const peakPosS = 0.38 * actualChordLen;
  const ds = (s - peakPosS) / sigmaS;
  const bellS = Math.exp(-0.5 * ds * ds);

  // Atténuation en hauteur selon la loi dipolaire de Laplace : 1 / (1 + (h / sigmaH)^2)
  const sigmaH = 0.30 * actualChordLen;
  const dh = hDist / sigmaH;
  const lorentzH = 1.0 / (1.0 + dh * dh);

  // Déplacement normal induit par l'épaisseur
  const thickDeflection = (isExtrados ? 1.0 : -1.0) * peakThickness * bellS * lorentzH;

  // 2. Déviation de portance / sillage (Downwash de Kutta-Joukowski via fonction arctan lisse)
  const liftTransition = 0.5 + (1.0 / Math.PI) * Math.atan((s - peakPosS) / (0.32 * actualChordLen));
  const dhLift = hDist / (0.45 * actualChordLen);
  const liftDecayH = 1.0 / (1.0 + dhLift * dhLift);
  const liftDeflection = - cz * 0.042 * actualChordLen * liftTransition * liftDecayH;

  const totalNormalDeflection = thickDeflection + liftDeflection;

  // Position finale défléchie en coordonnées physiques
  const deflPhysX = xPhys + totalNormalDeflection * nx;
  const deflPhysY = y0Phys + totalNormalDeflection * ny;

  // 3. Calcul de la vitesse locale relative selon Bernoulli (accélération Venturi sous l'intrados)
  let vRatio = 1.0;
  if (!isExtrados) {
    // Accélération dépressionnaire sous l'aileron / diffuseur
    vRatio = Math.min(2.1, 1.0 + 0.52 * cz * bellS * lorentzH);
  } else {
    // Léger ralentissement en surpression sur l'extrados
    vRatio = Math.max(0.55, 1.0 - 0.22 * cz * bellS * lorentzH);
  }

  // Ralentissement au point d'arrêt du bord d'attaque
  const distFromLead = Math.sqrt(dx * dx + dy * dy);
  if (distFromLead < 0.22 * actualChordLen) {
    const normDist = distFromLead / (0.12 * actualChordLen);
    const stagFactor = Math.exp(-normDist * normDist);
    vRatio = Math.max(0.42, vRatio * (1.0 - 0.58 * stagFactor));
  }

  return {
    x: originX + deflPhysX * scale,
    y: originY - deflPhysY * scale,
    vRatio: vRatio
  };
}

function canvasRenderLoop() {
  try {
    drawWindTunnel();
  } catch (err) {
    console.error("Erreur de rendu canvas :", err);
  }
  state.animId = requestAnimationFrame(canvasRenderLoop);
}

function drawWindTunnel() {
  if (!ctx) return;
  const w = canvasWidth;
  const h = canvasHeight;

  // 1. Fond sombre de soufflerie
  ctx.clearRect(0, 0, w, h);

  // Grille subtile
  ctx.strokeStyle = "rgba(31, 41, 61, 0.45)";
  ctx.lineWidth = 1;
  const gridSize = 40;
  for (let x = 0; x < w; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // 2. Échelle géométrique dynamique & Centrage optimal du profil
  const chordLength = (state.simData && state.simData.inputs) ? state.simData.inputs.chord_m : 0.35;
  const baseScale = (w * 0.62) / Math.max(chordLength, 0.05);
  const scale = baseScale * state.zoomLevel;

  const originX = (w * 0.50 + state.panOffset.x) - (chordLength * 0.50) * scale;
  const originY = (h * 0.50 + state.panOffset.y);

  // Mise à jour de l'indicateur d'échelle en direct
  if (dom.scaleIndicator) {
    const chordPx = Math.round(chordLength * scale);
    const zoomPct = Math.round(state.zoomLevel * 100);
    dom.scaleIndicator.textContent = `${chordPx} px = ${chordLength.toFixed(2)} m (${zoomPct}%)`;
  }

  function toScreen(xPhys, yPhys) {
    return {
      x: originX + xPhys * scale,
      y: originY - yPhys * scale
    };
  }

  // 3. Filets d'air réalistes et Particules animées (Contournement aérodynamique continu)
  if (state.showStreamlines) {
    const numLines = 18;
    const stepPx = 10; // Échantillonnage serré pour des courbes lisses et continues

    // A. Dessin des lignes de fumée de soufflerie continues (Streamlines C-infini)
    ctx.strokeStyle = "rgba(56, 189, 248, 0.20)";
    ctx.lineWidth = 1.2;
    for (let l = 0; l < numLines; l++) {
      const lineFrac = (l / (numLines - 1)) * 2.0 - 1.0;
      ctx.beginPath();
      for (let x = -15; x <= w + 15; x += stepPx) {
        const pt = getAirflowPoint(x, lineFrac, w, h, chordLength, scale, originX, originY);
        if (x === -15) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
    }

    // B. Particules de fumée lumineuses voyageant le long de ces trajectoires
    if (state.particles.length > 0) {
      const flowSpeedBase = (state.speedKmh / 200.0) * 0.0035;

      for (let p of state.particles) {
        const currentX = p.u * w;
        const currentPt = getAirflowPoint(currentX, p.lineFrac, w, h, chordLength, scale, originX, originY);

        // Progression de la particule selon la vitesse locale de Bernoulli
        p.u += flowSpeedBase * currentPt.vRatio * p.speedMult;
        if (p.u > 1.02) {
          p.u = -0.02;
        }

        // Extrémité arrière du filet pour former une traînée lumineuse
        const trailX = Math.max(-15, currentX - p.length);
        const trailPt = getAirflowPoint(trailX, p.lineFrac, w, h, chordLength, scale, originX, originY);

        ctx.strokeStyle = `rgba(6, 182, 212, ${p.opacity * 0.85})`;
        ctx.lineWidth = 2.0;
        ctx.beginPath();
        ctx.moveTo(trailPt.x, trailPt.y);
        ctx.lineTo(currentPt.x, currentPt.y);
        ctx.stroke();
      }
    }
  }

  // 4. Dessin du profil aérodynamique (Polygone + Segments de discrétisation N)
  if (state.simData && state.simData.geometry) {
    const upper = state.simData.geometry.upper_points || [];
    const lower = state.simData.geometry.lower_points || [];

    if (upper.length > 0 && lower.length > 0) {
      ctx.beginPath();
      const ptStart = toScreen(upper[0].x, upper[0].y);
      ctx.moveTo(ptStart.x, ptStart.y);

      // Extrados de gauche à droite
      for (let i = 1; i < upper.length; i++) {
        const pt = toScreen(upper[i].x, upper[i].y);
        ctx.lineTo(pt.x, pt.y);
      }

      // Intrados de droite à gauche pour fermer le polygone
      for (let i = lower.length - 1; i >= 0; i--) {
        const pt = toScreen(lower[i].x, lower[i].y);
        ctx.lineTo(pt.x, pt.y);
      }
      ctx.closePath();

      // Remplissage profil aspect carbone / aluminium sombre
      const gradient = ctx.createLinearGradient(originX, originY - 50, originX, originY + 50);
      gradient.addColorStop(0, "#1e293b");
      gradient.addColorStop(0.5, "#0f172a");
      gradient.addColorStop(1, "#1e293b");
      ctx.fillStyle = gradient;
      ctx.fill();

      // Contour du profil
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Dessin des petits sommets pour visualiser le découpage en N segments de Riemann
      ctx.fillStyle = "#facc15";
      for (let pt of upper) {
        const sPt = toScreen(pt.x, pt.y);
        ctx.beginPath();
        ctx.arc(sPt.x, sPt.y, 1.8, 0, Math.PI * 2);
        ctx.fill();
      }
      for (let pt of lower) {
        const sPt = toScreen(pt.x, pt.y);
        ctx.beginPath();
        ctx.arc(sPt.x, sPt.y, 1.8, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // 5. Vecteurs Normaux unitaires n_i
    if (state.showNormals) {
      ctx.strokeStyle = "rgba(245, 158, 11, 0.75)";
      ctx.lineWidth = 1.2;
      const panels = [
        ...(state.simData.geometry.upper_panels || []),
        ...(state.simData.geometry.lower_panels || [])
      ];

      for (let p of panels) {
        const mid = toScreen(p.x_mid, p.y_mid);
        const normLen = 16;
        const targetX = mid.x + p.nx * normLen;
        const targetY = mid.y - p.ny * normLen;

        ctx.beginPath();
        ctx.moveTo(mid.x, mid.y);
        ctx.lineTo(targetX, targetY);
        ctx.stroke();
      }
    }

    // 6. Vecteurs Forces de pression élémentaires dF_i
    if (state.showForces) {
      const panels = [
        ...(state.simData.geometry.upper_panels || []),
        ...(state.simData.geometry.lower_panels || [])
      ];

      const maxPressure = Math.max(...panels.map(p => Math.abs(p.delta_p_pa || 0)), 1.0);
      const arrowMaxPx = 36;

      for (let p of panels) {
        const mid = toScreen(p.x_mid, p.y_mid);
        const deltaP = p.delta_p_pa || 0;
        const pLen = (Math.abs(deltaP) / maxPressure) * arrowMaxPx;

        // Si surpression (deltaP > 0) : force pousse la surface vers l'intérieur (rouge)
        // Si succion / dépression (deltaP < 0) : force tire la surface vers l'extérieur (cyan)
        const isSuction = deltaP < 0;
        ctx.strokeStyle = isSuction ? "#06b6d4" : "#ef4444";
        ctx.fillStyle = ctx.strokeStyle;
        ctx.lineWidth = 1.5;

        // Direction de la force de pression : -P * n
        const dirX = isSuction ? (p.nx) : (-p.nx);
        const dirY = isSuction ? (-p.ny) : (p.ny);

        const endX = mid.x + dirX * pLen;
        const endY = mid.y + dirY * pLen;

        ctx.beginPath();
        ctx.moveTo(mid.x, mid.y);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        // Pointe de flèche
        drawArrowHead(ctx, mid.x, mid.y, endX, endY, 4);
      }
    }

    // 7. Résultante Globale au Centre Aérodynamique (Forces Fz et Fx)
    const kpis = state.simData.kpis || {};
    const centerPoint = toScreen(chordLength * 0.35, 0.0);

    // Flèche Appui (F_appui vers le bas en convention auto pour plaquer au sol)
    const downforceN = kpis.downforce_n || 0;
    const downforcePx = Math.min((downforceN / 3500.0) * 90, 110);
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(centerPoint.x, centerPoint.y);
    ctx.lineTo(centerPoint.x, centerPoint.y + downforcePx);
    ctx.stroke();
    drawArrowHead(ctx, centerPoint.x, centerPoint.y, centerPoint.x, centerPoint.y + downforcePx, 8);

    // Flèche Traînée (Fx vers la droite)
    const dragN = kpis.drag_force_n || 0;
    const dragPx = Math.min((dragN / 1500.0) * 75, 90);
    ctx.strokeStyle = "#f87171";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(centerPoint.x, centerPoint.y);
    ctx.lineTo(centerPoint.x + dragPx, centerPoint.y);
    ctx.stroke();
    drawArrowHead(ctx, centerPoint.x, centerPoint.y, centerPoint.x + dragPx, centerPoint.y, 7);
  }
}

function drawArrowHead(ctx, fromX, fromY, toX, toY, headLength) {
  if (isNaN(fromX) || isNaN(fromY) || isNaN(toX) || isNaN(toY)) return;
  const angle = Math.atan2(toY - fromY, toX - fromX);
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

// ==============================================================================
// 8. TUTEUR IA GEMINI (/api/explain)
// ==============================================================================
async function requestGeminiExplanation() {
  if (!state.simData) return;

  // Bascule sur l'onglet IA
  switchRightTab("ai");
  if (dom.aiLoadingState) dom.aiLoadingState.classList.remove("hidden");
  if (dom.aiContentContainer) dom.aiContentContainer.innerHTML = "";

  try {
    const res = await fetch("/api/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ simulation_data: state.simData })
    });

    if (!res.ok) throw new Error("Échec de la requête vers l'assistant IA");
    const data = await res.json();

    // Mise à jour du badge de modèle utilisé
    const modelUsed = data.model_used || "gemini-3.8-flash";
    if (dom.aiModelIndicator) {
      dom.aiModelIndicator.textContent = modelUsed;
      dom.aiModelIndicator.classList.remove("hidden");
    }
    if (dom.headerModelBadge) {
      dom.headerModelBadge.textContent = modelUsed;
    }

    // Rendu Markdown via Marked.js
    let htmlContent = "";
    if (typeof marked !== "undefined") {
      htmlContent = marked.parse(data.explanation || "");
    } else {
      htmlContent = `<pre class="whitespace-pre-wrap">${data.explanation}</pre>`;
    }
    if (dom.aiContentContainer) {
      dom.aiContentContainer.innerHTML = htmlContent;

      // Rendu automatique des formules mathématiques KaTeX dans la réponse de Gemini
      if (typeof renderMathInElement !== "undefined") {
        renderMathInElement(dom.aiContentContainer, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false }
          ],
          throwOnError: false
        });
      }
    }
  } catch (err) {
    if (dom.aiContentContainer) {
      dom.aiContentContainer.innerHTML = `
        <div class="bg-red-950/40 border border-red-800 rounded-lg p-3 text-red-300">
          <p class="font-bold">Erreur de communication avec Gemini</p>
          <p class="text-xs mt-1">${err.message}</p>
        </div>
      `;
    }
  } finally {
    if (dom.aiLoadingState) dom.aiLoadingState.classList.add("hidden");
  }
}

// ==============================================================================
// 9. MODALES DES PALIERS 2 ET 3 (PHASE 2)
// ==============================================================================
function showTierModal(tierNumber) {
  if (!dom.tierModal) return;

  if (tierNumber === 2) {
    if (dom.modalTitle) dom.modalTitle.textContent = "Palier 2 : Nombres Complexes & Transformation de Joukowski";
    if (dom.modalIconContainer) {
      dom.modalIconContainer.textContent = "ℂ";
      dom.modalIconContainer.className = "w-10 h-10 rounded-xl bg-purple-900/40 border border-purple-500/40 flex items-center justify-center text-purple-400 font-bold text-lg font-mono";
    }
    if (dom.modalBody) {
      dom.modalBody.innerHTML = `
        <p class="text-purple-300 font-semibold">Programme : Terminale Option Maths Expertes (Nombres Complexes & Géométrie)</p>
        <p>
          Ce module permettra de transformer le cercle unité dans le plan complexe en un véritable profil d'aile cambré via la fonction holomorphe de Joukowski :
        </p>
        <div id="modalLatex1" class="bg-[#0b101d] p-2.5 rounded-lg border border-[#1f293d] text-center my-2"></div>
        <p>
          Le calcul de la circulation de l'air $\\Gamma$ autour du profil utilisera le théorème fondamental de Kutta-Joukowski pour déterminer la portance et l'appui de manière analytique :
        </p>
        <div id="modalLatex2" class="bg-[#0b101d] p-2.5 rounded-lg border border-[#1f293d] text-center my-2"></div>
        <p class="text-gray-400 italic text-[11px]">
          Ce module sera accessible dans la Phase 2 du projet AeroCars.
        </p>
      `;

      renderKatexSafe("modalLatex1", "Z = z + \\frac{c^2}{z} \\quad (z \\in \\mathbb{C}^*)", true);
      renderKatexSafe("modalLatex2", "L' = \\rho \\cdot v_\\infty \\cdot \\Gamma \\quad \\text{avec } \\Gamma = 2\\pi a v_\\infty \\sin(\\alpha + \\beta)", true);
    }
  } else if (tierNumber === 3) {
    if (dom.modalTitle) dom.modalTitle.textContent = "Palier 3 : Équations Différentielles & Dynamique Véhicule";
    if (dom.modalIconContainer) {
      dom.modalIconContainer.textContent = "dv/dt";
      dom.modalIconContainer.className = "w-10 h-10 rounded-xl bg-amber-900/40 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold text-sm font-mono";
    }
    if (dom.modalBody) {
      dom.modalBody.innerHTML = `
        <p class="text-amber-300 font-semibold">Programme : Terminale Spécialité Mathématiques (Équations Différentielles y' = ay + b)</p>
        <p>
          Ce module résoudra l'équation différentielle non-linéaire du mouvement de la voiture en ligne droite, en confrontant la poussée du groupe motopropulseur à la traînée aérodynamique quadratique :
        </p>
        <div id="modalLatex3" class="bg-[#0b101d] p-2.5 rounded-lg border border-[#1f293d] text-center my-2"></div>
        <p>
          Il permettra également de calculer le gain en vitesse de passage en courbe grâce à l'adhérence supplémentaire conférée par l'appui :
        </p>
        <div id="modalLatex4" class="bg-[#0b101d] p-2.5 rounded-lg border border-[#1f293d] text-center my-2"></div>
        <p class="text-gray-400 italic text-[11px]">
          Ce module sera accessible dans la Phase 2 du projet AeroCars.
        </p>
      `;

      renderKatexSafe("modalLatex3", "m \\frac{dv}{dt} = F_{\\text{moteur}}(v) - \\frac{1}{2}\\rho S C_x v^2 \\implies v_{\\max} = \\sqrt{\\frac{2 P_{\\text{moteur}}}{\\rho S C_x}}", true);
      renderKatexSafe("modalLatex4", "v_{\\text{virage}} = \\sqrt{\\frac{\\mu \\cdot (m g + F_{\\text{appui}})}{m} \\cdot R}", true);
    }
  }

  dom.tierModal.classList.remove("hidden");
}

function hideTierModal() {
  if (dom.tierModal) dom.tierModal.classList.add("hidden");
}

function switchRightTab(tab) {
  state.activeRightTab = tab;
  if (tab === "math") {
    if (dom.tabRightMath) dom.tabRightMath.className = "px-3 py-1.5 rounded-lg text-xs font-bold font-display uppercase tracking-wider bg-[#1f293d] text-cyan-400 border border-cyan-800/60 transition-colors";
    if (dom.tabRightAi) dom.tabRightAi.className = "px-3 py-1.5 rounded-lg text-xs font-bold font-display uppercase tracking-wider text-gray-400 hover:text-gray-200 transition-colors";
    if (dom.panelMathView) dom.panelMathView.classList.remove("hidden");
    if (dom.panelAiView) dom.panelAiView.classList.add("hidden");
  } else {
    if (dom.tabRightAi) dom.tabRightAi.className = "px-3 py-1.5 rounded-lg text-xs font-bold font-display uppercase tracking-wider bg-[#1f293d] text-cyan-400 border border-cyan-800/60 transition-colors";
    if (dom.tabRightMath) dom.tabRightMath.className = "px-3 py-1.5 rounded-lg text-xs font-bold font-display uppercase tracking-wider text-gray-400 hover:text-gray-200 transition-colors";
    if (dom.panelAiView) dom.panelAiView.classList.remove("hidden");
    if (dom.panelMathView) dom.panelMathView.classList.add("hidden");
  }
}

// ==============================================================================
// 10. GESTION DU ZOOM, DU CADRAGE ET DU PAN DANS LA SOUFFLERIE
// ==============================================================================
function zoomBy(factor) {
  state.zoomLevel = Math.max(0.35, Math.min(state.zoomLevel * factor, 4.5));
}

function resetZoomAndPan() {
  state.zoomLevel = 1.0;
  state.panOffset = { x: 0, y: 0 };
  resizeCanvas();
}

function setupCanvasInteractions() {
  const canvas = dom.canvas;
  if (!canvas) return;

  // Zoom avec la molette de la souris
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.87;
    zoomBy(factor);
  }, { passive: false });

  // Déplacement libre à la souris (Pan / Drag)
  canvas.addEventListener("mousedown", (e) => {
    state.isDragging = true;
    state.dragStart = { x: e.clientX, y: e.clientY };
    canvas.classList.remove("cursor-grab");
    canvas.classList.add("cursor-grabbing");
  });

  window.addEventListener("mousemove", (e) => {
    if (!state.isDragging) return;
    const dx = e.clientX - state.dragStart.x;
    const dy = e.clientY - state.dragStart.y;
    state.panOffset.x += dx;
    state.panOffset.y += dy;
    state.dragStart = { x: e.clientX, y: e.clientY };
  });

  window.addEventListener("mouseup", () => {
    if (state.isDragging) {
      state.isDragging = false;
      if (canvas) {
        canvas.classList.remove("cursor-grabbing");
        canvas.classList.add("cursor-grab");
      }
    }
  });
}

// ==============================================================================
// 11. GESTION DES ÉVÉNEMENTS UTILISATEUR
// ==============================================================================
function setupEventListeners() {
  // Changement de profil
  if (dom.profileSelect) {
    dom.profileSelect.addEventListener("change", (e) => {
      state.selectedPresetId = e.target.value;
      applyPresetDefaults(state.selectedPresetId);
      triggerSimulation();
    });
  }

  // Sliders
  if (dom.speedSlider) {
    dom.speedSlider.addEventListener("input", (e) => {
      state.speedKmh = parseFloat(e.target.value);
      debouncedSimulation();
    });
  }

  if (dom.aoaSlider) {
    dom.aoaSlider.addEventListener("input", (e) => {
      state.aoaDeg = parseFloat(e.target.value);
      debouncedSimulation();
    });
  }

  if (dom.segmentsSlider) {
    dom.segmentsSlider.addEventListener("input", (e) => {
      state.numSegments = parseInt(e.target.value);
      debouncedSimulation();
    });
  }

  // Toggles Canvas
  if (dom.toggleForces) {
    dom.toggleForces.addEventListener("change", (e) => {
      state.showForces = e.target.checked;
    });
  }
  if (dom.toggleNormals) {
    dom.toggleNormals.addEventListener("change", (e) => {
      state.showNormals = e.target.checked;
    });
  }
  if (dom.toggleStreamlines) {
    dom.toggleStreamlines.addEventListener("change", (e) => {
      state.showStreamlines = e.target.checked;
    });
  }

  // Boutons de Zoom et Cadrage
  if (dom.btnZoomIn) {
    dom.btnZoomIn.addEventListener("click", () => zoomBy(1.25));
  }
  if (dom.btnZoomOut) {
    dom.btnZoomOut.addEventListener("click", () => zoomBy(0.80));
  }
  if (dom.btnFitView) {
    dom.btnFitView.addEventListener("click", () => resetZoomAndPan());
  }
  if (dom.btnResetView) {
    dom.btnResetView.addEventListener("click", () => resetZoomAndPan());
  }

  // Interactions souris (Zoom molette et Pan)
  setupCanvasInteractions();

  // Onglets Panneau Droit
  if (dom.tabRightMath) dom.tabRightMath.addEventListener("click", () => switchRightTab("math"));
  if (dom.tabRightAi) dom.tabRightAi.addEventListener("click", () => switchRightTab("ai"));

  // Déclencheur Gemini
  if (dom.btnExplain) dom.btnExplain.addEventListener("click", requestGeminiExplanation);
  if (dom.btnTriggerAiInner) dom.btnTriggerAiInner.addEventListener("click", requestGeminiExplanation);

  // Onglets Paliers Header
  if (dom.tabTier1) {
    dom.tabTier1.addEventListener("click", () => {
      // Déjà sur le palier 1
    });
  }
  if (dom.tabTier2) dom.tabTier2.addEventListener("click", () => showTierModal(2));
  if (dom.tabTier3) dom.tabTier3.addEventListener("click", () => showTierModal(3));

  // Modale
  if (dom.btnCloseModal) dom.btnCloseModal.addEventListener("click", hideTierModal);
  if (dom.btnConfirmModal) dom.btnConfirmModal.addEventListener("click", hideTierModal);
  if (dom.tierModal) {
    dom.tierModal.addEventListener("click", (e) => {
      if (e.target === dom.tierModal) hideTierModal();
    });
  }
}

// Démarrage automatique au chargement du DOM
document.addEventListener("DOMContentLoaded", initApp);
