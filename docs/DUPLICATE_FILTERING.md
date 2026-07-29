# Duplicate filtering

Duplicate prevention runs locally before provider grouping. It compares timeline intersection-over-union, normalized Arabic text, token overlap, repeated wording, hooks, and conclusions. Arabic comparison removes diacritics and punctuation, normalizes Alef variants and Ya/Alef Maqsura, and collapses whitespace while preserving the original display text.

Strict diversity rejects material timeline or text duplicates. Balanced and similar-allowed modes retain more alternatives. When candidates overlap materially, HookCut keeps the stronger evidence-based candidate and records the rejected candidate's similarity group and reason. Semantic provider grouping may supplement this evidence, but no local embedding model is installed in Phase 4.
