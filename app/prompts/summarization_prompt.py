# app/prompts/summarization_prompt.py

# Optimized for M2M communication: concise, direct, and token-efficient.
SUMMARIZATION_PROMPT = """
Integrate the 'PREVIOUS SUMMARY' with the 'NEW MESSAGES' into a single, updated, and concise summary. Preserve all key information and decisions. The final output must be a single coherent paragraph in Thai.

---
{conversation_history}
---
Updated Summary (Thai):
"""