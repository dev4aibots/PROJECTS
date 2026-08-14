# Engineering Decisions

- One document type only: invoice depth produces stronger failure evidence than shallow classification breadth.
- Decimal, never float: binary rounding is unacceptable for money and all DB money columns are NUMERIC.
- Default tolerance is 0.02 currency units to absorb normal document rounding; boundary tests freeze behavior.
- Trust labels avoid fabricated confidence: arithmetic/date/currency fields can be verified; names remain unverified; raw payload is AI-extracted.
- No Groq fallback: its configured text model cannot inspect documents. A vision outage must be an honest 503.
- Never auto-correct mismatches: financial review needs original evidence and explicit deltas.
- In-memory deterministic mode proves local behavior only; hosted storage/database/provider remain separate evidence gates.
