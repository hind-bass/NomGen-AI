"""
Architecture nanoGPT
Inspirée de Karpathy 'Let's build GPT' (2022).
Optimisée pour la génération conditionnelle de noms de marques.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class CausalSelfAttention(nn.Module):
    def __init__(self, n_embed, n_head, block_size, dropout=0.1):
        super().__init__()
        assert n_embed % n_head == 0
        self.n_head  = n_head
        self.head_dim = n_embed // n_head
        self.c_attn  = nn.Linear(n_embed, 3 * n_embed, bias=False)
        self.c_proj  = nn.Linear(n_embed, n_embed, bias=False)
        self.ad = nn.Dropout(dropout)
        self.rd = nn.Dropout(dropout)
        self.register_buffer(
            "mask",
            torch.tril(torch.ones(block_size, block_size))
            .view(1, 1, block_size, block_size),
        )

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(self.n_head * self.head_dim, dim=2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float("-inf"))
        att = self.ad(F.softmax(att, dim=-1))
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.rd(self.c_proj(y))


class FeedForward(nn.Module):
    def __init__(self, n_embed, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embed, 4 * n_embed),
            nn.GELU(),
            nn.Linear(4 * n_embed, n_embed),
            nn.Dropout(dropout),
        )
    def forward(self, x): 
        return self.net(x)


class TransformerBlock(nn.Module):
    def __init__(self, n_embed, n_head, block_size, dropout=0.1):
        super().__init__()
        self.ln1  = nn.LayerNorm(n_embed)
        self.attn = CausalSelfAttention(n_embed, n_head, block_size, dropout)
        self.ln2  = nn.LayerNorm(n_embed)
        self.ff   = FeedForward(n_embed, dropout)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


class NanoGPT(nn.Module):
    """
    Modèle GPT miniature pour la génération de noms de marques.
    Utilisé dans TOUS les sprints et dans le backend FastAPI.
    """
    def __init__(self, vocab_size, n_embed=64, n_head=4,
                 n_layer=4, block_size=24, dropout=0.1):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, n_embed)
        self.pos_emb   = nn.Embedding(block_size, n_embed)
        self.drop      = nn.Dropout(dropout)
        self.blocks    = nn.Sequential(
            *[TransformerBlock(n_embed, n_head, block_size, dropout)
              for _ in range(n_layer)]
        )
        self.ln_f  = nn.LayerNorm(n_embed)
        self.head  = nn.Linear(n_embed, vocab_size, bias=False)
        self.block_size = block_size
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, 0.0, 0.02)
            if hasattr(m, "bias") and m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos    = torch.arange(T, dtype=torch.long, device=idx.device)
        x      = self.drop(self.token_emb(idx) + self.pos_emb(pos))
        x      = self.blocks(x)
        logits = self.head(self.ln_f(x))
        
        loss = None
        if targets is not None:
            # Redimensionnement des tenseurs pour la CrossEntropyLoss (B*T, C)
            B, T, C = logits.shape
            logits_flat = logits.view(B * T, C)
            targets_flat = targets.view(B * T)
            loss = F.cross_entropy(logits_flat, targets_flat)
            
        return logits, loss

    def count_params(self):
        return sum(p.numel() for p in self.parameters())

    @torch.no_grad()
    def generate(self, context, max_new_tokens=15, temperature=1.0,
                 top_k=20, stop_token=0):
        """Génère des tokens un par un de façon autorégressive."""
        for _ in range(max_new_tokens):
            # On restreint le contexte à la taille maximale autorisée (block_size)
            idx_cond = context[:, -self.block_size:]
            
            # Appel au forward révisé (on ignore la loss car targets=None ici)
            logits, _ = self(idx_cond)
            
            # Extraction des prédictions de l'ultime étape temporelle
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            
            if top_k:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")
                
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            
            if idx_next.item() == stop_token:
                break
                
            context = torch.cat([context, idx_next], dim=1)
        return context