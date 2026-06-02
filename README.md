# content-automata

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ivanjay233/content-automata/actions/workflows/ci.yml/badge.svg)](https://github.com/ivanjay233/content-automata/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/content-automata/)

**AI-powered content pipeline** — topic research → copywriting → image generation → scheduling. One automated workflow for content creators and SMBs.

---

## Table of Contents

- [What is content-automata?](#what-is-content-automata)
- [Quick Start](#quick-start)
- [Pipeline Architecture](#pipeline-architecture)
- [Supported Platforms](#supported-platforms)
- [Installation](#installation)
- [Configuration](#configuration)
- [CLI Usage](#cli-usage)
- [Python API](#python-api)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## What is content-automata?

content-automata automates the entire content creation workflow:

1. **Research** — Given a topic or URL, it performs web research, identifies key points, and analyzes competitors.
2. **Copywriting** — Generates multiple content variants (blog posts, social media copy, ad copy) with tone customization.
3. **Image Generation** — Creates matching visuals using AI image APIs with configurable aspect ratios.
4. **Scheduling** — Formats and exports content for publishing (Markdown, HTML, CSV).

Built for content creators, marketers, and SMBs who want to go from idea to published content in minutes.

---

## Quick Start

```python
from content_automata import Pipeline

# Initialize and run the full pipeline
pipeline = Pipeline(api_key="your-api-key")
result = pipeline.from_topic("AI for small businesses")
print(result)
```

Three lines. Full content package in return.

---

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    content-automata                          │
│                                                              │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐  │
│   │ Research  │──▶│ Writing  │──▶│ Visuals  │──▶│Schedule │  │
│   │  Stage    │   │  Stage   │   │  Stage   │   │  Stage  │  │
│   └──────────┘   └──────────┘   └──────────┘   └─────────┘  │
│        │               │              │              │       │
│        ▼               ▼              ▼              ▼       │
│   Topic →       Copy →           Images →        Export →  │
│   Outline       Variants         Assets          Publish    │
└──────────────────────────────────────────────────────────────┘
```

The pipeline is a state machine with these states:

| State      | Description                         |
|------------|-------------------------------------|
| `research` | Web research & topic analysis       |
| `draft`    | Copywriting & content generation    |
| `review`   | Content review & quality checks     |
| `visuals`  | Image generation & asset creation   |
| `schedule` | Formatting, export, and scheduling  |

---

## Supported Platforms

- **Web Research**: Tavily, Exa (configurable)
- **Content Export**: Markdown, HTML, CSV
- **Scheduling**: Ready for integration with Buffer, Hootsuite, WordPress

---

## Installation

```bash
pip install content-automata
```

Or install from source:

```bash
git clone https://github.com/ivanjay233/content-automata.git
cd content-automata
make install
```

---

## Configuration

Create a `config.yaml` file:

```yaml
api_key: "your-api-key-here"
research:
  provider: "tavily"       # tavily | exa
  max_results: 5
copywriting:
  default_tone: "professional"  # professional | casual | persuasive | humorous
  variants: ["blog", "social", "ad"]
image_generation:
  provider: "openai"      # openai | stability
  default_aspect: "16:9"
scheduling:
  export_formats: ["markdown", "html", "csv"]
```

See `examples/config.yaml.example` for a full template.

---

## CLI Usage

```bash
# Initialize a new project
cauto init

# Run the full content pipeline
cauto run --topic "AI for small businesses"

# Schedule content for publishing
cauto schedule --format markdown

# Check pipeline status
cauto status
```

---

## Python API

```python
from content_automata import Pipeline

# Create a pipeline
pipeline = Pipeline(config="config.yaml")

# Start from a topic
result = pipeline.from_topic("AI for small businesses")

# Start from a URL
result = pipeline.from_url("https://example.com/blog-post")

# Start from a brief
result = pipeline.from_brief({
    "topic": "AI for small businesses",
    "keywords": ["automation", "customer service", "marketing"],
    "target_audience": "small business owners",
    "tone": "professional"
})

# Access results
print(result.research.outline)
print(result.draft.blog_post)
print(result.visuals.image_urls)
print(result.schedule.exports)
```

---

## Examples

```bash
# Run the basic pipeline example
python examples/basic_pipeline.py

# Or with make
make example
```

---

## Development

```bash
# Install in development mode
make install

# Run tests
make test

# Clean build artifacts
make clean
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
