import re
import unicodedata
from typing import Dict, List, Optional


# ============================================================
# GRAPHONE DETERMINISTIC ENTITY RESOLUTION
# ============================================================

CANONICAL_ENTITIES = [
    "OpenAI",
    "Anthropic",
    "Google",
    "Google DeepMind",
    "Microsoft",
    "Meta",
    "Amazon",
    "NVIDIA",
    "Apple",
    "IBM",
    "Oracle",
    "Cohere",
    "Mistral AI",
    "Hugging Face",
    "DeepSeek",
    "Perplexity",
    "xAI",
    "Databricks",
    "Scale AI",
    "Stability AI",
    "Runway",
    "Midjourney",
    "Character AI",
    "Jasper",
    "DataRobot",
    "Weights & Biases",
    "Replicate",
    "Together AI",
    "Groq",
    "Adept",
    "Inflection AI",
    "ElevenLabs",
    "Synthesia",
    "Glean",
    "Harvey",
    "Cursor",
    "Anysphere",
    "LangChain",
    "LlamaIndex",
    "MosaicML",
    "H2O.ai",
    "AI21 Labs",
    "Magic AI",
    "Vercel",
    "Pinecone",
    "Aleph Alpha",
    "Mistral",
    "VentureBeat AI",
    "Hugging Face Spaces",
    "Weights & Biases AI",
    "AssemblyAI",
    "Fireworks AI",
    "Modal",
    "Together Computer",
    "Baseten",
    "OctoAI",
]



# Explicit aliases only.
# No fuzzy guessing.
ALIASES = {
    # OpenAI
    "open ai": "OpenAI",
    "openai inc": "OpenAI",
    "openai inc.": "OpenAI",
    "openai corporation": "OpenAI",
    "openai": "OpenAI",

    # Anthropic
    "anthropic inc": "Anthropic",
    "anthropic inc.": "Anthropic",
    "anthropic": "Anthropic",
    "anthropics": "Anthropic",

    # Google
    "google llc": "Google",
    "google inc": "Google",
    "google inc.": "Google",
    "google": "Google",

    # DeepMind
    "deepmind": "Google DeepMind",
    "google deepmind": "Google DeepMind",
    "google-deepmind": "Google DeepMind",
    "google_deepmind": "Google DeepMind",

    # Microsoft
    "microsoft corporation": "Microsoft",
    "microsoft corp": "Microsoft",
    "microsoft corp.": "Microsoft",
    "microsoft": "Microsoft",

    # Meta
    "meta platforms": "Meta",
    "meta platforms inc": "Meta",
    "meta platforms inc.": "Meta",
    "facebook ai": "Meta",
    "meta": "Meta",

    # Amazon
    "amazon web services": "Amazon",
    "amazon aws": "Amazon",
    "amazon": "Amazon",

    # NVIDIA
    "nvidia corporation": "NVIDIA",
    "nvidia corp": "NVIDIA",
    "nvidia corp.": "NVIDIA",
    "nvidia": "NVIDIA",

    # Hugging Face
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "hugging-face": "Hugging Face",
    "hugging_face": "Hugging Face",

    # DeepSeek
    "deepseek": "DeepSeek",
    "deepseek ai": "DeepSeek",
    "deepseek-ai": "DeepSeek",
    "deepseek_ai": "DeepSeek",

    # Mistral
    "mistral": "Mistral AI",
    "mistral ai": "Mistral AI",
    "mistral-ai": "Mistral AI",

    # Perplexity
    "perplexity": "Perplexity",
    "perplexity ai": "Perplexity",

    # Weights & Biases
    "weights and biases": "Weights & Biases",
    "weights biases": "Weights & Biases",
    "weights & biases": "Weights & Biases",
    "wandb": "Weights & Biases",
    "w&b": "Weights & Biases",

    # Cohere
    "cohere ai": "Cohere",
    "cohere": "Cohere",

    # Stability
    "stability ai": "Stability AI",
    "stability-ai": "Stability AI",

    # Together
    "together ai": "Together AI",
    "together-ai": "Together AI",

    # Scale
    "scale ai": "Scale AI",
    "scale-ai": "Scale AI",

    # ElevenLabs
    "eleven labs": "ElevenLabs",
    "elevenlabs": "ElevenLabs",

    # H2O
    "h2o ai": "H2O.ai",
    "h2o.ai": "H2O.ai",

    # AI21
    "ai21": "AI21 Labs",
    "ai21 labs": "AI21 Labs",
}


def normalize_name(name: str) -> str:
    """
    Deterministic normalization.

    Examples:
        Open AI       -> open ai
        OpenAI, Inc.  -> openai
        Hugging-Face  -> hugging face
    """

    if not name:
        return ""

    value = str(name).strip()

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = value.encode(
        "ascii",
        "ignore"
    ).decode()

    value = value.lower()

    # Remove common legal suffixes.
    value = re.sub(
        r"\b(incorporated|inc|corp|corporation|llc|ltd|limited)\b\.?",
        " ",
        value,
    )

    # Normalize separators.
    value = value.replace("&", " and ")

    value = re.sub(
        r"[-_/]+",
        " ",
        value,
    )

    # Remove punctuation.
    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    # Collapse whitespace.
    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


class EntityResolver:
    """
    Deterministic startup/product entity resolver.

    Resolution order:
        1. Exact normalized canonical name
        2. Explicit verified alias
        3. No match

    No fuzzy matching is performed.
    """

    def __init__(
        self,
        canonical_entities: Optional[List[str]] = None,
        aliases: Optional[Dict[str, str]] = None,
    ):
        self.canonical_entities = list(
            dict.fromkeys(
                canonical_entities
                or CANONICAL_ENTITIES
            )
        )

        self.aliases = dict(
            aliases
            or ALIASES
        )

        self.normalized_canonical = {}

        for canonical in self.canonical_entities:
            normalized = normalize_name(canonical)

            if normalized:
                self.normalized_canonical[
                    normalized
                ] = canonical

        self.normalized_aliases = {}

        for alias, canonical in self.aliases.items():
            normalized_alias = normalize_name(alias)

            if normalized_alias:
                self.normalized_aliases[
                    normalized_alias
                ] = canonical

    def resolve(
        self,
        raw_name: str,
    ) -> Optional[str]:

        if not raw_name:
            return None

        normalized = normalize_name(raw_name)

        if not normalized:
            return None

        # ----------------------------------------------------
        # 1. Exact canonical match
        # ----------------------------------------------------
        if normalized in self.normalized_canonical:
            return self.normalized_canonical[
                normalized
            ]

        # ----------------------------------------------------
        # 2. Explicit alias match
        # ----------------------------------------------------
        if normalized in self.normalized_aliases:
            canonical = self.normalized_aliases[
                normalized
            ]

            if canonical in self.canonical_entities:
                return canonical

        # ----------------------------------------------------
        # 3. No deterministic match
        # ----------------------------------------------------
        return None

    def resolve_record(
        self,
        raw_name: str,
        entity_type: str,
        source_url: str = "",
    ) -> Dict:

        canonical = self.resolve(raw_name)

        return {
            "raw_name": raw_name,
            "canonical_name": canonical,
            "entity_type": entity_type,
            "source_url": source_url,
            "matched": canonical is not None,
        }


def resolve_entities(
    names: List[str],
    entity_type: str = "STARTUP",
) -> List[Dict]:

    resolver = EntityResolver()

    return [
        resolver.resolve_record(
            raw_name=name,
            entity_type=entity_type,
        )
        for name in names
    ]
