# Repository Instructions for Assistants

These instructions apply to the entire repository and must be followed by
Codex and other development assistants.

## Canonical repository

Canonical repository: https://github.com/sebtuet/AcousticBrain.git

Use this URL as the project reference in prompts, summaries, pull request
descriptions, and issue or pull request references. A local clone, fork, or
remote may use another URL; it does not change the canonical repository. Do not
replace or reconfigure local Git remotes unless the developer explicitly asks.

## Developer workflow

The developer should perform only validations that genuinely require resources
or judgment unavailable to the assistant. These may include:

- running `main.py` against private or real acoustic measurements;
- checking real acoustic or hardware behavior;
- performing subjective listening;
- confirming a product or business decision that cannot be derived from the
  repository.

Do not ask the developer to run a command that the assistant can run itself.

## Assistant responsibilities

When the environment permits, the assistant must autonomously:

- inspect the repository and relevant Git history;
- inspect relevant issues and pull requests;
- understand the existing architecture before changing it;
- make scoped code or documentation changes;
- add or update relevant tests;
- run available formatting and static checks;
- run `git diff --check`;
- run targeted tests and the complete test suite when appropriate;
- inspect the final diff and look for regressions;
- prepare a concise result summary;
- propose a commit title and a pull request title and description.

The assistant must complete every automatable validation before requesting
manual validation.

## Manual validation protocol

When manual validation is genuinely necessary, the assistant must:

1. finish all automatable validation first;
2. provide one copy-ready `main.py` command;
3. explain briefly what the command validates;
4. identify the exact output lines or sections the developer should return;
5. avoid requesting several commands when one scenario can cover the validation.

For example, a relevant task might require:

```bash
python main.py \
  --measurements-root measurements \
  --evidence-acquisition
```

This is not a universal validation command. Options must match the feature
being validated.

## AcousticBrain engineering principles

- AcousticBrain is deterministic.
- Never invent absent data.
- Never present a hypothesis as a fact.
- Never assert causality that the available evidence does not establish.
- Preserve traceability across observations, reasoning, hypotheses, actions,
  and plans.
- Prefer small, coherent pull requests with clear user value.
- Reuse existing contracts and abstractions.
- Avoid premature generalization.
- Do not create a generic framework without at least one demonstrated concrete
  need.
- Prefer a specialized local implementation when only one use case exists.
- Preserve compatibility of structured outputs unless an explicit requirement
  justifies a change.

## Git policy

Git inspection, diffs, tests, and preparation of commit messages or pull
request descriptions are expected. Without an explicit instruction from the
developer, the assistant must not:

- create, amend, rewrite, or squash a commit;
- push or force-push a branch;
- open or merge a pull request;
- change Git remotes;
- delete a remote branch;
- publish a release.

Authorization for one Git operation does not imply authorization for another.

## Expected final report

At the end of a task, report:

1. the relevant existing state;
2. the changes made;
3. the files changed;
4. validations run and their results;
5. remaining limitations or risks;
6. one manual `main.py` validation only when genuinely required;
7. a proposed commit title;
8. a proposed pull request title and description;
9. whether any commit, push, or pull request creation occurred.
