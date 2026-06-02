from content_automata.pipeline import ContentPipeline

pipeline = ContentPipeline.from_config("examples/config.yaml")
result = pipeline.run(topic="AI trends for startups", output_format="newsletter")
print(f"Newsletter generated: {result.title}")
