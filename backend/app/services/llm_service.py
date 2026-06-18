"""
Modèles FRANÇAIS  : gpt-4o (OpenAI), ollama (local), deepseek, mistral
Modèles ARABES    : allam (SDAIA), fanar (Qatar), acegpt, jais (MBZUAI)
Fallback          : nanoGPT local si aucun LLM disponible

Architecture :
  - BaseLLMProvider  : classe abstraite commune
  - Un Provider par LLM, tous retournent List[str]
  - LLMRouter        : dispatche vers le bon provider
"""
import os
import json
import re
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional

#  Prompt engineering commun 

SYSTEM_PROMPT_FR = """Tu es un expert en branding et naming de marques françaises.
Génère des noms de {type_nom} dans le secteur {secteur}.
Règles strictes :
- Noms courts : 3 à 12 caractères
- Mémorables, originaux, prononçables
- Style : {style}
- Évite les noms déjà déposés célèbres
- Réponds UNIQUEMENT avec une liste JSON de chaînes, rien d'autre
- Format : ["nom1", "nom2", "nom3", ...]
"""

SYSTEM_PROMPT_AR = """أنت خبير في تسمية العلامات التجارية العربية.
قم بتوليد أسماء {type_nom} في قطاع {secteur}.
القواعد الصارمة:
- أسماء قصيرة: 3 إلى 12 حرفاً
- سهلة النطق، أصلية، لافتة للانتباه
- الأسلوب: {style}
- تجنب الأسماء المشهورة المسجلة
- أجب فقط بقائمة JSON من السلاسل، لا شيء آخر
- الصيغة: ["اسم1", "اسم2", "اسم3", ...]
"""

USER_PROMPT_TEMPLATE = """
Contexte utilisateur : {prompt}
Génère exactement {n} noms uniques.
Langue : {langue}
"""

USER_PROMPT_AR_TEMPLATE = """
وصف المستخدم: {prompt}
قم بتوليد {n} أسماء فريدة تماماً.
اللغة: {langue}
"""


#  Classe de base 

class BaseLLMProvider(ABC):
    """Interface commune à tous les providers LLM."""

    def __init__(self, model_id: str, langue: str):
        self.model_id = model_id
        self.langue = langue

    def _build_system_prompt(self, type_nom: str, secteur: str, style: str) -> str:
        if self.langue == "ar":
            return SYSTEM_PROMPT_AR.format(
                type_nom=type_nom, secteur=secteur, style=style
            )
        return SYSTEM_PROMPT_FR.format(
            type_nom=type_nom, secteur=secteur, style=style
        )

    def _build_user_prompt(self, prompt: str, n: int) -> str:
        if self.langue == "ar":
            return USER_PROMPT_AR_TEMPLATE.format(
                prompt=prompt, n=n, langue="العربية"
            )
        return USER_PROMPT_TEMPLATE.format(
            prompt=prompt, n=n, langue="Français"
        )

    def _parse_response(self, text: str) -> list[str]:
        """Extrait une liste de noms depuis la réponse JSON du LLM."""
        # Tenter de parser le JSON directement
        text = text.strip()
        # Chercher un tableau JSON dans la réponse
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            try:
                names = json.loads(match.group())
                if isinstance(names, list):
                    return [str(n).strip() for n in names if n and len(str(n).strip()) >= 2]
            except json.JSONDecodeError:
                pass

        # Fallback : extraire ligne par ligne
        lines = text.split('\n')
        names = []
        for line in lines:
            line = re.sub(r'^[\d\-\*\.\s"\']+', '', line).strip().strip('"').strip("'")
            if 2 <= len(line) <= 20:
                names.append(line)
        return names

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        n: int,
        type_nom: str,
        secteur: str,
        style: str,
        temperature: float,
    ) -> list[str]:
        pass


#  Provider OpenAI GPT

class OpenAIProvider(BaseLLMProvider):
    """GPT-4o / GPT-4 / GPT-3.5 via OpenAI API."""

    def __init__(self, model_id: str = "gpt-4o-mini", langue: str = "fr"):
        super().__init__(model_id, langue)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY manquant dans les variables d'environnement.")

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_response(text)


#  Provider Mistral AI 

class MistralProvider(BaseLLMProvider):
    """Mistral Large / Mistral-7B via api.mistral.ai."""

    def __init__(self, model_id: str = "mistral-small-latest", langue: str = "fr"):
        super().__init__(model_id, langue)
        self.api_key = os.getenv("MISTRAL_API_KEY", "")
        self.base_url = "https://api.mistral.ai/v1/chat/completions"

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY manquant dans les variables d'environnement.")

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_response(text)


#  Provider DeepSeek

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek-V3 / DeepSeek-Chat — compatible API OpenAI."""

    def __init__(self, model_id: str = "deepseek-chat", langue: str = "fr"):
        super().__init__(model_id, langue)
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY manquant dans les variables d'environnement.")

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_response(text)


#  Provider Ollama (local) 

class OllamaProvider(BaseLLMProvider):
    """Ollama local — llama3, mistral, gemma2, qwen2 ..."""

    def __init__(self, model_id: str = "mistral", langue: str = "fr"):
        super().__init__(model_id, langue)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "options": {"temperature": temperature},
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
            except httpx.ConnectError:
                raise ConnectionError(
                    "Ollama n'est pas démarré. Ouvrez l'application Ollama ou lancez : ollama serve"
                ) from None
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(
                        f"Modèle '{self.model_id}' introuvable dans Ollama. "
                        f"Exécutez : ollama pull {self.model_id}"
                    ) from e
                raise
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            return self._parse_response(text)


#  Provider Allam (SDAIA / STC — Modèle arabe saoudien) 

class AllamProvider(BaseLLMProvider):
    """
    Allam — Modèle LLM arabe de SDAIA (Saudi Data & AI Authority).
    Documentation : https://sdaia.gov.sa / via IBM watsonx.ai
    Note : actuellement en bêta, API via watsonx.ai d'IBM.
    """

    def __init__(self, model_id: str = "allam-1-13b-instruct", langue: str = "ar"):
        super().__init__(model_id, langue)
        self.api_key   = os.getenv("WATSONX_API_KEY", "")
        self.project_id = os.getenv("WATSONX_PROJECT_ID", "")
        self.base_url  = os.getenv(
            "WATSONX_BASE_URL",
            "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation"
        )

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key or not self.project_id:
            raise ValueError(
                "WATSONX_API_KEY et WATSONX_PROJECT_ID requis pour Allam."
            )

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model_id": self.model_id,
            "input": full_prompt,
            "parameters": {
                "decoding_method": "sample",
                "temperature": temperature,
                "max_new_tokens": 500,
                "stop_sequences": ["]"],
            },
            "project_id": self.project_id,
        }

        async with httpx.AsyncClient(timeout=45) as client:
            # Obtenir le token IBM IAM
            iam_resp = await client.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key,
                },
            )
            iam_resp.raise_for_status()
            iam_token = iam_resp.json()["access_token"]

            resp = await client.post(
                f"{self.base_url}?version=2023-05-29",
                headers={
                    "Authorization": f"Bearer {iam_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["results"][0]["generated_text"]
            return self._parse_response(text)


#  Provider Fanar (Qatar Computing Research Institute) 

class FanarProvider(BaseLLMProvider):
    """
    Fanar — LLM arabe du Qatar Computing Research Institute (QCRI).
    Spécialisé arabe du Golfe, dialectes inclus.
    API : https://fanar.qa (en accès restreint / bêta publique)
    """

    def __init__(self, model_id: str = "fanar-v1", langue: str = "ar"):
        super().__init__(model_id, langue)
        self.api_key  = os.getenv("FANAR_API_KEY", "")
        self.base_url = os.getenv("FANAR_BASE_URL", "https://api.fanar.qa/v1")

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError("FANAR_API_KEY manquant. Inscrivez-vous sur https://fanar.qa")

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 500,
        }

        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_response(text)


#  Provider AceGPT (Arabic LLM — HKUST) 

class AceGPTProvider(BaseLLMProvider):
    """
    AceGPT — Modèle arabe de HKUST, via HuggingFace Inference API.
    Papier : AceGPT: Localizing Large Language Models in Arabic
    HuggingFace : FreedomIntelligence/AceGPT-13B-chat
    """

    def __init__(
        self,
        model_id: str = "FreedomIntelligence/AceGPT-13B-chat",
        langue: str = "ar"
    ):
        super().__init__(model_id, langue)
        self.api_key  = os.getenv("HUGGINGFACE_API_KEY", "")
        self.base_url = f"https://api-inference.huggingface.co/models/{model_id}"

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError(
                "HUGGINGFACE_API_KEY requis pour AceGPT. "
                "Obtenez-le sur https://huggingface.co/settings/tokens"
            )

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        # HuggingFace Inference API format
        full_input = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"

        payload = {
            "inputs": full_input,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": 500,
                "return_full_text": False,
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
            else:
                text = str(data)
            return self._parse_response(text)


#  Provider Jais (MBZUAI — Abu Dhabi) 

class JaisProvider(BaseLLMProvider):
    """
    Jais — LLM arabe de MBZUAI (Mohamed bin Zayed University of AI).
    Un des meilleurs modèles arabes open-source.
    HuggingFace : core42/jais-13b-chat
    """

    def __init__(
        self,
        model_id: str = "core42/jais-13b-chat",
        langue: str = "ar"
    ):
        super().__init__(model_id, langue)
        self.api_key  = os.getenv("HUGGINGFACE_API_KEY", "")
        self.base_url = f"https://api-inference.huggingface.co/models/{model_id}"

    async def generate(self, prompt, n, type_nom, secteur, style, temperature):
        if not self.api_key:
            raise ValueError(
                "HUGGINGFACE_API_KEY requis pour Jais. "
                "Obtenez-le sur https://huggingface.co/settings/tokens"
            )

        system_prompt = self._build_system_prompt(type_nom, secteur, style)
        user_prompt   = self._build_user_prompt(prompt, n)

        # Jais utilise le format ###Instruction: ###Response:
        full_input = (
            f"###System: {system_prompt}\n"
            f"###Instruction: {user_prompt}\n"
            f"###Response:"
        )

        payload = {
            "inputs": full_input,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": 500,
                "return_full_text": False,
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
            else:
                text = str(data)
            return self._parse_response(text)


# ─── Vérification Ollama (local) ───────────────────────────────────────────────

def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def check_ollama_running() -> tuple[bool, str]:
    """Vérifie si Ollama répond et retourne un message d'état."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{_ollama_base_url()}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            if not models:
                return False, (
                    "Ollama est démarré mais aucun modèle n'est installé. "
                    "Exécutez : ollama pull mistral"
                )
            return True, "OK"
    except httpx.ConnectError:
        return False, (
            "Ollama n'est pas démarré. Lancez l'application Ollama ou exécutez : ollama serve"
        )
    except Exception as e:
        return False, f"Ollama inaccessible : {e}"


def check_ollama_model(model_id: str) -> tuple[bool, str]:
    """Vérifie qu'un modèle Ollama précis est installé."""
    running, reason = check_ollama_running()
    if not running:
        return False, reason
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{_ollama_base_url()}/api/tags")
            resp.raise_for_status()
            installed = {m.get("name", "").split(":")[0] for m in resp.json().get("models", [])}
            if model_id not in installed and not any(
                name == model_id or name.startswith(f"{model_id}.") or name.startswith(f"{model_id}:")
                for name in installed
            ):
                return False, (
                    f"Modèle '{model_id}' non installé. Exécutez : ollama pull {model_id}"
                )
            return True, "OK"
    except Exception as e:
        return False, f"Erreur Ollama : {e}"


# ─── Registre des modèles disponibles ────────────────────────────────────────

AVAILABLE_MODELS = {
    # ── Français ──────────────────────────────────────────────────────────
    "gpt-4o-mini": {
        "provider": "openai",
        "nom_affiche": "GPT-4o Mini (OpenAI)",
        "langues": ["fr"],
        "description": "Rapide et économique, excellent en français",
        "env_required": ["OPENAI_API_KEY"],
    },
    "gpt-4o": {
        "provider": "openai",
        "nom_affiche": "GPT-4o (OpenAI)",
        "langues": ["fr"],
        "description": "Le plus puissant d'OpenAI pour le branding",
        "env_required": ["OPENAI_API_KEY"],
        "model_id": "gpt-4o",
    },
    "mistral-small": {
        "provider": "mistral",
        "nom_affiche": "Mistral Small (Mistral AI)",
        "langues": ["fr"],
        "description": "Modèle français, très bon en naming FR",
        "env_required": ["MISTRAL_API_KEY"],
        "model_id": "mistral-small-latest",
    },
    "mistral-large": {
        "provider": "mistral",
        "nom_affiche": "Mistral Large (Mistral AI)",
        "langues": ["fr"],
        "description": "Meilleur modèle Mistral, créativité maximale",
        "env_required": ["MISTRAL_API_KEY"],
        "model_id": "mistral-large-latest",
    },
    "deepseek-chat": {
        "provider": "deepseek",
        "nom_affiche": "DeepSeek-V3",
        "langues": ["fr"],
        "description": "Excellent rapport qualité/prix, multilingue",
        "env_required": ["DEEPSEEK_API_KEY"],
    },
    "ollama-mistral": {
        "provider": "ollama",
        "nom_affiche": "Mistral 7B (Local Ollama)",
        "langues": ["fr"],
        "description": "100% local, aucune clé API requise",
        "env_required": [],
        "model_id": "mistral",
    },
    "ollama-llama3": {
        "provider": "ollama",
        "nom_affiche": "Llama 3 8B (Local Ollama)",
        "langues": ["fr"],
        "description": "Meta Llama 3 en local, gratuit",
        "env_required": [],
        "model_id": "llama3.1",
    },
    # ── Arabe ─────────────────────────────────────────────────────────────
    "allam": {
        "provider": "allam",
        "nom_affiche": "Allam (SDAIA — السعودية)",
        "langues": ["ar"],
        "description": "Modèle arabe saoudien officiel, arabe du Golfe",
        "env_required": ["WATSONX_API_KEY", "WATSONX_PROJECT_ID"],
        "model_id": "allam-1-13b-instruct",
    },
    "fanar": {
        "provider": "fanar",
        "nom_affiche": "Fanar (QCRI — قطر)",
        "langues": ["ar"],
        "description": "LLM arabe du Qatar, dialectes du Golfe",
        "env_required": ["FANAR_API_KEY"],
    },
    "acegpt": {
        "provider": "acegpt",
        "nom_affiche": "AceGPT (HKUST)",
        "langues": ["ar"],
        "description": "Arabe moderne standard, très bon en naming",
        "env_required": ["HUGGINGFACE_API_KEY"],
    },
    "jais": {
        "provider": "jais",
        "nom_affiche": "Jais 13B (MBZUAI — الإمارات)",
        "langues": ["ar"],
        "description": "LLM open-source d'Abu Dhabi, arabe haute qualité",
        "env_required": ["HUGGINGFACE_API_KEY"],
    },
    "ollama-qwen2-ar": {
        "provider": "ollama",
        "nom_affiche": "Qwen2 7B Arabic (Local Ollama)",
        "langues": ["ar"],
        "description": "Alibaba Qwen2 en local, bon support arabe",
        "env_required": [],
        "model_id": "qwen2",
    },
}


# ─── LLMRouter — dispatche vers le bon provider ──────────────────────────────

class LLMRouter:
    """
    Instancie et appelle le bon provider selon le model_key choisi.
    Utilisation :
        router = LLMRouter()
        noms = await router.generate(model_key="mistral-small", ...)
    """

    def _get_provider(self, model_key: str, langue: str) -> BaseLLMProvider:
        config = AVAILABLE_MODELS.get(model_key)
        if not config:
            raise ValueError(f"Modèle inconnu : '{model_key}'. Disponibles : {list(AVAILABLE_MODELS.keys())}")

        provider_name = config["provider"]
        model_id      = config.get("model_id", model_key)

        providers = {
            "openai":   lambda: OpenAIProvider(model_id=model_id, langue=langue),
            "mistral":  lambda: MistralProvider(model_id=model_id, langue=langue),
            "deepseek": lambda: DeepSeekProvider(model_id=model_id, langue=langue),
            "ollama":   lambda: OllamaProvider(model_id=model_id, langue=langue),
            "allam":    lambda: AllamProvider(model_id=model_id, langue=langue),
            "fanar":    lambda: FanarProvider(model_id=model_id, langue=langue),
            "acegpt":   lambda: AceGPTProvider(model_id=model_id, langue=langue),
            "jais":     lambda: JaisProvider(model_id=model_id, langue=langue),
        }

        factory = providers.get(provider_name)
        if not factory:
            raise ValueError(f"Provider inconnu : {provider_name}")
        return factory()

    async def generate(
        self,
        model_key: str,
        prompt: str,
        n: int,
        langue: str,
        type_nom: str,
        secteur: str,
        style: str,
        temperature: float = 0.9,
    ) -> list[str]:
        """
        Génère des noms via le LLM choisi.
        Retourne une liste de strings (noms de marques/sociétés).
        """
        provider = self._get_provider(model_key, langue)
        names = await provider.generate(
            prompt=prompt,
            n=n,
            type_nom=type_nom,
            secteur=secteur,
            style=style,
            temperature=temperature,
        )
        # Nettoyage final
        cleaned = []
        for name in names:
            name = name.strip().strip('"').strip("'")
            if 2 <= len(name) <= 25:
                cleaned.append(name)
        return cleaned[:n]

    def _is_model_available(self, key: str, cfg: dict) -> tuple[bool, str]:
        """Vérifie la disponibilité réelle d'un modèle (clés API ou Ollama)."""
        missing = [env for env in cfg["env_required"] if not os.getenv(env)]
        if missing:
            return False, f"Variables d'env manquantes : {', '.join(missing)}"

        if cfg["provider"] == "ollama":
            model_id = cfg.get("model_id", key)
            return check_ollama_model(model_id)

        return True, "OK"

    def get_available_models(self, langue: Optional[str] = None) -> list[dict]:
        """Retourne la liste des modèles, filtrée par langue si fournie."""
        result = []
        for key, cfg in AVAILABLE_MODELS.items():
            if langue and langue not in cfg["langues"]:
                continue
            available, reason = self._is_model_available(key, cfg)
            result.append({
                "key": key,
                "nom_affiche": cfg["nom_affiche"],
                "langues": cfg["langues"],
                "description": cfg["description"],
                "env_required": cfg["env_required"],
                "available": available,
                "unavailable_reason": None if available else reason,
            })
        return result

    def check_model_available(self, model_key: str) -> tuple[bool, str]:
        """Vérifie si un modèle est utilisable (clés API présentes ou Ollama actif)."""
        cfg = AVAILABLE_MODELS.get(model_key)
        if not cfg:
            return False, f"Modèle '{model_key}' inconnu."
        return self._is_model_available(model_key, cfg)


# Singleton global
llm_router = LLMRouter()