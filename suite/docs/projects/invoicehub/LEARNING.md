# InvoiceHub learning guide (planned)

## Key idea
Money is domain data, not UI formatting. JavaScript floating-point arithmetic can create small discrepancies; parse decimal strings into integer minor units, use BigInt intermediates for multiplication, enforce bounds, and format only at display boundaries. SQL and server computation remain authoritative.

## Walk one invoice
Input “19.99”, quantity “1.5” → 1999 minor units, 1500 quantity-millis → half-up 2999 gross → 300 discount at 10% → 2699 taxable → 486 tax at 18% → 3185 total. Explain each rounding boundary. Do not just say “we round to two decimals.”

Draft editing is mutable; issue creates an immutable business/customer/item snapshot. Changing customer address later must not change old invoice PDF. Payment events reduce outstanding balance; manual status dropdown cannot declare money received.

## Interview questions
**Why use minor units?** Exact representation for supported currencies and predictable integer sums. Need exponent rules; not every world currency has two decimals. v1 explicitly limits currencies.

**What prevents duplicate invoice numbers?** Unique workspace/year/sequence constraint plus a locked transactional counter on issue, not `max(number)+1` in client code.

**What is idempotency?** Same request key and payload yields the same canonical payment; retry does not double-charge/record. Same key with different amount is a conflict, not silently accepted.

**How do you stop two simultaneous overpayments?** Lock invoice row while checking current payments and inserting; all writers use the same controlled transaction path. Two frontend balance checks are not enough.

**Why no mixed-currency revenue total?** Summing USD and INR without a defined FX policy misleads. Group by currency and distinguish cash received from invoice totals.

**Why isn't this tax-compliant software?** Generic invoice fields/rates don't meet jurisdiction-specific legal/filing/e-invoice requirements. State the limitation and don't fabricate compliance claims.

## Exercises
Write tests for 0.005 tie rounding, quantity 0.001, invalid exponent strings, max safe amount, 100% discount and partial payment. Freeze an invoice, change customer address, verify PDF unchanged. Simulate double issue/payment. Test CSV value beginning '='. Show which test failed before your fix.

## Presentation
Demonstrate issue once, retry issue (no new number), partial payment, PDF from saved snapshot, and an overpayment rejection. Open the transaction/constraint tests. Explain the deliberately narrow financial scope.
