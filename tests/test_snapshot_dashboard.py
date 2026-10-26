"""The dashboard snapshot turns the county's data into one readable line per project."""

import importlib.util

from leads import config

spec = importlib.util.spec_from_file_location("snapshot", config.PROJECT_DIR / "scripts" / "snapshot_dashboard.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def test_row_keeps_every_figure_and_marks_blanks():
    line = snapshot.row({"Project_Name": "Okatie River Park", "Project_Budget": 6827212.0,
                         "Project_Expenditures": None, "status": "In Progress", "lastUpdated": 1764637200000})
    assert "Project Name: Okatie River Park" in line
    assert "Project Budget: $6,827,212" in line
    assert "Spent to Date: not listed" in line
    assert "Last Updated: 2025-12-02" in line
