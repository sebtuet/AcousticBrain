# Ollama Structured Output Compatibility

This document records manual provider checks. They are deliberately separate
from the automated suite: no automated test requires Ollama, a downloaded
model or network access.

## Environment

- Date: 2026-07-18
- Ollama: 0.31.2
- Endpoint: local `/api/generate`
- Models: `qwen3:8b` and `gemma4:12b`
- Campaign: external real campaign, 97 files

A minimal request confirmed that Ollama 0.31.2 accepts a JSON Schema object in
`format`; `qwen3:8b` returned an object constrained by that schema.

## Root cause reproduced

The previous adapter sent `"format": "json"`. With `qwen3:8b`, Ollama returned
a syntactically valid but incompatible chat-shaped object containing only
`role` and `content`. AcousticBrain correctly rejected it because none of the
canonical advisor response fields were present.

Sending only the canonical field schema corrected the outer shape for both
models, but did not guarantee exact preservation of nested grounding values.
Both models could still alter an assertion or omit a preserved value. Those
responses were rejected by the unchanged post-response validation rules.

## Corrected request

The adapter now sends the schema returned by
`provider_output_json_schema(required_grounding_values)` directly in `format`.
The generated schema keeps `answer` as model-produced text and constrains every
other response field with the exact deterministic grounding values. The same
schema and values are repeated in the prompt for compatibility; the prompt is
not the enforcement mechanism.

There is no fallback to generic JSON, alternate model, permissive parsing or
automatic response repair.

## Results

Both real-model runs received a schema-conformant object and completed local
validation with:

| Model | Validation | Blocking factors | Contradictions | Unsupported claims |
| --- | --- | ---: | ---: | ---: |
| `qwen3:8b` | `VALID` | 5 preserved | 2 preserved | 0 |
| `gemma4:12b` | `VALID` | 5 preserved | 2 preserved | 0 |

`gemma4:12b` took materially longer than `qwen3:8b` on this machine. Provider
latency and generated prose remain model- and hardware-dependent. A timeout is
reported as a typed provider error and never triggers a fallback.

An additional manual run exposed repeated identical validation violations. The
validator now deduplicates identical violation messages before constructing
the immutable safety response. This changes no acceptance rule: the response
remains `INVALID`, and the deterministic local safety answer is rendered.
