"""Save today's Beaufort County Capital Projects Dashboard as a dated project list.

The county replaced its dated project list PDFs with a live dashboard that keeps no past versions.
Running this script now and then builds that history: each run saves one dated snapshot, and Scout
compares snapshots the same way it compares the 2020-2022 project lists.

Usage:  python -I scripts/snapshot_dashboard.py
Writes: data/current/text/dashboard/project_list_<today>.txt  (what Scout reads)
        data/current/raw/dashboard/project_list_<today>.json  (the county's data, exactly as received)
"""

import json
import ssl
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parent.parent
# The data layer behind https://bcscgis.maps.arcgis.com/apps/dashboards/4f51cca9d4bf4caea48a3860b0646bfb
SERVICE = "https://services.arcgis.com/mbPLXL6SDfBjrAmS/arcgis/rest/services/Capital_Projects/FeatureServer/0"
QUERY = SERVICE + "/query?where=1%3D1&outFields=*&returnGeometry=false&orderByFields=Project_Name&f=json"
PROJECTS_PER_PAGE = 6  # keeps each page short enough for one read_section call


def day(ms) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if ms else "not listed"


def money(value) -> str:
    return f"${value:,.2f}".replace(".00", "") if value is not None else "not listed"


def row(a: dict) -> str:
    text = lambda key: " ".join((a.get(key) or "not listed").split())  # noqa: E731
    return (f"Project Name: {text('Project_Name')} | Project ID: {text('Project_ID')} | "
            f"Department: {text('Department')} | Description: {text('Description')} | "
            f"Project Budget: {money(a.get('Project_Budget'))} | Spent to Date: {money(a.get('Project_Expenditures'))} | "
            f"Project Status: {text('status')} | Phase: {text('Phase')} | Contractor: {text('Contractor')} | "
            f"Architect/Engineer: {text('Architect_Engineer')} | Projected Start: {day(a.get('projectedStartDate'))} | "
            f"Projected End: {day(a.get('projectedEndDate'))} | Last Updated: {day(a.get('lastUpdated'))} | "
            f"Latest Comment: {text('latestComment')}")


def main() -> None:
    context = ssl.create_default_context(cafile=certifi.where())  # same as the app's other downloads
    with urllib.request.urlopen(QUERY, timeout=30, context=context) as response:
        raw = response.read()
    projects = [f["attributes"] for f in json.loads(raw)["features"]]
    today = date.today().isoformat()

    raw_path = ROOT / "data" / "current" / "raw" / "dashboard" / f"project_list_{today}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)

    header = (f"BEAUFORT COUNTY CAPITAL PROJECTS DASHBOARD, saved {today} "
              f"({len(projects)} projects; source: {SERVICE})")
    pages = [projects[i:i + PROJECTS_PER_PAGE] for i in range(0, len(projects), PROJECTS_PER_PAGE)]
    text = "\n\n".join(f"=== Page {n} ===\n{header}\n" + "\n".join(row(a) for a in page)
                       for n, page in enumerate(pages, start=1)) + "\n"
    text_path = ROOT / "data" / "current" / "text" / "dashboard" / f"project_list_{today}.txt"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text, encoding="utf-8")
    print(f"Saved {len(projects)} projects to {text_path.relative_to(ROOT)} and {raw_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
