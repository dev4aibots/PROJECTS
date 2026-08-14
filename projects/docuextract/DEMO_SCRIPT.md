# Demo

1. Clean invoice → green VERIFIED report.
2. Broken-total invoice → red VERIFICATION_FAILED: expected 11,800, actual 12,800, delta 1,000; show raw value was not changed.
3. Broken line item → exact indexed field failure.
4. Receipt PNG → same verified pipeline.
5. Cat image → friendly FAILED_EXTRACTION and no fabricated invoice.
6. Run `pytest backend/tests/test_verification.py -v`; close with 18 total tests and 5/5 local verdict eval, clearly excluding live Gemini claims.
