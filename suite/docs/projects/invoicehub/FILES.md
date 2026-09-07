# InvoiceHub planned file ledger

Relative to `suite/apps/invoicehub/`. Nothing implemented until IH-01. Expand config/UI paths before task completion; no blank scaffolding.

| File | Symbols / contract | Gate | State |
|---|---|---|---|
| package.json | independent app scripts/dependencies | IH-01 | planned |
| package-lock.json | reproducible exact versions | IH-01 | planned |
| src/lib/money.ts | parseMinorUnits, roundHalfUp, calculateLine/Invoice | IH-01 | planned |
| src/lib/invoice-state.ts | allowed lifecycle/derived balance | IH-01 | planned |
| src/lib/invoice-schema.ts | runtime limits/currency/quantity | IH-01 | planned |
| tests/money.test.ts | rounding/overflow/zero/negative/property cases | IH-01 | planned |
| tests/invoice-state.test.ts | invalid lifecycle and overdue | IH-01 | planned |
| src/app/layout.tsx | invoice brand/root boundary | IH-02 | planned |
| src/components/invoice-editor.tsx | line items and draft UX | IH-02 | planned |
| src/app/app/[workspaceId]/invoices/actions.ts | server-authoritative draft/issue mutations | IH-02/03 | planned |
| src/lib/data/customers.ts | user-scoped client lookup | IH-02 | planned |
| src/lib/pdf.ts | issued snapshot to PDF bytes | IH-03 | planned |
| src/app/api/invoices/[id]/pdf/route.ts | authenticated safe PDF headers | IH-03 | planned |
| src/lib/payments.ts | validated idempotent record command | IH-03 | planned |
| tests/payments.test.ts | duplicate/conflicting/overpayment cases | IH-03 | planned |
| src/lib/expenses.ts | category/amount/date validation | IH-04 | planned |
| src/lib/reports.ts | per-currency totals, safe CSV | IH-04 | planned |
| tests/invoices.spec.ts | full draft/issue/payment/PDF browser flow | IH-05 | planned |
| suite/supabase/migrations/<timestamp>_invoicehub.sql | invariants/RLS/issue/payment functions | IH-01/03 | planned |
| suite/supabase/tests/invoicehub_rls.test.sql | roles/tenant/concurrent financial tests | IH-05 | planned |

Auth utilities follow verified ClientFlow patterns; record actual paths, do not reference non-existing shared packages. Add PDF library/font license and env/readme evidence at implementation.
