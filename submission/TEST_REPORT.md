# Automated test report

Verified in the packaged source environment:

```text
python -m compileall -q .
python -m pytest -q
10 passed
```

Coverage includes:
- SQLite lead storage and username deduplication.
- Follower-count parsing.
- Demo workflow: AI demo analysis, draft generation, simulated send and opt-out stop rule.
- Public search parsing for canonical Instagram profile URLs ending in `/` (HTTP call mocked).
- Live inbox-processing opt-out path (Gmail fetch mocked), including no reply draft for an opt-out.
- Follow-up timing and suppression after an influencer replies.
- Groq OpenAI-compatible endpoint selection, model, and bearer-key handling (network mocked).
- Claude Messages API selection and key handling (network mocked).

These are automated code tests, not live-service verification. They do **not** prove live Groq, Anthropic, SerpAPI, Gmail or Google Sheets connectivity. Those require the user's own credentials and a controlled end-to-end test. No API key is included in the ZIP; create your own Groq key and add it locally to `.env`.
