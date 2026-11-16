# Assignment mapping and evidence checklist

| Assignment requirement | Implementation / evidence to capture |
|---|---|
| Search by niche, keywords, location, follower count | Research tab with SerpAPI; show query and returned public profile URLs. Search results are limited to indexed public web data. |
| Public name, username, link, niche, followers, business email, location | Candidate table and CRM. Show source; leave unavailable fields blank and verify manually. |
| AI profile analysis, category, summary, score, priority | AI Filter tab with a real provider key configured. Groq is the default; the assignment explicitly names Claude, so select Claude if you obtain Anthropic API access or get written approval to use Groq. |
| Google Sheets / CRM and duplicate prevention | CRM tab; import/save the same profile twice and show duplicate prevention; show Sheets sync if configured. |
| Personalised cold email and human approval | Outreach tab; open/edit draft, click Approve and send to test mailbox. |
| Follow-up after 3–5 days and another 5–7 days | Scheduler worker; defaults 4 and 6 days. Use a separate test DB with shorter intervals only for a controlled demo. |
| Stop follow-ups after reply/decline/opt-out | Demonstrate reply detection and show no further follow-up created for that lead. |
| Classify replies and generate human-reviewed reply | Replies tab; show classification, suggested action, reply draft, approval. |
| End-to-end demonstration and deliverables | Record screen walkthrough, submit this source ZIP, export workbook, sample initial/follow-up/reply emails and this mapping. |

## Known external dependencies / limits

- Live public-web search requires a SerpAPI key and is constrained by search-engine indexing.
- Live AI requires a Groq API key (default) or an Anthropic API key when `AI_PROVIDER=claude`. Groq does not fulfil the exact Claude-specific requirement unless the coordinator approves it.
- Live Gmail requires Google Cloud OAuth credentials and user consent.
- Google Sheets requires a service-account JSON and spreadsheet sharing.
- The scheduler must run as a separate long-lived process; it is not a serverless/background service when the UI is closed.
- Synthetic sample records are only for safe demonstration and must not be presented as real influencers.
