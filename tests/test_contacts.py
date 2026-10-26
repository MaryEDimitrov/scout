"""Who to contact: officials named in a lead, matched to official contact info; never private people."""

from leads.contacts import contacts_for, directory


def card(quote, lead_type="Worth a closer look", file="2022-03-21_finance_minutes_360.pdf"):
    return {"title": "A lead", "lead": "", "lead_type": lead_type, "evidence": [{"quote": quote, "file": file}]}


def test_official_named_by_title_and_last_name_is_found():
    found = contacts_for(card("Committee Chairman Lawson asked about the overage"), "Local government")
    assert [p["name"] for p in found["people"]] == ["Mark Lawson"]
    assert found["people"][0]["email"].endswith("@bcgov.net") and found["people"][0]["source"].startswith("https://")


def test_hilton_head_minutes_resolve_shared_surname_to_the_town_official():
    found = contacts_for(card("Ms. Becker moved to approve the amended Agenda. Mr. Alfred seconded.",
                              file="2026-09-15_hhi-town-council_regular_minutes_1080.pdf"), "Local government")
    assert sorted(p["name"] for p in found["people"]) == ["Steve Alfred", "Tamara Becker"]


def test_arrest_record_never_gets_personal_contacts():
    official = directory()["people"][0]["name"]
    found = contacts_for(card(f"Booking 1 | Name: {official} | Charges: ASSAULT", lead_type="Arrest record"),
                         "Public safety")
    assert found["people"] == []
    assert [o["name"] for o in found["offices"]][:2] == ["Beaufort County Sheriff's Office", "14th Circuit Solicitor's Office"]


def test_every_contact_has_an_official_source():
    data = directory()
    for entry in data["people"] + list(data["offices"].values()):
        assert entry["source"].startswith("https://") and (".gov" in entry["source"] or ".org" in entry["source"]
                                                          or ".net" in entry["source"])
