# Data sources

All files in `data/` are **real, unaltered public records** from Beaufort County, South Carolina.
Synthetic or altered test documents live only in `test_fixtures/`.

- `data/pdfs/` — original PDFs exactly as downloaded
- `data/text/` — plain text the app reads (pdfplumber 0.11.4):
  - Council records: `scripts/extract_text.py` (plain page text)
  - Trackers: `scripts/extract_trackers.py`, which rebuilds each table row as one line
    (`Project Name: … | Description: … | Project Cost: … | Funding Source: … | Project Status: …`).
    Every word comes from the PDF; only the layout changes, so columns no longer mix.

## Capital project trackers (Beaufort County Engineering, Capital Improvement Projects)

Downloaded 2026-10-24. File names use the "Updated" date printed on each tracker.

| File | "Updated" date on document | Source URL |
|---|---|---|
| tracker_2020-12-04.pdf | December 4, 2020 | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2020/Project%20Tracker%20120420.pdf |
| tracker_2021-01-08.pdf | January 8, 2021 (URL has no date) | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2021/_Project%20Tracker%20Webpage%20Template.pdf |
| tracker_2021-02-05.pdf | February 5, 2021 | https://beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2021/_Project%20Tracker%20Webpage%20Template%20020521.pdf |
| tracker_2021-03-05.pdf | March 5, 2021 | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2021/_Project%20Tracker%20Webpage%20Template%20030521.pdf |
| tracker_2021-05-10.pdf | May 10, 2021 | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2021/_Project%20Tracker%20Webpage%20Template%20051021.pdf |
| tracker_2021-11-05.pdf | November 5, 2021 | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2021/_Project%20Tracker%20Webpage%20Template%20110521.pdf |
| tracker_2022-04-01.pdf | April 1, 2022 | https://www.beaufortcountysc.gov/engineering/Capital%20Improvement%20Projects/2022/_Project%20Tracker%20Webpage%20Template%20040122.pdf |

**Not yet obtained:** June 4, 2021 tracker
(`.../2021/_Project%20Tracker%20Webpage%20Template%20060421.pdf`). The county server
returned an empty (0-byte) file on 2026-10-24, with and without `www.`.

The June 4, 2021 tracker is expected to be saved by hand from a browser (see README).

## County Council and committee records

Downloaded 2026-10-24 from Beaufort County's CivicClerk portal
(https://beaufortcosc.portal.civicclerk.com/), which the county's meetings index
(https://beaufortcountysc.gov/council/council-committee-meetings/index.html) links to for current meetings.
File names: `<meeting date>_<body>_<document type>_<CivicClerk event id>.pdf`.
Bodies: `council` = County Council, `pubfac` = Public Facilities Committee,
`finance` = Finance, Administration, and Economic Development Committee, `exec` = Executive Committee.

**Packet excerpts** (`data/pdfs/packet_excerpts/`) contain only the listed pages of the full backup packet,
copied without alteration. Full packets are 6–22 MB each, so we ship only the pages that matter.
In the extracted text, page numbers restart at 1 within each excerpt.

**Coverage gap:** Council records from April to November 2020 are not posted on CivicClerk
or on the county's older archive (which ends in March 2020). Searches of the collection
cannot confirm or rule out approvals from that period.

| File | Meeting | Source URL |
|---|---|---|
| 2020-12-14_council_minutes_581.pdf | County Council Meeting, 2020-12-14 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1386,plainText=false) |
| 2020-12-21_pubfac_minutes_142.pdf | Public Facilities, 2020-12-21 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=294,plainText=false) |
| 2021-01-11_council_minutes_549.pdf | County Council Meeting, 2021-01-11 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1297,plainText=false) |
| 2021-01-19_pubfac_minutes_113.pdf | Public Facilities Committee, 2021-01-19 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=217,plainText=false) |
| 2021-02-16_pubfac_minutes_128.pdf | Public Facilities Committee, 2021-02-16 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=255,plainText=false) |
| 2021-02-22_council_minutes_433.pdf | County Council Meeting, 2021-02-22 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1011,plainText=false) |
| 2021-04-19_pubfac_minutes_121.pdf | Public Facilities Committee, 2021-04-19 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=240,plainText=false) |
| 2021-04-26_council_minutes_572.pdf | County Council Meeting, 2021-04-26 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1362,plainText=false) |
| 2021-05-17_pubfac_minutes_146.pdf | Public Facilities Committee, 2021-05-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=306,plainText=false) |
| 2021-06-21_pubfac_minutes_117.pdf | Public Facilities Committee, 2021-06-21 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=228,plainText=false) |
| 2021-10-18_pubfac_minutes_118.pdf | Public Facilities Committee, 2021-10-18 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=231,plainText=false) |
| 2022-01-18_pubfac_minutes_87.pdf | Public Facilities Committee, 2022-01-18 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=142,plainText=false) |
| 2022-01-24_council_minutes_453.pdf | County Council Meeting, 2022-01-24 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1061,plainText=false) |
| 2022-02-07_exec_minutes_293.pdf | Executive Committee, 2022-02-07 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=649,plainText=false) |
| 2022-02-28_council_agenda_473.pdf | County Council Meeting, 2022-02-28 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1106,plainText=false) |
| 2022-02-28_council_minutes_473.pdf | County Council Meeting, 2022-02-28 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1108,plainText=false) |
| 2022-03-21_finance_minutes_360.pdf | Finance Committee, 2022-03-21 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=821,plainText=false) |
| 2021-01-19_pubfac_packet_113_p56-58.pdf | Public Facilities Committee, 2021-01-19 (pages 56-58 of the full packet) | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=216,plainText=false) |
| 2022-01-18_pubfac_packet_87_p8.pdf | Public Facilities Committee, 2022-01-18 (pages 8 of the full packet) | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=141,plainText=false) |
| 2022-03-21_finance_packet_360_p22-25.pdf | Finance Committee, 2022-03-21 (pages 22-25 of the full packet) | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=820,plainText=false) |

## Optional document sets (real records; added only when a reporter clicks "Add these")

Downloaded 2026-10-25. Stored in `data/samples/<set>/pdfs/` (originals) and `data/samples/<set>/text/`.

### Hilton Head Island Town Council minutes (Nov 2025 – Sep 2026)

From the Town of Hilton Head Island's CivicClerk portal (https://hiltonheadsc.portal.civicclerk.com/),
linked from https://hiltonheadislandsc.gov/government/town_council/agendas_minutes.php.
The October 2025 minutes (Oct 7, 13, 21) were left out: they are scanned images with no text.

| File | Source URL |
|---|---|
| 2025-11-04_hhi-town-council_regular_minutes_657.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1551,plainText=false) |
| 2025-12-09_hhi-town-council_regular_minutes_658.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1652,plainText=false) |
| 2025-12-18_hhi-town-council_special_minutes_1273.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1653,plainText=false) |
| 2026-01-13_hhi-town-council_regular_minutes_1072.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1654,plainText=false) |
| 2026-02-10_hhi-town-council_regular_minutes_1073.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1708,plainText=false) |
| 2026-02-24_hhi-town-council_workshop_minutes_1085.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1710,plainText=false) |
| 2026-03-10_hhi-town-council_regular_minutes_1074.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1775,plainText=false) |
| 2026-03-26_hhi-town-council_special_minutes_1302.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1776,plainText=false) |
| 2026-03-31_hhi-town-council_special_minutes_1086.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1871,plainText=false) |
| 2026-04-07_hhi-town-council_regular_minutes_1075.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1870,plainText=false) |
| 2026-04-28_hhi-town-council_workshop_minutes_1087.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1869,plainText=false) |
| 2026-05-05_hhi-town-council_special_minutes_1303.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1866,plainText=false) |
| 2026-05-12_hhi-town-council_regular_minutes_1076.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1867,plainText=false) |
| 2026-05-13_hhi-town-council_special_minutes_1316.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1868,plainText=false) |
| 2026-05-14_hhi-town-council_budget-workshop_minutes_1219.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1930,plainText=false) |
| 2026-05-19_hhi-town-council_budget-workshop_minutes_1220.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1931,plainText=false) |
| 2026-06-09_hhi-town-council_regular_minutes_1077.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1932,plainText=false) |
| 2026-07-14_hhi-town-council_regular_minutes_1078.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1965,plainText=false) |
| 2026-07-28_hhi-town-council_workshop_minutes_1090.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=2032,plainText=false) |
| 2026-08-11_hhi-town-council_regular_minutes_1079.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=2033,plainText=false) |
| 2026-09-15_hhi-town-council_regular_minutes_1080.pdf | https://hiltonheadsc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=2066,plainText=false) |

### Beaufort County School District board agendas (Oct 2025 – Oct 2026)

From the district's Diligent Community portal, linked from
https://www.beaufortschools.net/about-us/board-of-ed/board-meetings. The portal posts each regular
meeting's agenda and agenda packet but no separate minutes, so the agendas are used.

| File | Meeting page |
|---|---|
| 2025-10-07_school-board_regular_agenda_966.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=966 |
| 2025-10-21_school-board_regular_agenda_973.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=973 |
| 2025-11-04_school-board_regular_agenda_976.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=976 |
| 2025-12-09_school-board_regular_agenda_988.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=988 |
| 2026-01-06_school-board_regular_agenda_990.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=990 |
| 2026-02-03_school-board_regular_agenda_993.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=993 |
| 2026-02-17_school-board_regular_agenda_997.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=997 |
| 2026-03-03_school-board_regular_agenda_998.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=998 |
| 2026-04-07_school-board_regular_agenda_1006.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1006 |
| 2026-05-05_school-board_regular_agenda_1010.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1010 |
| 2026-05-19_school-board_regular_agenda_1013.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1013 |
| 2026-06-09_school-board_regular_agenda_1015.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1015 |
| 2026-06-23_school-board_regular_agenda_1017.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1017 |
| 2026-07-14_school-board_regular_agenda_1019.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1019 |
| 2026-08-04_school-board_regular_agenda_1021.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1021 |
| 2026-09-01_school-board_regular_agenda_1026.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1026 |
| 2026-09-15_school-board_regular_agenda_1033.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1033 |
| 2026-10-06_school-board_regular_agenda_1039.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1039 |
| 2026-10-20_school-board_regular_agenda_1045.pdf | https://beaufortcountyschooldistrict.community.diligentoneplatform.com/Portal/MeetingInformation.aspx?Org=Cal&Id=1045 |

### Beaufort County Council and committee minutes (Oct 2025 – Oct 2026): the built-in collection

Since 2026-10-25 these are the records Scout always searches. Stored in `data/current/pdfs/county_recent/`
(originals) and `data/current/text/county_recent/`. The December 2020 – April 2022 records above are now an
optional one-click archive.

From the county's CivicClerk portal (https://beaufortcosc.portal.civicclerk.com/). All meetings with
posted minutes except Caucus meetings (mostly closed-session notices).

| File | Meeting | Source URL |
|---|---|---|
| 2025-10-27_council_minutes_588.pdf | County Council Meeting, 2025-10-27 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6572,plainText=false) |
| 2025-11-03_commsvc_minutes_228.pdf | Community Services Committee, 2025-11-03 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4357,plainText=false) |
| 2025-11-03_natres_minutes_21.pdf | Natural Resources Committee Meeting, 2025-11-03 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4358,plainText=false) |
| 2025-11-10_council_minutes_525.pdf | County Council Meeting, 2025-11-10 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6573,plainText=false) |
| 2025-11-17_exec_minutes_1543.pdf | Executive Committee Meeting, 2025-11-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4320,plainText=false) |
| 2025-11-17_finance_minutes_9.pdf | Finance, Administration and Economic Development Committee Meeting, 2025-11-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4327,plainText=false) |
| 2025-11-17_pubfac_minutes_1456.pdf | Public Facilities Committee Meeting, 2025-11-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4328,plainText=false) |
| 2025-12-08_council_minutes_35.pdf | County Council Meeting, 2025-12-08 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6584,plainText=false) |
| 2026-01-12_council_minutes_1544.pdf | County Council Meeting, 2026-01-12 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4339,plainText=false) |
| 2026-01-12_exec_minutes_2563.pdf | Executive Committee, 2026-01-12 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4377,plainText=false) |
| 2026-01-20_council_minutes_2606.pdf | Special Called County Council Meeting, 2026-01-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7648,plainText=false) |
| 2026-01-20_exec_minutes_2605.pdf | Special Called Executive Committee Meeting, 2026-01-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4378,plainText=false) |
| 2026-01-20_finance_minutes_2576.pdf | Finance, Administration, and Economic Development Committee, 2026-01-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7621,plainText=false) |
| 2026-01-20_pubfac_minutes_2586.pdf | Public Facilities Committee, 2026-01-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7622,plainText=false) |
| 2026-01-26_council_minutes_1571.pdf | County Council Meeting, 2026-01-26 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7619,plainText=false) |
| 2026-01-26_exec_minutes_2607.pdf | Special Called Executive Committee Meeting, 2026-01-26 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4379,plainText=false) |
| 2026-02-03_commsvc_minutes_2596.pdf | Community Services and Public Safety Committee, 2026-02-03 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6434,plainText=false) |
| 2026-02-03_natres_minutes_2567.pdf | Natural Resources Committee, 2026-02-03 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6449,plainText=false) |
| 2026-02-09_council_minutes_2545.pdf | County Council Meeting, 2026-02-09 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6383,plainText=false) |
| 2026-02-09_exec_minutes_2608.pdf | Special Called Executive Committee Meeting, 2026-02-09 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6476,plainText=false) |
| 2026-02-17_finance_minutes_2577.pdf | Finance, Administration, and Economic Development Committee, 2026-02-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6424,plainText=false) |
| 2026-02-17_pubfac_minutes_2587.pdf | Public Facilities Committee, 2026-02-17 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6425,plainText=false) |
| 2026-02-23_council_minutes_2546.pdf | County Council Meeting, 2026-02-23 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6415,plainText=false) |
| 2026-02-23_exec_minutes_2609.pdf | Special Called Executive Committee, 2026-02-23 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6477,plainText=false) |
| 2026-03-02_commsvc_minutes_2597.pdf | Community Services and Public Safety Committee, 2026-03-02 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6450,plainText=false) |
| 2026-03-09_commsvc_minutes_2547.pdf | County Council Meeting, 2026-03-09 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6436,plainText=false) |
| 2026-03-10_council_minutes_2610.pdf | County Council Workshop, 2026-03-10 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6480,plainText=false) |
| 2026-03-16_finance_minutes_2578.pdf | Finance, Administration, and Economic Development Committee, 2026-03-16 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6492,plainText=false) |
| 2026-03-16_pubfac_minutes_2588.pdf | Public Facilities Committee, 2026-03-16 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6493,plainText=false) |
| 2026-03-23_council_minutes_2548.pdf | County Council Meeting, 2026-03-23 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6479,plainText=false) |
| 2026-04-06_commsvc_minutes_2598.pdf | Community Services and Public Safety Committee, 2026-04-06 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6519,plainText=false) |
| 2026-04-06_natres_minutes_2569.pdf | Natural Resources Committee, 2026-04-06 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6520,plainText=false) |
| 2026-04-09_council_minutes_2612.pdf | County Council Budget Workshop, 2026-04-09 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6505,plainText=false) |
| 2026-04-13_council_minutes_2549.pdf | County Council Meeting, 2026-04-13 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6506,plainText=false) |
| 2026-04-13_exec_minutes_2564.pdf | Executive Committee, 2026-04-13 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7642,plainText=false) |
| 2026-04-20_finance_minutes_2579.pdf | Finance, Administration, and Economic Development Committee, 2026-04-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6554,plainText=false) |
| 2026-04-20_general_minutes_2613.pdf | County Council Budget Workshop, 2026-04-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6558,plainText=false) |
| 2026-04-20_pubfac_minutes_2589.pdf | Public Facilities Committee, 2026-04-20 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6556,plainText=false) |
| 2026-04-27_council_minutes_2550.pdf | County Council Meeting, 2026-04-27 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6559,plainText=false) |
| 2026-05-04_commsvc_minutes_2599.pdf | Community Services and Public Safety Committee, 2026-05-04 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7656,plainText=false) |
| 2026-05-04_natres_minutes_2570.pdf | Natural Resources Committee, 2026-05-04 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7657,plainText=false) |
| 2026-05-11_council_minutes_2551.pdf | County Council Meeting, 2026-05-11 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6566,plainText=false) |
| 2026-05-18_finance_minutes_2580.pdf | Finance, Administration, and Economic Development Committee, 2026-05-18 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7602,plainText=false) |
| 2026-05-18_pubfac_minutes_2590.pdf | Public Facilities Committee, 2026-05-18 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7603,plainText=false) |
| 2026-05-19_council_minutes_2616.pdf | Special Called County Council Meeting, 2026-05-19 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7647,plainText=false) |
| 2026-05-26_council_minutes_2552.pdf | County Council Meeting, 2026-05-26 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6592,plainText=false) |
| 2026-05-28_exec_minutes_2618.pdf | Special Called Executive Committee Meeting, 2026-05-28 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7643,plainText=false) |
| 2026-06-01_council_minutes_2619.pdf | Special Called County Council Meeting, 2026-06-01 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=6591,plainText=false) |
| 2026-06-08_council_minutes_2553.pdf | County Council Meeting, 2026-06-08 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7617,plainText=false) |
| 2026-06-08_council_minutes_2617.pdf | County Council Workshop, 2026-06-08 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7618,plainText=false) |
| 2026-06-15_finance_minutes_2581.pdf | Finance, Administration, and Economic Development Committee, 2026-06-15 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8669,plainText=false) |
| 2026-06-15_natres_minutes_2620.pdf | Special Called Natural Resources Committee Meeting, 2026-06-15 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7658,plainText=false) |
| 2026-06-15_pubfac_minutes_2591.pdf | Public Facilities Committee, 2026-06-15 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8668,plainText=false) |
| 2026-06-22_council_minutes_2554.pdf | County Council Meeting, 2026-06-22 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7646,plainText=false) |
| 2026-06-30_exec_minutes_3620.pdf | Special Called Executive Committee Meeting, 2026-06-30 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7644,plainText=false) |
| 2026-07-13_council_minutes_2555.pdf | County Council Meeting, 2026-07-13 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=7665,plainText=false) |
| 2026-08-03_natres_minutes_2572.pdf | Natural Resources Committee, 2026-08-03 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8699,plainText=false) |
| 2026-08-10_council_minutes_2556.pdf | County Council Meeting, 2026-08-10 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8700,plainText=false) |
| 2026-08-28_council_minutes_3621.pdf | County Council Workshop, 2026-08-28 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8717,plainText=false) |
| 2026-09-14_council_minutes_2557.pdf | County Council Meeting, 2026-09-14 | https://beaufortcosc.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=8737,plainText=false) |

## Official contacts (`data/contacts.json`)

Public officials and offices only, copied on 2026-10-25 from: the Beaufort County Council member pages
(https://www.beaufortcountysc.gov/council/council-members/), the county Public Information page and
Administration page, the Town of Hilton Head Island Town Council page
(https://hiltonheadislandsc.gov/government/town_council/index.php), the Town of Port Royal Town Council page
(https://www.portroyal.org/171/Town-Council), and the Beaufort County School District site. The Sheriff's
Office site blocks automated access and the Solicitor's site lists no office line, so those two are links only.
Each entry in the file keeps its own source link.

## Current project lists (built-in collection)

### Capital Projects Dashboard snapshots

The county's live dashboard (https://bcscgis.maps.arcgis.com/apps/dashboards/4f51cca9d4bf4caea48a3860b0646bfb,
linked from https://www.beaufortcountysc.gov/capital-projects-management/) keeps no past versions.
`scripts/snapshot_dashboard.py` saves its data layer
(https://services.arcgis.com/mbPLXL6SDfBjrAmS/arcgis/rest/services/Capital_Projects/FeatureServer/0) as a dated list:
`data/current/text/dashboard/project_list_<date>.txt`, with the county's raw data in `data/current/raw/dashboard/`.
First snapshot: 2026-10-25 (24 projects; the county last edited the data in March 2026).

### Capital Improvement Plan, fiscal years 2025–2026

https://www.beaufortcountysc.gov/capital-projects-management/FY%202025%20CIP%20Plan.pdf (downloaded 2026-10-25,
307 pages, 116 MB). Only the text of pages 7–29 (project lists and summary tables) is shipped, in
`data/current/text/cip_plans/cip_fy2025-2026_p7-29.txt`; page N there is page N+6 of the original. The PDF is too
large for GitHub, even cut down to those pages. A FY 2023 plan is also linked from the county page, but the
file it serves is empty (0 bytes, checked 2026-10-25).
