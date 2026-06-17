"""
ollama_service.py — Mode B simplifié
Appel direct Ollama via httpx (15 lignes) ou fallback OpenAI
Support multilingue: Français, Arabe, Anglais
"""
import httpx
import json
import os


# Prompts système par langue
SYSTEM_PROMPTS = {
    "fr": "Tu es expert en branding et naming. Génère {n} noms uniques. Format JSON seulement: [\"nom1\", \"nom2\", ...]",
    "ar": "أنت خبير في تسمية العلامات التجارية. وليد {n} اسماً فريداً. الصيغة: JSON فقط [\"اسم1\", \"اسم2\"]",
    "en": "You are a branding expert. Generate {n} unique names. JSON format only: [\"name1\", \"name2\", ...]",
}

# Modèles recommandés par langue
RECOMMENDED_MODELS = {
    "fr": ["mistral", "dolphin-mixtral", "neural-chat"],
    "ar": ["allam", "fanar", "acegpt"],  # Modèles arabes spécialisés
    "en": ["mistral", "neural-chat"],
}


async def call_ollama(model: str, prompt: str, langue: str = "fr") -> list[str]:
    """Appel direct Ollama localhost:11434. Retourne liste de noms JSON."""
    try:
        system_prompt = SYSTEM_PROMPTS.get(langue, SYSTEM_PROMPTS["fr"])

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": f"{system_prompt}\n\nUser query: {prompt}",
                    "stream": False,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            text = resp.json()["response"]

            # Parser JSON de la réponse
            try:
                import re
                match = re.search(r"\[.*?\]", text, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except:
                pass

            # Fallback: split par lignes
            return [line.strip() for line in text.split("\n") if line.strip()][:8]
    except Exception as e:
        print(f"[Ollama Error] {e}. Fallback OpenAI...")
        return await call_openai(model, prompt, langue)


async def call_openai(model: str, prompt: str, langue: str = "fr") -> list[str]:
    """Fallback OpenAI si Ollama indisponible."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("Ollama offline et OPENAI_API_KEY non defini")

    system_prompt = SYSTEM_PROMPTS.get(langue, SYSTEM_PROMPTS["fr"])

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model or "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]

        try:
            import re
            match = re.search(r"\[.*?\]", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass

        return [line.strip() for line in text.split("\n") if line.strip()][:8]


def get_recommended_models(langue: str = "fr") -> list[str]:
    """Retourne les modèles recommandés pour une langue."""
    return RECOMMENDED_MODELS.get(langue, RECOMMENDED_MODELS["fr"])

