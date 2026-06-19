#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generer 10 noms arabes et francais
Mode A (nanoGPT) et Mode B (Ollama/OpenAI)
"""

import sys
import asyncio
from pathlib import Path
import io

# Fix encoding Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.nomgen_core import NomGenService
from app.services.ollama_service import call_ollama


async def main():
    print("="*80)
    print("GENERATION 10 NOMS — MODE A + MODE B")
    print("="*80)

    # ─── Mode A: nanoGPT ──────────────────────────────────────────────────────
    print("\n[MODE A] nanoGPT Generative Model")
    print("-"*80)

    service = NomGenService()

    # Français Mode A
    print("\n1. FRANCAIS - Mode A (nanoGPT):")
    result_fr_a = service.generate(
        prompt="Marque luxe innovative",
        secteur="LUXE",
        langue="fr",
        n=10,
        temperature=1.0,
        top_k=20,
        seed=42,
    )
    for i, nom_obj in enumerate(result_fr_a["noms"][:10], 1):
        print(f"  {i:2}. {nom_obj['nom']:20} (score: {nom_obj['score']:.1f})")

    # Arabe Mode A
    print("\n2. ARABE - Mode A (nanoGPT):")
    result_ar_a = service.generate(
        prompt="علامة تجارية",
        secteur="GENERAL",
        langue="ar",
        n=10,
        temperature=1.0,
        top_k=20,
        seed=42,
    )
    for i, nom_obj in enumerate(result_ar_a["noms"][:10], 1):
        print(f"  {i:2}. {nom_obj['nom']:20} (score: {nom_obj['score']:.1f})")

    # ─── Mode B: Ollama/OpenAI ────────────────────────────────────────────────
    print("\n[MODE B] LLM (Ollama/OpenAI)")
    print("-"*80)

    # Français Mode B
    print("\n3. FRANCAIS - Mode B (Ollama):")
    try:
        system_fr = (
            "Tu es expert en branding. Genere 10 noms de marques innovants. "
            "Format: JSON [\"nom1\", \"nom2\", ...] seulement."
        )
        user_fr = "Secteur: Luxe. Style: moderne, elegant. Genere 10 noms uniques."
        noms_fr_b = await call_ollama("mistral", user_fr, system_fr)
        for i, nom in enumerate(noms_fr_b[:10], 1):
            print(f"  {i:2}. {nom}")
    except Exception as e:
        print(f"  [ERREUR] {e}")

    # Arabe Mode B
    print("\n4. ARABE - Mode B (Ollama):")
    try:
        system_ar = (
            "أنت خبير في تسمية العلامات التجارية. وليد 10 أسماء فريدة. "
            "الصيغة: JSON فقط"
        )
        user_ar = "وليد 10 أسماء للعلامات التجارية العربية"
        noms_ar_b = await call_ollama("mistral", user_ar, system_ar)
        for i, nom in enumerate(noms_ar_b[:10], 1):
            print(f"  {i:2}. {nom}")
    except Exception as e:
        print(f"  [ERREUR] {e}")

    # ─── Résumé ───────────────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("RESUME")
    print("="*80)
    print(f"Mode A - Francais: {len(result_fr_a['noms'])} noms")
    print(f"Mode A - Arabe:    {len(result_ar_a['noms'])} noms")
    print(f"\nMode B - Francais: {len(noms_fr_b) if 'noms_fr_b' in locals() else 0} noms")
    print(f"Mode B - Arabe:    {len(noms_ar_b) if 'noms_ar_b' in locals() else 0} noms")
    print("\nNote: Mode B necessite Ollama local (localhost:11434)")
    print("      ou OPENAI_API_KEY configuree pour fallback")


if __name__ == "__main__":
    print("\nDemarrage...")
    print(f"Workspace: {Path.cwd()}\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Interrupted]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
