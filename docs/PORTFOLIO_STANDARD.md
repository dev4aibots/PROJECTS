# Portfolio and Proof-of-Work Standard

The repository should show how the owner thinks and verifies, not just that an agent can generate files. Apply this standard proportionally to each project's real scope.

## 1. The 90-second scan

A reviewer should find, above the fold or within one click:

1. one-sentence problem and differentiator;
2. a real screenshot or live demo link when applicable;
3. architecture at a glance;
4. one trustworthy result: evaluation, test, performance, security, accessibility, or reliability metric;
5. setup and test commands that work;
6. honest limitations and current status.

## 2. Required evidence by project type

| Project type | Minimum evidence |
|---|---|
| AI/LLM/RAG/agent | golden or attack dataset; deterministic checks where possible; model/eval configuration; failure and refusal behavior; saved honest results |
| API/backend | contract tests; invalid-input and dependency-failure tests; data persistence proof; security boundaries; representative curl output |
| Frontend | production build/typecheck; critical interaction tests; loading/error/empty states; accessibility check; responsive screenshots |
| Data/CLI/library | deterministic fixtures; unit/integration tests; sample invocation and output; edge cases; performance measurement when relevant |
| Security project | threat model; attack corpus; false-positive/false-negative discussion; defense-in-depth proof; residual risks |
| Static site | link check; responsive and accessibility checks; Lighthouse or equivalent; deployed URL/screenshot when in scope |

A project can document why a row is not applicable. It cannot silently substitute an unrelated metric.

## 3. Truth rules

- A command is evidence only if it was run and its exit/result recorded.
- A live URL is evidence only after a post-deploy smoke test.
- A screenshot is evidence only if it depicts the current build.
- A benchmark records hardware/environment, input, date, and method.
- An AI metric records dataset, metric definition, model/provider, prompt/version, run date, and limitations.
- Mocked tests prove application logic, not provider or deployment availability. Label them.
- Do not claim production-ready, secure, complete, or accessible without defining and meeting a matching gate.

## 4. Recommended project README structure

1. Title, pitch, status, demo/repository links
2. Screenshot or terminal demo
3. Problem and intended users
4. Solution and differentiator
5. Real architecture diagram
6. Key capabilities, with no roadmap items presented as shipped
7. Results/evaluation table with methodology link
8. Failure handling table: scenario, behavior, proof
9. Technology choices and links to decisions
10. Quickstart and environment variables
11. Test and verification commands
12. API/usage examples
13. Limitations, security caveats, and next improvements
14. Author/contact and license if appropriate

Keep detailed reference material in project docs; keep the root README scannable.

## 5. Project completion portfolio gate

Before `COMPLETE`, verify:

- [ ] no undeclared mock path powers the primary demo
- [ ] no dead primary UI action
- [ ] README claims map to code and evidence
- [ ] architecture diagram matches deployed/current implementation
- [ ] important decision tradeoffs are documented
- [ ] at least one happy path and meaningful failure path are demonstrated
- [ ] results are reproducible or clearly marked as externally dependent
- [ ] limitations include cost/free-tier, privacy, security, scale, and environment constraints that actually apply
- [ ] demo script uses real inputs and does not depend on hidden manual repair
- [ ] owner can explain the principal architecture and tradeoffs

## 6. Proof record format

Use `docs/projects/<project-id>/PROOF.md` as the evidence ledger. Prefer concise records with:

- acceptance criterion;
- exact command or manual procedure;
- timestamp and environment;
- observed result;
- artifact/link;
- limitations or unverified portion.

Do not paste huge logs. Store a small artifact or summarize output with enough detail to reproduce it.
