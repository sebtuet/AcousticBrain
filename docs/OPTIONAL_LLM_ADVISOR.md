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
The v2 context also declares the expected response language, the exact
reasoning and blocking-factor ids that require coverage, READY and BLOCKED plan
ids, the complete allowed-id set, and deterministic display labels. The
provider never infers a plan status.

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

`ADVISOR_SYSTEM_PROMPT_V2` states the non-authoritative boundary, but the prompt
is not treated as a security control. Provider output must use the strict
structured schema: answer, cited object ids, claims with supporting ids and
structured fact assertions, preserved blocks, contradictions and limitations,
explicit empty collections for proposed actions and introduced scores, exact
coverage collections for reasoning, blocking factors and both plan classes,
and the declared response language.

## Post-response validation

The local validator checks:

- every object and claim reference exists in the canonical context;
- every claim cites provenance and asserts an exact structured fact;
- asserted evidence, dimensions, applicability, blocks, contradictions and
  limitations match the canonical objects;
- no blocked action is asserted applicable;
- no factor, contradiction or limitation is omitted, denied or invented;
- no new action, global score, percentage or absent geometry is introduced.
- structured coverage is complete, unique, correctly ordered and never crosses
  READY/BLOCKED plan classes;
- the declared language matches the request and manifest use of another
  language is rejected by a deliberately conservative check;
- empty, generic, copied or category-omitting answers are rejected as
  degenerate.

Validity is multidimensional: scientific fidelity, semantic coverage, response
language, reference integrity and degeneracy are reported independently. No
global score, average, probability or confidence number is computed. Overall
validation is valid only when every required dimension is valid.

Invalid provider text is never rendered as normal advice. A deterministic,
structured local safety report in the requested language is returned with
`INVALID`, the violations, all required coverage and the unchanged deterministic
references. `Response Source` distinguishes `PROVIDER` from
`LOCAL_SAFETY_RESPONSE`. Provider failures remain typed errors and are never
converted into scientific conclusions.

## CLI

```bash
python main.py \
  --measurements-root /path/to/campaign \
  --advisor \
  --advisor-provider mock \
  --question "Why is this action blocked?" \
  --advisor-language en \
  --advisor-audience general \
  --advisor-detail standard
```

Providers are `mock`, `ollama` and `openai`. Audience values are `general`,
`enthusiast`, `acoustician` and `developer`; detail values are `concise`,
`standard` and `technical`. A question without `--advisor`, or `--advisor`
without a question, is rejected. Language values are `fr`, `en` and `auto`.
`auto` uses deterministic markers from the question; an explicit choice always
wins. No interactive mode is added.

## Determinism and limitations

Context selection, reference closure, serialization, request ids, validation,
the safety response, Mock output and rendering are deterministic. Text from a
real Ollama or OpenAI model is not claimed to be reproducible byte-for-byte.

Semantic validation is intentionally conservative and combines exact
structured assertions with explicit prohibited overrides. It cannot make free
text intrinsically trustworthy; provider output remains non-authoritative and
is always subordinate to the structured deterministic objects displayed by the
validator.

## Local Ollama compatibility observations

Manual campaign trials on Ollama 0.31.2 remain separate from the automated
suite. With the six PR-059 plans in context, `qwen3:8b` produced a fully valid
French response in one run. A separate English run returned the prohibited
generic metadata sentence and was rejected. `gemma4:12b` produced structurally
grounded French output but omitted plan identifiers from its prose, then
returned invalid JSON in the English trial. Both outputs were rejected before
normal rendering.

These observations are model outputs, not deterministic guarantees: repeated
generation may differ. AcousticBrain therefore does not relax parsing, repair
missing coverage, retry automatically, select another model, or fall back to a
generic JSON mode. The local safety report is the only response rendered after
a semantic rejection; malformed provider JSON remains an explicit typed
provider error.
