"""
Service principal NomGen AI — v3.0
Supporte deux stratégies de génération :
  A) Modèle unifié  + token de contrôle  (#MARQUE#LUXE#)
  B) Modèles dédiés par catégorie        (model_fr_marque_luxe.pt)
Fallback automatique : B → A → modèle général
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

MODEL_CONFIG = dict(n_embed=64, n_head=4, n_layer=4, block_size=32, dropout=0.0)
MODEL_CONFIG_CAT = dict(n_embed=64, n_head=4, n_layer=4, block_size=24, dropout=0.0)


class NomGenService:
    def __init__(self):
        print("[NomGenService] Chargement des modèles...")
        # ── Modèles et vocabs unifiés (toujours présents) ────────
        self.vocab_fr   = self._load_vocab("vocab_fr.json")
        self.vocab_ar   = self._load_vocab("vocab_ar.json")
        self.model_fr   = self._load_model("model_fr.pt", len(self.vocab_fr["stoi"]), MODEL_CONFIG)
        self.model_ar   = self._load_model("model_ar.pt", len(self.vocab_ar["stoi"]), MODEL_CONFIG)
        # ── Cache des modèles spécialisés (chargés à la demande) ─
        self._cat_cache = {}
        print("[NomGenService] Modèles principaux chargés ✓")

    def _load_vocab(self, filename):
        path = os.path.join(WEIGHTS_DIR, filename)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_model(self, filename, vocab_size, config):
        path = os.path.join(WEIGHTS_DIR, filename)
        model = NanoGPT(vocab_size=vocab_size, **config)
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
        return model

    def _get_category_model(self, lang, type_, secteur):
        """
        Retourne le modèle spécialisé si disponible (Sprint5),
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
                model = self._load_model(f"model_{tag}.pt",
                                         len(vocab["stoi"]), MODEL_CONFIG_CAT)
                self._cat_cache[tag] = (model, vocab)
                print(f"[NomGenService] Modèle spécialisé chargé : {tag}")
                return model, vocab
            except Exception as e:
                print(f"[NomGenService] ⚠️  Impossible de charger {tag} : {e}")

        self._cat_cache[tag] = None   # mémorise l'absence
        return None

    def generate(self, prompt, secteur, generation_type,
                 langue, n, temperature, top_k, seed):
        """
        Paramètres
        ----------
        generation_type : 'marque' ou 'societe'
        secteur         : 'luxe', 'tech', 'food', 'general', etc.
        """
        if seed is not None:
            torch.manual_seed(seed)
            random.seed(seed)

        lang     = langue
        score_fn = score_fr if lang == "fr" else score_ar
        type_    = generation_type.lower() if generation_type else "marque"
        sect     = secteur.lower() if secteur else "general"

        # ── 1. Essai modèle spécialisé (Sprint5) ────────────────
        cat_result = self._get_category_model(lang, type_, sect)

        if cat_result is not None:
            cat_model, cat_vocab = cat_result
            stoi = cat_vocab["stoi"]
            itos = {int(v): k for k, v in stoi.items()}
            names = self._run_simple(cat_model, stoi, itos, n, temperature, top_k)
            strategy = f"spécialisé:{lang}_{type_}_{sect}"

        else:
            # ── 2. Fallback modèle unifié avec token de contrôle ──
            vocab = self.vocab_fr if lang == "fr" else self.vocab_ar
            model = self.model_fr if lang == "fr" else self.model_ar
            stoi  = vocab["stoi"]
            itos  = {int(v): k for k, v in stoi.items()}

            ctrl_token = f"#{type_.upper()}#{sect.upper()}#"
            # Vérifier que tous les chars du token sont dans le vocab
            if all(c in stoi for c in ctrl_token):
                names    = self._run_conditioned(model, stoi, itos, ctrl_token,
                                                  n, temperature, top_k)
                strategy = f"unifié:{ctrl_token}"
            else:
                # ── 3. Fallback final : token NLU classique ────────
                tokens = parse_prompt(prompt) if prompt else [f"#{sect[0].upper()}"]
                names  = self._run_generation(model, stoi, itos, tokens[0],
                                               n, temperature, top_k)
                strategy = f"nlu:{tokens[0]}"

        print(f"[NomGenService] Stratégie : {strategy} → {len(names)} noms")

        return {
            "noms": [
                {"nom": nm, "score": score_fn(nm),
                 "langue": lang, "secteur": secteur,
                 "type": generation_type}
                for nm in names
            ],
            "tokens": [strategy],
        }

    @torch.no_grad()
    def _run_simple(self, model, stoi, itos, n, temperature, top_k):
        """Génération simple (modèle spécialisé sans token de contrôle)."""
        names  = []
        pad_id = stoi.get("\n", 0)
        block  = model.block_size

        for _ in range(n * 4):
            ctx   = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -1] = pad_id
            chars = []
            for _ in range(18):
                logits, _ = model(ctx)
                logits = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                ch = itos.get(ix, "")
                if ch in ("\n", "") : break
                chars.append(ch)
                new = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx = new
            nm = "".join(chars).strip()
            if 3 <= len(nm) <= 15 and nm not in names:
                names.append(nm)
            if len(names) >= n:
                break
        return names[:n]

    @torch.no_grad()
    def _run_conditioned(self, model, stoi, itos, ctrl_token,
                          n, temperature, top_k):
        """Génération avec token de contrôle (modèle unifié Sprint3_v2)."""
        names   = []
        block   = model.block_size
        eol_id  = stoi.get("\n", 0)
        hash_id = stoi.get("#", -1)

        for _ in range(n * 4):
            ctx_ids = [stoi[c] for c in ctrl_token if c in stoi]
            ctx = torch.zeros((1, block), dtype=torch.long)
            for j, cid in enumerate(ctx_ids[-block:]):
                ctx[0, -(len(ctx_ids)) + j] = cid
            chars = []
            for _ in range(20):
                logits, _ = model(ctx)
                logits = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                ch = itos.get(ix, "")
                if ch in ("\n", "#", "") : break
                chars.append(ch)
                new = torch.roll(ctx, -1, dims=1).clone()
                new[0, -1] = ix
                ctx = new
            nm = "".join(chars).split("#")[-1].strip()
            if 3 <= len(nm) <= 15 and nm not in names:
                names.append(nm)
            if len(names) >= n:
                break
        return names[:n]

    @torch.no_grad()
    def _run_generation(self, model, stoi, itos, ctrl_token,
                         n, temperature, top_k):
        """Génération legacy (Sprint3 original, token #L, #T...)."""
        names   = []
        ctrl_id = stoi.get(ctrl_token, 0)
        pad_id  = stoi.get(".", 0)
        block   = model.block_size

        for _ in range(n * 3):
            ctx = torch.zeros((1, block), dtype=torch.long)
            ctx[0, -2] = ctrl_id
            ctx[0, -1] = pad_id
            chars = []
            for _ in range(18):
                logits, _ = model(ctx)
                logits = logits[:, -1, :] / max(temperature, 1e-5)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float("-inf")
                ix = torch.multinomial(F.softmax(logits, -1), 1).item()
                if ix == pad_id: break
                ch = itos.get(ix, "")
                if ch.startswith("#"): break
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
