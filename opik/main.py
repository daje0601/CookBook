from opik.evaluation.metrics import LevenshteinRatio
from opik_optimizer import MetaPromptOptimizer, ChatPrompt
from opik_optimizer.datasets import tiny_test


import os 
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPIK_API_KEY"] = ""
os.environ["OPIK_WORKSPACE"] = ""
# You can use a demo dataset for testing, or your own dataset
dataset = tiny_test()
print(f"Using dataset: {dataset.name}, with {len(dataset.get_items())} items.")

# This example uses Levenshtein distance to measure output quality
def levenshtein_ratio(dataset_item, llm_output):
    metric = LevenshteinRatio()
    return metric.score(reference=dataset_item['label'], output=llm_output)

prompt = ChatPrompt(
  project_name="Prompt Optimization Quickstart",
  messages=[
    {"role": "system", "content": "You are an expert assistant. Your task is to answer questions accurately and concisely. Consider the context carefully before responding."},
    {"role": "user", "content": "{text}"}
  ]
)
print("Prompt defined.")

optimizer = MetaPromptOptimizer(
    model="gpt-4.1",
)
print(f"Optimizer configured: {type(optimizer).__name__}")

print("Starting optimization...")
result = optimizer.optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    metric=levenshtein_ratio,
)
print("Optimization finished.")

print("Optimization Results:")
result.display()
