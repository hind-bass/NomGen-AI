"""
Service principal NomGen AI.
Charge les modèles PyTorch AU DÉMARRAGE (une seule fois) et expose generate().
"""
import torch
import torch.nn.functional as F
import json
import os
import random

from app.models.nanogpt import NanoGPT
from app.services.scorer import score_fr, score_ar
from app.services.prompt_nlu import parse_prompt

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "..", "weights")

# Hyperparamètres du modèle (doivent correspondre aux notebooks)
MODEL_CONFIG = dict(n_embed=64, n_head=4, n_layer=4, block_size=24, dropout=0.0)


class NomGenService:
    def __init__(self):
        print("[NomGenService] Chargement des modèles...")
        # ── Vocabulaires ────────────────────────────────────────
        with open(f"{WEIGHTS_DIR}/vocab_fr.json", encoding="utf-8") as f:
            self.vocab_fr = json.load(f)
        with open(f"{WEIGHTS_DIR}/vocab_ar.json", encoding="utf-8") as f:
            self.vocab_ar = json.load(f)

        # ── Modèles ─────────────────────────────────────────────
        self.model_fr = self._load(
            f"{WEIGHTS_DIR}/model_fr.pt", len(self.vocab_fr["stoi"])
        )
        self.model_ar = self._load(
            f"{WEIGHTS_DIR}/model_ar.pt", len(self.vocab_ar["stoi"])
        )
        print("[NomGenService] Modèles chargés ✓")

    def _load(self, path, vocab_size):
        model = NanoGPT(vocab_size=vocab_size, **MODEL_CONFIG)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        return model

    def generate(self, prompt, secteur, langue, n,
                 temperature, top_k, seed):
        tokens   = parse_prompt(prompt) if prompt else [f"#{secteur[0].upper()}"]
        vocab    = self.vocab_fr if langue == "fr" else self.vocab_ar
        model    = self.model_fr if langue == "fr" else self.model_ar
        score_fn = score_fr      if langue == "fr" else score_ar

        # Extraction sécurisée de stoi
        stoi = vocab["stoi"]
        
        # CORRECTION : Reconstruction dynamique de itos à partir de stoi pour éviter le crash KeyError
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
        names = []
        ctrl_id = stoi.get(ctrl_token, 0)
        pad_id  = stoi.get(".", 0)
        block   = model.block_size

        for _ in range(n * 3):
            ctx  = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -2] = ctrl_id
            ctx[0, -1] = pad_id
            chars = []

            for _ in range(18):
                # CORRECTION : On déballe le tuple (logits, loss) renvoyé par le forward de NanoGPT
                logits, _ = model(ctx)
                
                # Extraction sécurisée de l'étape de prédiction
                logits = logits[:, -1, :] / max(temperature, 1e-5)
                
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                probs    = F.softmax(logits, dim=-1)
                ix       = torch.multinomial(probs, 1).item()
                if ix == pad_id:
                    break
                ch = itos.get(ix, "")
                if ch.startswith("#"):
                    break
                chars.append(ch)
                new = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx = new

            nm = "".join(chars)
            if 3 <= len(nm) <= 15:
                names.append(nm)
            if len(names) >= n:
                break

        return names[:n]