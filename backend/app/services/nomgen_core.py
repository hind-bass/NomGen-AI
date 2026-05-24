"""
Service principal NomGen AI — v3.1
Ajout : logging structuré (stratégie, modèle, durée, noms générés).
"""
import logging
import time as _time
import json
import os
import random

import torch
import torch.nn.functional as F

from app.models.nanogpt import NanoGPT
from app.services.scorer import score_fr, score_ar
from app.services.prompt_nlu import parse_prompt

# ── Configuration du logger ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-14s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nomgen.core")

WEIGHTS_DIR    = os.path.join(os.path.dirname(__file__), "..", "weights")
MODEL_CONFIG   = dict(n_embed=64, n_head=4, n_layer=4, block_size=32, dropout=0.0)
MODEL_CONFIG_CAT = dict(n_embed=64, n_head=4, n_layer=4, block_size=24, dropout=0.0)


class NomGenService:

    def __init__(self):
        _t0 = _time.perf_counter()
        logger.info("Chargement des modèles principaux…")

        self.vocab_fr = self._load_vocab("vocab_fr.json")
        self.vocab_ar = self._load_vocab("vocab_ar.json")
        self.model_fr = self._load_model(
            "model_fr.pt", len(self.vocab_fr["stoi"]), MODEL_CONFIG
        )
        self.model_ar = self._load_model(
            "model_ar.pt", len(self.vocab_ar["stoi"]), MODEL_CONFIG
        )
        self._cat_cache: dict = {}

        elapsed = round((_time.perf_counter() - _t0) * 1000)
        logger.info(
            "Modèles principaux prêts | vocab_fr=%d vocab_ar=%d | %dms",
            len(self.vocab_fr["stoi"]),
            len(self.vocab_ar["stoi"]),
            elapsed,
        )

    # ── Chargement ────────────────────────────────────────────────────────────
    def _load_vocab(self, filename: str) -> dict:
        path = os.path.join(WEIGHTS_DIR, filename)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_model(self, filename: str, vocab_size: int, config: dict) -> NanoGPT:
        path  = os.path.join(WEIGHTS_DIR, filename)
        model = NanoGPT(vocab_size=vocab_size, **config)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        logger.debug("Modèle chargé : %s (%d params)", filename, model.count_params())
        return model

    def _get_category_model(
        self, lang: str, type_: str, secteur: str
    ) -> tuple | None:
        """
        Retourne (model, vocab) pour un modèle spécialisé Sprint5 si disponible,
        sinon None (fallback vers modèle unifié Sprint3_v2).
        """
        tag      = f"{lang}_{type_}_{secteur}"
        pt_path  = os.path.join(WEIGHTS_DIR, f"model_{tag}.pt")
        voc_path = os.path.join(WEIGHTS_DIR, f"vocab_{tag}.json")

        if tag in self._cat_cache:
            return self._cat_cache[tag]

        if os.path.exists(pt_path) and os.path.exists(voc_path):
            try:
                vocab = self._load_vocab(f"vocab_{tag}.json")
                model = self._load_model(
                    f"model_{tag}.pt", len(vocab["stoi"]), MODEL_CONFIG_CAT
                )
                self._cat_cache[tag] = (model, vocab)
                logger.info("Modèle spécialisé chargé en cache : %s", tag)
                return model, vocab
            except Exception as exc:
                logger.warning("Impossible de charger le modèle %s : %s", tag, exc)

        self._cat_cache[tag] = None
        return None

    # ── Génération principale ─────────────────────────────────────────────────
    def generate(
        self,
        prompt: str,
        secteur: str,
        generation_type: str,
        langue: str,
        n: int,
        temperature: float,
        top_k: int,
        seed: int | None,
    ) -> dict:
        """
        Sélectionne la meilleure stratégie disponible et génère n noms.
        Stratégies (par ordre de priorité) :
          1. Modèle spécialisé Sprint5 : model_{lang}_{type}_{secteur}.pt
          2. Modèle unifié Sprint3_v2 avec token de contrôle
          3. Fallback NLU legacy (token #L, #T…)
        """
        _t0 = _time.perf_counter()

        if seed is not None:
            torch.manual_seed(seed)
            random.seed(seed)

        score_fn = score_fr if langue == "fr" else score_ar
        type_    = (generation_type or "marque").lower()
        sect     = (secteur or "general").lower()

        # ── Stratégie 1 : modèle spécialisé ──────────────────────────────────
        cat_result = self._get_category_model(langue, type_, sect)
        if cat_result is not None:
            cat_model, cat_vocab = cat_result
            stoi = cat_vocab["stoi"]
            itos = {int(v): k for k, v in stoi.items()}
            names    = self._run_simple(cat_model, stoi, itos, n, temperature, top_k)
            strategy = f"specialise:{langue}_{type_}_{sect}"

        else:
            # ── Stratégie 2 : token de contrôle ──────────────────────────────
            vocab = self.vocab_fr if langue == "fr" else self.vocab_ar
            model = self.model_fr if langue == "fr" else self.model_ar
            stoi  = vocab["stoi"]
            itos  = {int(v): k for k, v in stoi.items()}

            ctrl_token = f"#{type_.upper()}#{sect.upper()}#"
            if all(c in stoi for c in ctrl_token):
                names    = self._run_conditioned(model, stoi, itos, ctrl_token, n, temperature, top_k)
                strategy = f"unifie:{ctrl_token}"
            else:
                # ── Stratégie 3 : NLU legacy ──────────────────────────────────
                tokens = parse_prompt(prompt) if prompt else [f"#{sect[0].upper()}"]
                names  = self._run_generation(model, stoi, itos, tokens[0], n, temperature, top_k)
                strategy = f"nlu:{tokens[0]}"

        elapsed = round((_time.perf_counter() - _t0) * 1000, 1)

        logger.info(
            "strategy=%-30s lang=%s type=%-8s sect=%-10s "
            "n_req=%d n_gen=%d temp=%.1f time=%.0fms",
            strategy, langue, type_, sect,
            n, len(names), temperature, elapsed,
        )

        return {
            "noms": [
                {
                    "nom":     nm,
                    "score":   score_fn(nm),
                    "langue":  langue,
                    "secteur": secteur,
                    "type":    generation_type,
                }
                for nm in names
            ],
            "tokens": [strategy],
        }

    # ── Stratégie 1 : modèle spécialisé (sans token de contrôle) ─────────────
    @torch.no_grad()
    def _run_simple(
        self, model: NanoGPT, stoi: dict, itos: dict,
        n: int, temperature: float, top_k: int,
    ) -> list[str]:
        names  = []
        pad_id = stoi.get("\n", 0)
        block  = model.block_size

        for _ in range(n * 4):
            ctx   = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -1] = pad_id
            chars = []
            for _ in range(18):
                logits, _ = model(ctx)
                logits     = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                ch = itos.get(ix, "")
                if ch in ("\n", ""):
                    break
                chars.append(ch)
                new        = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx        = new
            nm = "".join(chars).strip()
            if 3 <= len(nm) <= 15 and nm not in names:
                names.append(nm)
            if len(names) >= n:
                break
        return names[:n]

    # ── Stratégie 2 : token de contrôle (modèle unifié Sprint3_v2) ───────────
    @torch.no_grad()
    def _run_conditioned(
        self, model: NanoGPT, stoi: dict, itos: dict,
        ctrl_token: str, n: int, temperature: float, top_k: int,
    ) -> list[str]:
        names  = []
        block  = model.block_size

        for _ in range(n * 4):
            ctx_ids = [stoi[c] for c in ctrl_token if c in stoi]
            ctx     = torch.zeros((1, block), dtype=torch.long)
            for j, cid in enumerate(ctx_ids[-block:]):
                ctx[0, -(len(ctx_ids)) + j] = cid
            chars = []
            for _ in range(20):
                logits, _ = model(ctx)
                logits     = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                ch = itos.get(ix, "")
                if ch in ("\n", "#", ""):
                    break
                chars.append(ch)
                new        = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx        = new
            nm = "".join(chars).split("#")[-1].strip()
            if 3 <= len(nm) <= 15 and nm not in names:
                names.append(nm)
            if len(names) >= n:
                break
        return names[:n]

    # ── Stratégie 3 : NLU legacy (Sprint3 original) ───────────────────────────
    @torch.no_grad()
    def _run_generation(
        self, model: NanoGPT, stoi: dict, itos: dict,
        ctrl_token: str, n: int, temperature: float, top_k: int,
    ) -> list[str]:
        names   = []
        ctrl_id = stoi.get(ctrl_token, 0)
        pad_id  = stoi.get(".", 0)
        block   = model.block_size

        for _ in range(n * 3):
            ctx        = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -2] = ctrl_id
            ctx[0, -1] = pad_id
            chars = []
            for _ in range(18):
                logits, _ = model(ctx)
                logits     = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                if ix == pad_id:
                    break
                ch = itos.get(ix, "")
                if ch.startswith("#"):
                    break
                chars.append(ch)
                new        = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx        = new
            nm = "".join(chars)
            if 3 <= len(nm) <= 15:
                names.append(nm)
            if len(names) >= n:
                break
        return names[:n]