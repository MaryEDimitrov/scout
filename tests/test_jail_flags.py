"""The newsroom's arrest list is applied to jail logs in plain code."""

from leads import config
from leads.documents import DocumentStore
from leads.jail import flag_bookings
from leads.uploads import build_collection

ROSTER = config.PROJECT_DIR / "test_fixtures" / "uploads" / "sample_jail_roster.html"


def store_with(lines, tmp_path):
    log = "\n".join(f"Booking {i} | Name: PERSON {chr(65 + i)} | Booked: 10/25/2026 | Released: not released | "
                    f"Arresting agency: Sheriff | Charges: {c}" for i, c in enumerate(lines))
    text_dir, _ = build_collection([("jail_log.txt", log.encode())], base_dir=config.FIXTURE_DATA_DIR,
                                   uploads_root=tmp_path)
    return DocumentStore(text_dir)


def test_serious_charges_are_flagged_and_routine_ones_are_not(tmp_path):
    store = store_with(["DOMESTIC VIOLENCE 2ND DEGREE (16-25-0020)", "SHOPLIFTING (16-13-0110)",
                        "DRIVING UNDER THE INFLUENCE (56-05-2930)", "CHILD ENDANGERMENT (56-05-2947)",
                        "FAILURE TO STOP FOR A BLUE LIGHT (56-05-0750)", "POSS. OF 28G OR MORE OF COCAINE (44-53-0370)",
                        "POSS. OF 28G OR LESS OF MARIJUANA (44-53-0370)"],
                       tmp_path)
    candidates, summary = flag_bookings(store)
    assert summary["bookings_checked"] == 7 and summary["flagged"] == 3  # "28G or less" is not trafficking
    flagged = {c["project"] for c in candidates}
    # shoplifting, DUI, and failure to stop for a blue light stay out
    assert not flagged & {"PERSON B", "PERSON C", "PERSON E"}


def test_ice_holds_are_a_pattern_never_a_name(tmp_path):
    candidates, summary = flag_bookings(store_with(["ICE Hold (ICE)", "ICE Hold (ICE)", "LITTERING (16-11-0700)"],
                                                   tmp_path))
    assert summary["ice_holds"] == 2
    pattern = [c for c in candidates if c["project"] == "ICE holds"]
    assert len(pattern) == 1 and "PERSON" not in str(pattern[0]["pointers"])


def test_name_in_public_records_is_flagged_as_unconfirmed(tmp_path):
    text_dir, _ = build_collection([(ROSTER.name, ROSTER.read_bytes())], base_dir=config.FIXTURE_DATA_DIR,
                                   uploads_root=tmp_path)
    candidates, _ = flag_bookings(DocumentStore(text_dir))
    match = [c for c in candidates if c["project"] == "LUIS ORTEGA"][0]
    assert "identity not confirmed" in match["what_caught_my_eye"]
