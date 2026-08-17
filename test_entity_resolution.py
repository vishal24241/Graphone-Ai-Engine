from src.entity_resolution.resolver import EntityResolver, normalize_name


resolver = EntityResolver()

tests = {
    "OpenAI": "OpenAI",
    "Open AI": "OpenAI",
    "OpenAI, Inc.": "OpenAI",
    "Anthropic Inc.": "Anthropic",
    "Google DeepMind": "Google DeepMind",
    "DeepMind": "Google DeepMind",
    "HuggingFace": "Hugging Face",
    "Hugging Face": "Hugging Face",
    "Weights & Biases": "Weights & Biases",
    "W&B": "Weights & Biases",
    "Completely Unknown Startup": None,
}


print("=" * 70)
print("GRAPHONE ENTITY RESOLUTION TEST")
print("=" * 70)

passed = 0

for raw, expected in tests.items():
    result = resolver.resolve(raw)

    print(f"{raw:35} -> {result}")

    assert result == expected, (
        f"Expected {expected!r}, got {result!r} for {raw!r}"
    )

    passed += 1


print()
print("Tests passed:", passed)
print("Canonical seed entities:", len(resolver.canonical_entities))

assert len(resolver.canonical_entities) >= 50

print()
print("=" * 70)
print("ENTITY RESOLUTION: PASS")
print("=" * 70)
