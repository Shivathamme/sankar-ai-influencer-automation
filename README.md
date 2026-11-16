# Sankar Group — AI-Powered Instagram Influencer Research & Email Outreach

A practical Python + Streamlit implementation of the six-step internship assignment. The app has a safe demo mode and separately configurable live integrations.

## What is included

1. **Influencer discovery:** SerpAPI-backed Google public-web search for indexed Instagram profile URLs using niche, location and keywords; follower range filters; optional second search for publicly published business emails; CSV import; manual verification. It does not scrape Instagram pages or bypass login/access controls. Search result fields can be incomplete.
2. **AI provider:** Groq API is the default (free tier, subject to model-specific limits) for profile relevance, category, summary, 0–100 score, personalised initial/follow-up emails and reply classification. Anthropic Claude is also supported by selecting `AI_PROVIDER=claude`. Important: the assignment explicitly names Claude; Groq demonstrates equivalent LLM workflow capabilities but does not satisfy the Claude-specific wording unless the coordinator approves the alternative. When demo mode is on and no provider key is present, deterministic sample responses are used and labelled as simulated.
3. **CRM:** SQLite database, username deduplication, statuses, activity history, Excel/CSV export and optional Google Sheets sync.
4. **Gmail outreach:** Gmail API OAuth. Initial emails are drafts and require a human to edit/approve before sending. Daily limit and test-recipient override are supported.
5. **Follow-ups:** Separate `scheduler.py` worker checks the inbox before creating/sending follow-ups. Defaults: first after 4 days; second 6 days after the first. Stops when a reply, decline or opt-out is detected. If inbox checking fails, the follow-up run fails closed.
6. **Reply management:** Gmail inbox thread matching, selected-provider classification, suggested next action, reply draft and CRM status update. Reply drafts require human approval. Explicit opt-outs are handled deterministically without asking the LLM.

## Windows quick start

1. Extract the ZIP.
2. Double-click `run.bat` (creates `.venv`, installs packages, creates `.env`, starts Streamlit).
3. Open the local URL shown in the terminal (normally `http://localhost:8501`).
4. In demo mode, load synthetic sample leads and walk through the UI. No external email is sent.

To run automatic follow-up checks, open a **second terminal** in the project folder and run `run_scheduler.bat`. Keep this process running. The scheduler is a separate worker by design; it must be running for unattended follow-ups.

## Configure live services

Never paste API keys or OAuth secrets into ChatGPT or commit them to Git. Store them locally in `.env`.

### A. Groq API (default; no Anthropic key needed)

1. Create a Groq account at https://console.groq.com/.
2. Open https://console.groq.com/keys and create your own API key.
3. Copy the key into the local `.env` file as `GROQ_API_KEY=...`.
4. Keep `AI_PROVIDER=groq` and use `GROQ_MODEL=openai/gpt-oss-120b` unless your Groq console shows a different model available to your account.
5. Free-plan requests are subject to model-specific rate limits. Check https://console.groq.com/docs/rate-limits. Exceeding a free-tier limit can return HTTP 429; it does not silently turn the free account into a paid one. Check the current billing page before upgrading.

Never paste the key into ChatGPT, source code, screenshots or Git. The ZIP deliberately contains an empty placeholder, not a working key.

### B. Claude API (if you need to satisfy the assignment's named-provider requirement)

- Create an API key in the Anthropic Console and add it locally as `ANTHROPIC_API_KEY=...`.
- Set `AI_PROVIDER=claude` in `.env`.
- `CLAUDE_MODEL` is configurable; use a model currently enabled for your Anthropic account.
- Claude API billing is separate from a Claude chat subscription. Check Anthropic Console billing and pricing before making API calls.
- If you use Groq instead, ask the assignment coordinator to approve it because the PDF explicitly says Claude AI in Steps 2, 4 and 6.

### C. Public influencer search

- Create a SerpAPI account and API key.
- Set `SERPAPI_API_KEY=...`.
- The search uses Google-indexed public snippets. Search engines may omit profiles, emails, locations or follower counts. Unknown fields remain unknown; verify candidates manually. This is not an exhaustive Instagram search engine.
- The Instagram Graph API is not required for the base workflow. Its Business Discovery endpoint has eligibility and permission limitations; do not assume it can search every account.

### D. Gmail API OAuth

1. In Google Cloud Console, create/select a project and enable Gmail API.
2. Configure the OAuth consent screen and create an **OAuth Client ID → Desktop app**.
3. Download the client JSON to this folder as `credentials.json`.
4. Set `SENDER_EMAIL` to the authorised Gmail address and `SENDER_NAME` / `SENDER_TITLE`.
5. Set a real `POSTAL_ADDRESS` and a test mailbox in `TEST_RECIPIENT`.
6. Keep `DEMO_MODE=true` for UI walkthroughs. For a controlled live test, set `DEMO_MODE=false`; the first Gmail action opens Google's OAuth consent flow and saves `token.json` locally.
7. All initial emails still require human approval. For safety, keep `TEST_RECIPIENT` set so outgoing mail is redirected to your own mailbox during testing.

The Gmail connector uses the Gmail API OAuth flow, not a Gmail password or app password. Google may require test-user configuration or app verification depending on the account and OAuth consent-screen status.

### E. Google Sheets (optional)

1. Enable Google Sheets API in Google Cloud.
2. Create a service account and download its JSON as `service_account.json` in this folder.
3. Share the target spreadsheet with the service-account email as Editor.
4. Set `GOOGLE_SHEET_ID` in `.env`.
5. Use the CRM tab's sync action. Excel/CSV exports work without Sheets.

## Important operating notes

- Do not use private information, automated login scraping, session-cookie scraping or access-control bypasses. Public search results can be incomplete and should be manually verified.
- The demo influencer data is synthetic and uses reserved `.test` email addresses. Never send real outreach to these addresses.
- The assignment asks for public business contact information. Only use a contact address that is clearly published for business enquiries and retain its source/provenance.
- The app includes a daily send limit and human approval for initial emails and replies. Follow-ups are automatically sent only if `AUTO_SEND_FOLLOWUPS=true`; set it to `false` to require manual follow-up approval instead.
- Set accurate sender identity and postal address before any real campaign. Review applicable anti-spam/privacy laws and platform terms for the recipient's jurisdiction.
- The app is not a guarantee of deliverability, API availability, complete influencer discovery or legal compliance. Run controlled tests first.

## Demo and submission checklist

1. Start app in default demo mode.
2. Research tab → Load synthetic demo records → Save to CRM.
3. AI Filter tab → Run AI filtering (simulated without a key; live Groq by default, or Claude if selected and configured).
4. Outreach tab → Generate initial drafts → edit one → approve and send (simulated in demo mode).
5. Replies tab → simulate an interested/pricing/not-interested/opt-out reply; inspect classification and CRM status.
6. Export tab → create Excel and CSV records.
7. For a true live demo, configure Claude, SerpAPI, Gmail OAuth and Sheets; use a controlled test mailbox and show a real search result, real response from the selected AI provider, test email, reply detection, reply draft and CRM update. If the evaluator requires Claude, select `AI_PROVIDER=claude` and configure Anthropic credentials.
8. Start `scheduler.py` in a second terminal to demonstrate unattended follow-up checks. For a timing demo, use a separate test database and shorten `FOLLOWUP1_DAYS` / `FOLLOWUP2_DAYS` only for that test.

## Files

- `app.py` — Streamlit dashboard
- `research.py` — public-web influencer search and demo data
- `ai_service.py` — Groq/Claude API calls, prompts and structured JSON handling
- `workflow.py` — CRM, outreach, follow-ups and reply workflow
- `gmail_service.py` — Gmail API OAuth, send and inbox read
- `sheets_service.py` — Google Sheets and local export
- `database.py` — SQLite storage and deduplication
- `scheduler.py` — unattended follow-up worker
- `.env.example` — configuration template
- `tests/` — automated workflow and core tests
- `submission/sample_crm.xlsx` — synthetic sample CRM workbook for the assignment
- `submission/DEMO_RECORDING_SCRIPT.md` — screen-recording walkthrough
- `submission/TEST_REPORT.md` — automated test scope and result

## Tests

```bash
python -m pytest -q
```

Automated tests cover database deduplication, follower parsing, canonical Instagram URL parsing, the demo outreach/reply flow, live-inbox opt-out handling (with Gmail mocked), and follow-up timing/stop rules. The latest packaged run is recorded in `submission/TEST_REPORT.md`. They do **not** prove live Groq, Anthropic, SerpAPI, Gmail or Google Sheets connectivity; those require account credentials and an end-to-end authorised test.
