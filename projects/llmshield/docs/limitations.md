# Limitations

- Injection checks detect reviewed lexical families and obfuscation signals; they do not understand arbitrary semantic attacks.
- Regex PII detection can miss novel formats and can flag legitimate number-like text. Credit cards require Luhn validation.
- The deterministic provider proves application flow only. It does not prove Groq, Gemini, quota, latency, or model quality.
- Memory logs are process-local. Production durability requires applying the Postgres migration and setting `DATABASE_URL`.
- Local trace IDs prove correlation only. Langfuse availability and trace shape require owner credentials and a live smoke test.
- Authentication, tenant isolation, rate limiting, content moderation models, and tool sandboxing are production controls outside this portfolio demo.
