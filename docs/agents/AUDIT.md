# Adversarial Project Completion Audit

Run this after implementation claims are complete and before marking the project `COMPLETE`. Audit the active project only; do not refactor unrelated code.

## 1. Establish claimed scope

Read the project brief, checklist, README, proof ledger, and limitations. List every shipped claim and primary user flow. Roadmap items must be clearly labeled as unshipped.

## 2. Trace user-visible behavior

For each important button, form, CLI command, endpoint, or library entry point, trace:

```text
input -> validation -> handler -> domain/service -> dependency/storage -> response -> visible result
```

Flag dead handlers, nonexistent endpoints, static fixtures presented as live data, swallowed errors, missing persistence, or UI state that does not reflect the result.

## 3. Search for unfinished or deceptive paths

Search project-scoped files for terms such as:

```text
TODO FIXME mock fake dummy placeholder lorem hardcoded not implemented
example.com console.log pass return [] return {}
```

Not every match is a defect. Classify and justify each material match. Test fixtures and explicit demo samples are acceptable when labeled and isolated from real paths.

## 4. Execute verification

Use project-native commands and record output:

- dependency/install integrity;
- typecheck/lint/format;
- full relevant test suites, including skipped-test explanation;
- production build/package where environment permits;
- import/startup check;
- one happy path and one invalid-input path for each primary interface;
- fresh migration/schema check where safe;
- deployment smoke if a live URL is claimed.

Do not run destructive or cost-incurring live checks without approval.

## 5. Data and dependency reality

Check that:

- referenced tables/columns/files/routes exist;
- migrations match current code and run in order on an isolated database when feasible;
- lists and dashboards read from declared sources;
- retries and idempotency avoid duplicate side effects;
- external dependency failures are user-safe;
- no runtime depends accidentally on process memory or local files when the deployment is stateless.

## 6. Security and privacy

Check project-relevant threats:

- secrets in working tree and tracked history;
- server secrets exposed to clients;
- authorization and data isolation;
- hostile input, upload limits, injection, path traversal, SSRF, unsafe deserialization, or generated-code execution as applicable;
- raw stack traces, SQL, personal data, prompts, provider payloads, or tokens in responses/logs;
- claimed security controls mapped to tests;
- dependency advisories, interpreted rather than blindly counted.

## 7. Claims versus evidence

For every README result and capability, identify code plus proof. Remove, qualify, or implement unsupported claims. Verify diagrams and setup commands against the current repository.

For AI projects, additionally verify:

- eval dataset and methodology are versioned;
- test/eval calls are distinguished from mocked calls;
- malformed output and provider failure are handled;
- refusal/insufficient-evidence behavior exists where required;
- metrics are reproducible and not cherry-picked without disclosure;
- prompt injection or project-specific adversarial cases are covered.

## 8. Report before fixing

Write findings to the project `PROOF.md` or project audit file using:

| Severity | Location | Finding | Proof | Minimal fix | Status |
|---|---|---|---|---|---|

Severity meanings:

- `CRITICAL`: broken core flow, data/security exposure, fabricated feature, unusable build
- `HIGH`: important unhandled failure, untested security claim, deployment incompatibility
- `MEDIUM`: incomplete secondary behavior, weak test, documentation drift
- `LOW`: minor maintainability or presentation issue

Fix all critical and high findings. Re-run affected checks and the full practical verification set. Critical/high open findings block completion.

## 9. Completion gate

A project can become `COMPLETE` only if:

- [ ] accepted scope works end to end
- [ ] no open critical/high findings
- [ ] tests/checks pass at the documented level
- [ ] proof ledger is current
- [ ] README and diagrams match reality
- [ ] limitations and unverified external steps are explicit
- [ ] demo path is reproducible
- [ ] checklist and resume show a terminal state
- [ ] git working state is safe and documented

Do not say "done" when the honest state is "code complete, live verification blocked." Use the more precise status.
