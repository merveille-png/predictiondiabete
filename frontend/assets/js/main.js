/* ==========================================================================
   DiaCheck — logique frontend
   - Appel AJAX (fetch) vers l'API FastAPI pour évaluer le risque
   - Petites animations d'interface (reveal au scroll, navbar au scroll)
   ========================================================================== */

// Chemin relatif : la page est servie par la même API FastAPI (voir app.py),
// donc pas besoin de coder l'adresse en dur.
const API_URL = "/api/evaluer-risque";

document.addEventListener("DOMContentLoaded", () => {
  initNavbarScroll();
  initRevealAuScroll();
  initFormulaireDepistage();
  initBpmHero();
  initDeconnexion();
});

/* ---------- Déconnexion ---------- */
function initDeconnexion() {
  const bouton = document.getElementById("bouton-deconnexion");
  if (!bouton) return;
  bouton.addEventListener("click", async () => {
    await fetch("/api/deconnexion", { method: "POST" }).catch(() => {});
    window.location.href = "/connexion";
  });
}

/* ---------- Trace ECG réutilisable (HTML injecté dans le hero + les popups) ---------- */
const POINTS_ECG =
  "0,65 40,65 55,50 70,65 100,65 115,65 125,100 135,10 145,120 155,65 175,65 195,65 210,45 225,65 260,65 300,65";

function ecgTraceHtml(classeRisque) {
  const classeTrack = classeRisque ? `ecg-track risque-${classeRisque}` : "ecg-track";
  return `
    <div class="ecg-scroller">
      <div class="${classeTrack}">
        <svg class="ecg-trace" viewBox="0 0 300 130" preserveAspectRatio="none"><polyline points="${POINTS_ECG}" /></svg>
        <svg class="ecg-trace" viewBox="0 0 300 130" preserveAspectRatio="none"><polyline points="${POINTS_ECG}" /></svg>
      </div>
    </div>`;
}

/* ---------- BPM affiché sur le moniteur du hero (petit effet "en direct") ---------- */
function initBpmHero() {
  const bpmEl = document.getElementById("bpm-hero");
  if (!bpmEl) return;
  setInterval(() => {
    const bpm = 70 + Math.floor(Math.random() * 6); // léger frémissement 70-75
    bpmEl.firstChild.textContent = bpm;
  }, 2400);
}

/* ---------- Navbar : ombre renforcée au scroll ---------- */
function initNavbarScroll() {
  const navbar = document.querySelector(".navbar-dia");
  if (!navbar) return;
  const auScroll = () => {
    navbar.classList.toggle("shadow-sm", window.scrollY > 10);
  };
  document.addEventListener("scroll", auScroll, { passive: true });
  auScroll();
}

/* ---------- Animation d'apparition au scroll ---------- */
function initRevealAuScroll() {
  const elements = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || elements.length === 0) {
    elements.forEach((el) => el.classList.add("visible"));
    return;
  }
  const observateur = new IntersectionObserver(
    (entries) => {
      entries.forEach((entree) => {
        if (entree.isIntersecting) {
          entree.target.classList.add("visible");
          observateur.unobserve(entree.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  elements.forEach((el) => observateur.observe(el));
}

/* ---------- Formulaire de dépistage (appel AJAX vers l'API + SweetAlert2) ---------- */
const ICONE_PAR_CATEGORIE = { faible: "success", "modéré": "warning", "élevé": "error" };
const COULEUR_PAR_CATEGORIE = { faible: "#16a34a", "modéré": "#d97706", "élevé": "#dc2626" };
const CLASSE_PAR_CATEGORIE = { faible: "faible", "modéré": "modere", "élevé": "eleve" };

/* ---------- Réinitialisation du formulaire ---------- */
function reinitialiserFormulaire() {
  const formulaire = document.getElementById("formulaire-depistage");
  if (!formulaire) return;
  formulaire.reset(); // remet grossesses=0 et antécédents=0.2 (valeurs par défaut du HTML), vide le reste
  const premierChamp = document.getElementById("age");
  if (premierChamp) premierChamp.focus();
}

function initFormulaireDepistage() {
  const formulaire = document.getElementById("formulaire-depistage");
  if (!formulaire) return;

  const boutonSoumettre = document.getElementById("bouton-soumettre");
  const boutonReinitialiser = document.getElementById("bouton-reinitialiser");
  const nombreOuNull = (valeur) => (valeur === "" ? null : Number(valeur));

  if (boutonReinitialiser) {
    boutonReinitialiser.addEventListener("click", reinitialiserFormulaire);
  }

  formulaire.addEventListener("submit", async (evenement) => {
    evenement.preventDefault();

    const donnees = {
      age: Number(document.getElementById("age").value),
      grossesses: Number(document.getElementById("grossesses").value || 0),
      glycemie: nombreOuNull(document.getElementById("glycemie").value),
      tension_systolique: nombreOuNull(document.getElementById("tension_systolique").value),
      epaisseur_peau: nombreOuNull(document.getElementById("epaisseur_peau").value),
      insuline: nombreOuNull(document.getElementById("insuline").value),
      imc: nombreOuNull(document.getElementById("imc").value),
      antecedents_familiaux: Number(document.getElementById("antecedents_familiaux").value || 0.2),
    };

    boutonSoumettre.disabled = true;

    Swal.fire({
      title: "Calcul en cours...",
      html: `
        <div class="ecg-mini-ecran">${ecgTraceHtml()}</div>
        <p class="text-body-secondary mb-0">Analyse de tes données de santé...</p>
      `,
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
    });

    try {
      const reponse = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(donnees),
      });

      if (reponse.status === 401) {
        window.location.href = "/connexion";
        return;
      }

      if (!reponse.ok) {
        const detail = await reponse.json().catch(() => null);
        throw new Error(
          detail && detail.detail ? JSON.stringify(detail.detail) : `Erreur API (${reponse.status})`
        );
      }

      const resultat = await reponse.json();
      afficherResultatSweetAlert(resultat);
    } catch (erreur) {
      Swal.fire({
        icon: "error",
        title: "Impossible de contacter l'API",
        html:
          `${erreur.message}<br><br>` +
          `Vérifie que le serveur tourne bien (<code>uvicorn app:app --reload</code>) ` +
          `et que l'URL configurée dans <code>main.js</code> correspond à son adresse.`,
        confirmButtonText: "Compris",
        confirmButtonColor: "#e11d48",
      });
    } finally {
      boutonSoumettre.disabled = false;
    }
  });
}

const TITRE_PAR_CATEGORIE = {
  faible: "Risque faible",
  "modéré": "Risque modéré",
  "élevé": "Risque élevé",
};

const SOUS_TITRE_PAR_CATEGORIE = {
  faible: "Continue sur cette lancée",
  "modéré": "Quelques ajustements peuvent faire la différence",
  "élevé": "Ne néglige pas ce signal",
};

const CONSEILS_PAR_CATEGORIE = {
  faible: [
    "Continue à bouger au moins 30 min/jour et à manger équilibré.",
    "Garde un poids santé (IMC entre 18,5 et 25).",
    "Refais un dépistage tous les 3 ans, ou plus tôt en cas d'antécédents familiaux.",
  ],
  "modéré": [
    "Réduis les sucres raffinés et les boissons sucrées dans ton alimentation.",
    "Augmente ton activité physique hebdomadaire (marche rapide, vélo, natation...).",
    "Fais un bilan glycémique avec un professionnel de santé dans les prochains mois.",
  ],
  "élevé": [
    "Prends rendez-vous avec un médecin dès que possible pour un bilan complet.",
    "Surveille les signes d'alerte : soif excessive, fatigue inhabituelle, vision floue.",
    "Fais suivre aussi ta tension artérielle et ton cholestérol.",
  ],
};

function afficherResultatSweetAlert(resultat) {
  const icone = ICONE_PAR_CATEGORIE[resultat.categorie] || "info";
  const couleur = COULEUR_PAR_CATEGORIE[resultat.categorie] || "#e11d48";
  const classeRisque = CLASSE_PAR_CATEGORIE[resultat.categorie] || "faible";
  const titre = TITRE_PAR_CATEGORIE[resultat.categorie] || `Risque ${resultat.categorie}`;
  const sousTitre = SOUS_TITRE_PAR_CATEGORIE[resultat.categorie] || "";
  const conseils = CONSEILS_PAR_CATEGORIE[resultat.categorie] || [];

  const listeConseils = conseils
    .map((conseil) => `<li class="d-flex align-items-start gap-2 mb-2">
        <i class="bi bi-check-circle-fill mt-1" style="color:${couleur}; flex-shrink:0;"></i>
        <span>${conseil}</span>
      </li>`)
    .join("");

  Swal.fire({
    icon: icone,
    title: titre,
    width: 480,
    confirmButtonText: "Compris",
    confirmButtonColor: "#e11d48",
    footer: '<a href="#conseils" onclick="Swal.close()">Voir tous les conseils santé <i class="bi bi-arrow-right"></i></a>',
    html: `
      <p class="text-body-secondary mb-3">${sousTitre}</p>

      <div class="ecg-mini-ecran">${ecgTraceHtml(classeRisque)}</div>

      <p class="display-5 fw-bold mb-2" style="color:${couleur};">${resultat.risque_pourcentage}%</p>
      <div class="jauge-risque mb-3">
        <div class="remplissage" style="width:${resultat.risque_pourcentage}%; background:${couleur};"></div>
      </div>

      <div class="alert-recommandation mb-3">
        <i class="bi bi-info-circle-fill me-1"></i> ${resultat.recommandation}
      </div>

      <div class="text-start">
        <p class="fw-semibold mb-2"><i class="bi bi-lightbulb-fill me-1" style="color:#f59e0b;"></i>Conseils pour toi</p>
        <ul class="list-unstyled mb-0">${listeConseils}</ul>
      </div>
    `,
    didClose: reinitialiserFormulaire,
  });
}
