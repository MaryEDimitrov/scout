# Test fixtures (SYNTHETIC — not real records)

Everything in this folder is **made up** for testing. The real Beaufort County records are in `../data/`.

- `text/` — a small fake collection for "Port Harlow County" (3 tracker snapshots, 4 sets of minutes)
- `answer_key.json` — what the app should find:
  - **3 planted leads** (F1–F3), modeled on the kinds of leads found in the real data
  - **3 decoys** (D1–D3) that look suspicious but are explained by the documents or are too small
  - **1 prompt injection** hidden in `text/council/2023-05-15_pubfac_minutes.txt`

Used by `scripts/evaluate.py`, `scripts/test_injection_live.py`, and `scripts/cost_experiment.py`.
In the app, turn on **Options → Use synthetic test documents** to run on this collection.

## Sample jail log (synthetic)

`uploads/sample_jail_log_2023-06-02.txt` is a made-up booking log for the made-up Port Harlow County.
Use it **only with the synthetic collection**: turn on *Options → Use synthetic test documents*, then drag
the file into *Add your own meeting minutes*. It tests arrest-record leads:
- "Thomas Pruitt" shares a surname with Council Member Pruitt in the synthetic minutes (identity not confirmed)
- "Darnell Hughes" lists his employer as Coastal Asphalt, the county's paving contractor in the synthetic minutes
- the other two bookings are routine

`uploads/sample_jail_roster.html` copies the **layout** of a saved Beaufort County inmate-inquiry page
with **fictional people**. It includes fake addresses, birth dates, race, height, and weight so tests can
prove the app removes them. "Luis Ortega" shares a full name with the fictional Vice Chair in the synthetic minutes.
