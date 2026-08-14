# Deterministic Verification

Checks use `Decimal`: each `quantity × unit_price` versus line total; line-total sum versus subtotal; subtotal plus tax versus total; invoice date no later than tomorrow; recognized ISO currency. Absolute delta `<= 0.02` passes. Missing tax uses zero and records `assumed_zero`.

Negative quantities/prices/totals and unknown currencies fail Pydantic before verification. Zero quantity is valid only when its line arithmetic balances. The engine returns expected, actual, delta, field, and verdict for every check and never changes extracted values.
