# Live demonstration recording script (7–10 minutes)

> Use synthetic demo records for a safe UI walkthrough. The assignment explicitly names Claude; if demonstrating Groq instead, disclose it and confirm the coordinator accepts this alternative. To prove live integrations, separately show a real SerpAPI search result, a real response from the selected provider and a Gmail test sent to your own test mailbox. Do not describe simulated data as live data.

1. **Introduction (30 sec):** State the objective and explain that the app uses public search-index results only, the selected LLM provider for analysis, SQLite/Google Sheets for CRM, and Gmail for outreach.
2. **Campaign setup (45 sec):** Configure brand, campaign niche, location, offer and sender identity. Save and restart if `.env` values were changed.
3. **Research (1–2 min):** Search for a niche/location, show Instagram profile URLs and provenance. Explain that missing follower counts/emails remain blank for verification. Load synthetic data only if a live search key is unavailable.
4. **AI analysis (1 min):** Run AI filtering. If using live mode, show the actual Claude response and score. If demo mode, clearly state the results are synthetic.
5. **CRM (45 sec):** Show statuses and duplicate prevention by saving the same username again. Sync to Google Sheets if configured; otherwise show SQLite-backed CRM and local exports.
6. **Initial outreach (1 min):** Generate personalised email drafts, open one, review/edit it, approve it and send only to the configured test mailbox. Show sender identity and opt-out text.
7. **Reply management (1–2 min):** For a live test, reply from the test mailbox and check the Gmail inbox. Show classification, suggested action, reply draft and human approval. In demo mode, use the reply simulator and label it simulated.
8. **Follow-ups (1 min):** Show scheduler configuration (4 days + 6 days) and run `run_scheduler.bat` in a second terminal. For a controlled timing demonstration, use a separate test database and temporary shorter intervals; restore production intervals afterwards. Show that replies/declines/opt-outs suppress follow-ups.
9. **Export and close (30 sec):** Export the Excel workbook/CSV and summarise the full flow.

## Before recording

- [ ] `.env` configured with the services you intend to demonstrate.
- [ ] `TEST_RECIPIENT` set to your own mailbox for live Gmail tests.
- [ ] Sender name, sender email, title and postal address are accurate.
- [ ] Test records are clearly labelled synthetic.
- [ ] Follow-up scheduler is running in a second terminal if demonstrating unattended scheduling.
- [ ] No API keys, OAuth token files or personal credentials visible in the recording.
