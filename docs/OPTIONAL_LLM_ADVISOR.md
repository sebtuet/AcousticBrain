# Optional LLM Advisor

> The advisor is not a scientific authority.
> Le conseiller n’est pas une autorité scientifique.

## Boundary

```text
Deterministic Scientific Core
    ├── Observations
    ├── Reasoning
    ├── Corrective Actions
    └── Evidence Weighting
             │
             ▼
      Deterministic Context Builder
             │
             ▼
        Advisor Provider
             │
             ▼
      Response Validator
             │
             ▼
       Read-only Renderer
```

The deterministic core remains the only source of scientific truth. The
optional advisor selects, links, summarizes and reformulates existing objects.
It cannot create or change evidence, reasoning, actions, weight dimensions,
contradictions, limitations, blocking factors, geometry, protocols or
parameters.

Without `--advisor`, no provider is constructed, no provider configuration or
API key is read, and no network request is attempted. The deterministic engine
has no provider dependency.

## Canonical context

`AdvisorContextBuilder` starts from the selected Evidence Weight ids (all
weights by default) and follows their explicit action, reasoning and observation
references. Unreferenced observations are excluded. Each object is retained as
canonical, stably ordered JSON with its type, id and references. Blocking
factors, contradictions and limitations are separately preserved.

The provider receives a minimal textual JSON projection. It never receives raw
measurement files, local paths, secrets or API keys. Context construction does
not access the measurement filesystem or recalculate an analysis.

## Provider contract

All providers implement `provider_id`, `is_available()` and
`generate(request, context)`. There is no fallback between providers.

### Mock

`mock` is offline and byte-for-byte stable. Test modes cover compliant output,
hallucination, unknown references, omitted or contradicted blocks, falsely
resolved contradictions, invented scores or actions, failure and timeout.

### Ollama

Ollama is optional and uses the standard-library HTTP client. Configure:

```bash
export OLLAMA_ADVISOR_ENDPOINT=http://localhost:11434
export OLLAMA_ADVISOR_MODEL=your-explicit-model
```

AcousticBrain never starts or installs Ollama. Missing configuration, network
errors and timeouts are explicit failures.

The Ollama `/api/generate` request sends the complete canonical JSON Schema in
`format` and repeats it explicitly in the user prompt for model compatibility.
It never falls back to the generic `"json"` format. A syntactically valid JSON
object outside the contract, including a chat-shaped `{role, content}` object,
is rejected without conversion or repair. Local compatibility was verified
with Ollama 0.31.2; provider behavior may still vary by model, so the local
post-response validator remains authoritative and strict.

### OpenAI

The OpenAI adapter is optional, isolated, and uses the Responses API with a
strict Structured Outputs JSON schema. Configure:

```bash
export OPENAI_API_KEY=...
export OPENAI_ADVISOR_MODEL=your-explicit-model
```

The endpoint defaults to `https://api.openai.com/v1/responses` and may be
explicitly overridden with `OPENAI_ADVISOR_ENDPOINT`. The API key is read only
when the OpenAI advisor is explicitly enabled, is sent only in the
Authorization header, and is never serialized into context or logged.

`ADVISOR_TIMEOUT_SECONDS` configures either real adapter. No SDK or mandatory
provider dependency is installed.

## Prompt and structured response

`ADVISOR_SYSTEM_PROMPT_V1` states the non-authoritative boundary, but the prompt
is not treated as a security control. Provider output must use the strict
structured schema: answer, cited object ids, claims with supporting ids and
structured fact assertions, preserved blocks, contradictions and limitations,
and explicit empty collections for proposed actions and introduced scores.

## Post-response validation

The local validator checks:

- every object and claim reference exists in the canonical context;
- every claim cites provenance and asserts an exact structured fact;
- asserted evidence, dimensions, applicability, blocks, contradictions and
  limitations match the canonical objects;
- no blocked action is asserted applicable;
- no factor, contradiction or limitation is omitted, denied or invented;
- no new action, global score, percentage or absent geometry is introduced.

Invalid provider text is never rendered as normal advice. A deterministic local
safety answer is returned with `INVALID`, the violations, and the unchanged
deterministic references. Provider failures remain typed errors and are never
converted into scientific conclusions.

## CLI

```bash
python main.py \
  --measurements-root /path/to/campaign \
  --advisor \
  --advisor-provider mock \
  --question "Why is this action blocked?" \
  --advisor-audience general \
  --advisor-detail standard
```

Providers are `mock`, `ollama` and `openai`. Audience values are `general`,
`enthusiast`, `acoustician` and `developer`; detail values are `concise`,
`standard` and `technical`. A question without `--advisor`, or `--advisor`
without a question, is rejected. No interactive mode is added.

## Determinism and limitations

Context selection, reference closure, serialization, request ids, validation,
the safety response, Mock output and rendering are deterministic. Text from a
real Ollama or OpenAI model is not claimed to be reproducible byte-for-byte.

Semantic validation is intentionally conservative and combines exact
structured assertions with explicit prohibited overrides. It cannot make free
text intrinsically trustworthy; provider output remains non-authoritative and
is always subordinate to the structured deterministic objects displayed by the
validator.
