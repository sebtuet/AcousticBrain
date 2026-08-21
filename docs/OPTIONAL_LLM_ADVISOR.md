# Optional LLM Advisor V2

> The Advisor explains AcousticBrain. It does not become AcousticBrain.

## Authority boundary

```text
V1 deterministic Report
→ CampaignUserAssessmentPresenter
→ CampaignUserAssessment
→ AdvisorAssessmentContext
→ optional provider
→ local validation
→ read-only AdvisorResponse
```

`CampaignUserAssessment` is the Advisor's only scientific source. The provider
does not receive the full V1 report, raw observations, unprojected reasonings or
weights, unselected plans, measurements, manifests, registries or campaign
files. It cannot call an analysis engine, workflow or tool.

The Advisor explains and reformulates facts in the current assessment. It does
not diagnose beyond V1, rank findings, choose a main problem, create severity or
causality, invent a correction, treatment, placement, EQ or protocol, replace
the selected plan, declare or execute an experiment, or mutate campaign state.

## Bounded context

`AdvisorContextBuilder` produces an immutable, versioned projection containing:

- campaign measurement and analysis-readiness states;
- projected findings and uncertainties;
- applicable and unavailable actions;
- the single next step already selected by V1, when present;
- its prerequisites and availability state;
- scientific boundaries and exact source identifiers.

It does not recalculate or select anything. `READY` means that the planning
contract is defined for its current state, not that execution is authorized.
`SUPPORTED` does not establish causality. `APPLICABLE` does not predict benefit
or physical safety. `AVAILABILITY_NOT_VERIFIED` is not a confirmed prerequisite.

## Strict-context conversation

The initial V2 policy is `STRICT_CONTEXT_ONLY`. For general acoustic knowledge,
an absent fact, another campaign, an unestablished cause, treatment or placement,
the bounded answer is:

> AcousticBrain does not currently establish this.

The question and all assessment strings are untrusted data. Instructions in
either cannot override the system contract or authorize use of a provider's own
acoustic knowledge. There is no conversational memory, RAG, web search, agent,
tool use or command execution.

The deterministic `mock` provider can restate the already selected V1 next
step and the existing uncertain or contradictory states for bounded questions
such as “What should I do next?”, “Que dois-je comprendre en priorité ?” and
“Qu’est-ce qui bloque ?”. It never turns that projection into a ranking, a
cause, an execution authorization or a physical recommendation.

## Providers and validation

The existing `mock`, `ollama` and `openai` providers retain the same transport
interface. Without `--advisor`, no provider is constructed and no provider
configuration or network is used. Ollama and OpenAI remain optional, explicitly
configured integrations with typed timeouts and provider errors.

Provider output uses the structured Advisor schema. Every published claim must
cite an allowed source. Local validation checks reference integrity, exact
structured states, preserved contradictions and limitations, language, and
semantic overreach. In particular it rejects transformations such as:

- `SUPPORTED` → proven, confirmed or established cause;
- `READY` → ready to run, ready to execute or executable now;
- `APPLICABLE` → guaranteed improvement, benefit or safety;
- `AVAILABILITY_NOT_VERIFIED` → available or confirmed;
- an invented main problem, best treatment or optimal placement.

Invalid semantic output is replaced by a deterministic local safety response.
Malformed provider JSON and provider failures remain explicit typed errors.
Real-provider prose is not byte-for-byte deterministic; the mock, context,
validation and safety response are deterministic.

### Provider timeouts

Local structured generation time depends on the model, hardware, assessment
context size and output schema. Ollama therefore defaults to 120 seconds and can
be configured explicitly:

```bash
export OLLAMA_ADVISOR_ENDPOINT=http://localhost:11434
export OLLAMA_ADVISOR_MODEL=qwen3:8b
export OLLAMA_ADVISOR_TIMEOUT_SECONDS=120
```

OpenAI retains its 30-second default and supports
`OPENAI_ADVISOR_TIMEOUT_SECONDS`. Values may be integer or floating-point
seconds and must be positive. The historical `ADVISOR_TIMEOUT_SECONDS` remains a
fallback when no provider-specific timeout is set; a provider-specific value
takes precedence. Provider timeouts continue to raise `AdvisorTimeoutError`.

## CLI

```bash
python main.py \
  --measurements-root /path/to/campaign \
  --advisor \
  --advisor-provider mock \
  --question "What should I do next?" \
  --advisor-language en \
  --advisor-audience general \
  --advisor-detail standard
```

Providers are `mock`, `ollama` and `openai`. Audience values are `general`,
`enthusiast`, `acoustician` and `developer`; detail values are `concise`,
`standard` and `technical`. Language values are `fr`, `en` and `auto`. A
question without `--advisor`, or `--advisor` without a question, is rejected.

The detailed deterministic reports remain the expert and audit views. The
Advisor is only a conversational presentation above their user assessment.
