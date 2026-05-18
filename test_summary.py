from backend.services.summary_service import summarize_article

summary = summarize_article(
    "OpenAI releases new GPT model",
    "OpenAI announced a new model with better reasoning, coding, and multimodal abilities. The model improves performance across benchmarks and introduces faster inference."
)

print(summary)