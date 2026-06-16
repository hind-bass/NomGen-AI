"""
Service principal NomGen AI — v4.0
Jour 2 : chargement DYNAMIQUE du modèle selon (langue, secteur).

Hiérarchie de chargement :
  1. model_{langue}_{secteur}_marque.pt   (ex: model_fr_tech_marque.pt)
  2. model_{langue}_{secteur}.pt          (ex: model_fr_tech.pt)
  3. model_{langue}.pt                    (modèle générique — fallback)

Les vocabs sont partagés par langue (un seul vocab_fr.json et vocab_ar.json).
"""
import torch
import torch.nn.functional as F
import json
import os
import random
from pathlib import Path

from app.models.nanogpt import NanoGPT
from app.services.scorer import score_fr, score_ar
from app.services.prompt_nlu import parse_prompt

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"

# Hyperparamètres du modèle — doivent correspondre aux notebooks
MODEL_CONFIG = dict(n_embed=64, n_head=4, n_layer=4, block_size=24, dropout=0.0)

# Secteurs supportés pour le chargement conditionnel
SECTEURS_CONNUS = {"tech", "food", "luxe", "general", "sante", "finance"}


def _normalise_secteur(secteur: str) -> str:
    """Convertit le secteur API vers le nom de fichier normalisé."""
    mapping = {
        "TECH": "tech", "FOOD": "food", "LUXE": "luxe",
        "BIO": "food", "PHARMA": "sante", "SANTE": "sante",
        "FINANCE": "finance", "INDUSTRIE": "general",
        "GENERAL": "general",
    }
    return mapping.get(secteur.upper(), "general")


class NomGenService:
    def __init__(self):
        print("[NomGenService] Démarrage — chargement vocabulaires...")

        # ── Vocabulaires (partagés par langue) ──────────────────────────────
        with open(WEIGHTS_DIR / "vocab_fr.json", encoding="utf-8") as f:
            self.vocab_fr = json.load(f)
        with open(WEIGHTS_DIR / "vocab_ar.json", encoding="utf-8") as f:
            self.vocab_ar = json.load(f)

        # ── Cache des modèles chargés (évite de recharger à chaque requête) ─
        self._model_cache: dict[str, NanoGPT] = {}

        # ── Pré-charger les modèles génériques (toujours disponibles) ───────
        self._model_cache["fr_generic"] = self._load_model(
            WEIGHTS_DIR / "model_fr.pt", len(self.vocab_fr["stoi"])
        )
        self._model_cache["ar_generic"] = self._load_model(
            WEIGHTS_DIR / "model_ar.pt", len(self.vocab_ar["stoi"])
        )
        print(f"[NomGenService] Modèles génériques chargés [OK]")

        # ── Tenter de charger les modèles par catégorie (s'ils existent) ────
        for secteur in SECTEURS_CONNUS:
            for langue in ["fr", "ar"]:
                vocab = self.vocab_fr if langue == "fr" else self.vocab_ar
                vocab_size = len(vocab["stoi"])

                # Essayer model_{langue}_{secteur}.pt
                path = WEIGHTS_DIR / f"model_{langue}_{secteur}.pt"
                if path.exists():
                    key = f"{langue}_{secteur}"
                    self._model_cache[key] = self._load_model(path, vocab_size)
                    print(f"  [OK] Modèle spécialisé chargé : {path.name}")

        print(f"[NomGenService] {len(self._model_cache)} modèle(s) en cache [OK]")

    def _load_model(self, path: Path, vocab_size: int) -> NanoGPT:
        """Charge un fichier .pt et retourne le modèle en mode eval."""
        model = NanoGPT(vocab_size=vocab_size, **MODEL_CONFIG)
        model.load_state_dict(torch.load(str(path), map_location="cpu"))
        model.eval()
        return model

    def _get_model(self, langue: str, secteur: str) -> NanoGPT:
        """
        Sélectionne le meilleur modèle disponible pour (langue, secteur).
        Ordre de priorité :
          1. model_{langue}_{secteur}  (spécialisé)
          2. model_{langue}_generic    (générique)
        """
        secteur_norm = _normalise_secteur(secteur)

        # Essai 1 : modèle spécialisé
        key_specialise = f"{langue}_{secteur_norm}"
        if key_specialise in self._model_cache:
            return self._model_cache[key_specialise]

        # Fallback : modèle générique
        key_generic = f"{langue}_generic"
        print(f"[NomGenService] Fallback vers modèle générique ({langue})")
        return self._model_cache[key_generic]

    def generate(self, prompt, secteur, langue, n,
                 temperature, top_k, seed):
        """Point d'entrée principal — Mode A (nanoGPT)."""
        tokens   = parse_prompt(prompt) if prompt else [f"#{secteur[0].upper()}"]
        vocab    = self.vocab_fr if langue == "fr" else self.vocab_ar
        model    = self._get_model(langue, secteur)
        score_fn = score_fr      if langue == "fr" else score_ar

        stoi = vocab["stoi"]
        itos = {int(v): k for k, v in stoi.items()}

        if seed is not None:
            torch.manual_seed(seed)
            random.seed(seed)

        names = self._run_generation(
            model, stoi, itos, tokens[0], n, temperature, top_k
        )
        return {
            "noms": [
                {"nom": nm, "score": score_fn(nm),
                 "langue": langue, "secteur": secteur}
                for nm in names
            ],
            "tokens": tokens,
        }

    @torch.no_grad()
    def _run_generation(self, model, stoi, itos, ctrl_token,
                        n, temperature, top_k):
        """Génère n noms via inférence autorégressive."""
        names    = []
        ctrl_id  = stoi.get(ctrl_token, 0)
        pad_id   = stoi.get(".", 0)
        block    = model.block_size

        for _ in range(n * 4):          # tentatives = 4× le nombre voulu
            ctx    = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -2] = ctrl_id
            ctx[0, -1] = pad_id
            chars  = []

            for _ in range(18):         # longueur max d'un nom
                logits, _ = model(ctx)
                logits = logits[:, -1, :] / max(temperature, 1e-5)

                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")

                probs  = F.softmax(logits, dim=-1)
                ix     = torch.multinomial(probs, 1).item()

                if ix == pad_id:
                    break
                ch = itos.get(ix, "")
                if ch.startswith("#"):
                    break
                chars.append(ch)

                new = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx = new

            nm = "".join(chars).strip()
            if 3 <= len(nm) <= 15:
                names.append(nm)
            if len(names) >= n:
                break

        return names[:n]