# Finish the Entire Projects Repository

Run this only after no in-scope project is `DISCOVERED`, `PLANNED`, or `ACTIVE`.

## Repository-level checks

1. Re-inventory the root and compare it with `PROJECTS.md` so no project was missed.
2. Verify every in-scope project has a terminal status and linked proof.
3. Confirm each `COMPLETE` project passed its project audit.
4. Confirm every `BLOCKED` project has evidence, exact external action, and a resume command.
5. Confirm every `OUT_OF_SCOPE` project has explicit owner approval or a clearly authoritative scope source.
6. Check shared packages and configuration against all consumers.
7. Run repository-level checks if they exist.
8. Check that root documentation links resolve and status counts agree.
9. Review the full working tree for secrets, generated artifacts, and uncommitted work.
10. Verify remote/PR/deployment claims rather than assuming local success implies them.

## Portfolio roll-up

Produce a truthful table:

| Project | Outcome | Strongest proof | Demo/deploy | Important limitation | Status |
|---|---|---|---|---|---|

Then identify:

- the best project to feature first;
- one defensible metric from each completed project;
- one architecture/decision talking point from each;
- one failure-handling story from each;
- owner-only actions still needed, in exact order.

## Final repository completion gate

- [ ] all plausible project folders classified
- [ ] all in-scope projects terminal
- [ ] all complete projects audited with no critical/high findings
- [ ] proof links and demo claims verified
- [ ] registry counts correct
- [ ] root resume says `NONE — repository terminal` or names the first external unblock action
- [ ] clean/safely documented git state
- [ ] no invented URLs, metrics, screenshots, test results, or PRs

If any box fails, the repository is not finished. Update `PROJECTS.md` and activate the smallest task that closes the gap.
