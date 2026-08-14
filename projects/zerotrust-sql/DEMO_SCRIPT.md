# 90–120 Second Demo

1. Show the landing scorecard and seven defense layers.
2. Run “Top 10 customers by revenue”; show generated SQL, green checks, and descending results.
3. Run “DROP TABLE orders”; show statement-type failure and no executed SQL.
4. Run piggyback SQL; show single-statement failure.
5. Run the million-row request; show `LIMIT INJECTED` and exactly 100 rows.
6. Show recent audit events and explain the independent read-only role.
7. Close with `pytest` (57 passed), corpus 50/50, and golden eval 13/13. State clearly that live deployment is not yet verified.
