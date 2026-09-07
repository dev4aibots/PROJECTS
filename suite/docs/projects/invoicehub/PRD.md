# InvoiceHub — product requirements

## Problem
Freelancers/small businesses need consistent invoices, a clear outstanding balance and a simple expense record. A spreadsheet can hide rounding and duplicate-payment mistakes. InvoiceHub demonstrates reliable business rules, not payment processing or tax-certified accounting.

## v1 stories
| ID | Story | Acceptance |
|---|---|---|
| IH-P1 | Owner sets up business/customer details | Validated per-workspace records; isolation and role checks |
| IH-P2 | Member prepares invoice draft | Add/edit/remove line items; exact server totals; discount/tax; saved draft reloads |
| IH-P3 | Owner/admin issues invoice | Atomic unique number and immutable business/customer/items/totals snapshot |
| IH-P4 | Owner/admin records manual partial/full payment | Positive amount, invoice currency, no overpayment, idempotency key; balance/status derived |
| IH-P5 | Owner/admin voids unpaid issued invoice | Reason required, immutable history; paid/partially paid invoice not voidable in v1 |
| IH-P6 | User exports PDF | Real downloadable PDF matching stored issue snapshot; authenticated access, overflow/page breaks handled |
| IH-P7 | User records expenses | Category/date/amount/currency, optional receipt later, filtering and export |
| IH-P8 | User sees balances/reporting | Per-currency totals; unpaid/overdue and cash received distinct; no mixed-currency aggregation |

## Business rules
Supported initial currencies: INR, USD, EUR (2 minor digits). No FX conversion. Tax is a generic rate field, not GST compliance. Quantity scale up to 3 decimals; unit price parsed from decimal string into minor units. Line gross = round-half-up(unit_price_minor × quantity_millis / 1000). Discount rate basis points applied/rounded per line; tax basis points applied/rounded to discounted line. Sum rounded lines. Tax-exclusive only. Example: 19.99 × 1.5 → 29.99; 10% discount → 3.00; taxable 26.99; 18% tax → 4.86; total 31.85. Tests lock this policy.

Draft → issued → derived partially_paid/paid; issued with zero payments → void with reason. Overdue derived from due_date < today AND outstanding > 0, not a mutable status. No delete/edit issued financial values. Due date on/after issue date. Invoice numbers unique per workspace/year allocated only on issue, not draft. Do not promise legally gapless numbering.

## Exclusions and risks
No real money movement, payment gateway, bank feeds, automatic tax returns, legally compliant e-invoice/GST schema, refunds, credit notes, multiple tax regimes or double-entry general ledger. These require separate validated scope. No financial advice claims. Synthetic data only in public demo.

## Edge cases
Zero price allowed (free item), invoice must contain at least one valid line, bounded total; negative/NaN/Infinity/exponent notation rejected. Maximum line/invoice amount within safe integer bounds before arithmetic; BigInt intermediate math. Duplicate submit/issue/payment safe. Partial payment then void denied. Two simultaneous payments cannot exceed balance. Export escaped to prevent CSV formulas, filenames sanitized.
