# Product design system

Reading this as: practical B2B work software for small agencies and hiring reviewers, with a calm, precise visual language. Function and information hierarchy first; no generic AI gradients or ornamental dashboards.

## Shared foundation
- 4px spacing rhythm: 4/8/12/16/24/32/48. 14–16px body, 12px metadata (not primary controls), 28–36px page title.
- System sans for initial build (no external font request); a licensed self-hosted font may be added with budget/size review. Tabular numerals for dates/money/stats.
- Native labeled controls; Radix/shadcn for complex focus-sensitive dialogs when needed. One icon family (Phosphor), 18–20px, decorative icons hidden from accessibility tree.
- Buttons and inputs radius 6px; panels radius 10px; pill only for status badges. Borders define groups, not nesting card-in-card everywhere.
- At least 44px touch target where practical; readable 4.5:1 normal text contrast. Visible 2px focus ring. Never color-only status.
- Loading: content skeleton or clear operation label. Empty: why empty + next action. Error: specific recovery + retry. Destructive action: confirmation, then explicit result.
- URL carries filters/status/view and selected record where useful; browser back/forward works. No dead sidebar links or fictitious team switchers.

## ClientFlow — quiet agency operations
Palette: canvas #f7f8fa, surface #ffffff, ink #182321, muted #556460, border #dce3df, accent #176448, accent-soft #eaf4ef. One emerald accent; amber/red reserved semantic states.
Layout: 232px sidebar, 64px utility header, content max 1320px; project worklist is the main element. Small unboxed summary counts; a deadline rail on wide screens only. No made-up analytics chart.
```text
+----------------+------------------------------------------------+
| ClientFlow     | Workspace / Projects                 Demo mode |
| Workspace name +------------------------------------------------+
| Overview       | Projects                            New project|
| Projects       | [Active] [At risk] [Due soon]                  |
| (real routes)  | Search...     Status...        Table / Board   |
|                +----------------------------------+-------------+
|                | Project / Client / Status / Due | This week   |
|                | readable interactive work list  | actual data |
| Demo boundary  |                                |             |
+----------------+----------------------------------+-------------+
```
375px: compact header, wrapped real navigation, single-column toolbar and project rows/cards, no clipped actions. Detail/form lives on its own route in the first slice, avoiding a custom modal. Table view and status board are alternate views of the same dataset. Drag/drop only if keyboard-equivalent status control already exists.

## SupportDesk — editorial support inbox
Palette: canvas #f5f7fa, ink #1b2538, accent #2459b8, borders #dce2eb. Three-pane inbox desktop: queue 240px, conversation flexible, evidence 300px. Mobile queue → thread → sources via explicit navigation. Cite source title and excerpt beside the answer; never hide uncertainty behind a confidence percentage without calibration. Human handoff visibly changes ownership/status. Retrieval-only badge differs from generated-answer badge.

## InvoiceHub — document-first finance
Palette: canvas #f8f8f7, ink #272b32, accent #334c7c, border #dedfe2. Invoice list as ledger; editor left, printable preview right on wide screens. Right-aligned numbers, explicit currency, compact totals, no decorative revenue charts. Draft/issued/paid/void text distinct. Overdue is derived, not another mutable state. Print uses clean black on white, sensible page breaks, no navigation.

## Design review protocol
For each primary screen: describe job-to-be-done → sketch layout → define full state matrix → implement → take desktop/mobile screenshots → inspect actual render → axe + keyboard checks → record findings as `file:line – issue – fix`. Re-fetch Vercel guidelines for final review. Use owner reference images if supplied, not unlicensed stock or invented testimonials. No paid generated assets required.

## UI acceptance
No placeholder links, fake account switch, fake charts, or console-only buttons. Demo mode controls really mutate sample state and disclose persistence boundaries. Authenticated mode must match loading/error UX before release. Do not equate polished sample data with a live platform.
