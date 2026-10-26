"""Draw Scout the alligator dressed up for each beat (assets/beats/*.svg).

Every drawing shares the same Scout (body, head, arm) and adds a costume or prop on top.

Usage:  python scripts/make_beat_art.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INK, GREEN, DARK, LIGHT = "#1F4D26", "#5FA864", "#3F8547", "#CFE8C4"

TAIL = f'<path d="M14 70 C4 70 0 62 3 55 C5 51 9 52 8 56 C7 61 12 64 20 63 Z" fill="{GREEN}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
BODY = (f'<ellipse cx="38" cy="66" rx="25" ry="16" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
        f'<path d="M19 72 Q38 84 57 72 Q40 79 19 72 Z" fill="{LIGHT}" stroke="{INK}" stroke-width="1.2"/>'
        f'<g fill="{DARK}" stroke="{INK}" stroke-width="1.2"><circle cx="26" cy="52" r="3"/><circle cx="36" cy="50" r="3.2"/>'
        f'<circle cx="46" cy="50.5" r="3"/></g>')
LEGS = (f'<path d="M24 79 q-2 8 -8 8 h9 q3 0 3 -5" fill="{GREEN}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M48 80 q-1 7 -6 7 h9 q3 0 2 -6" fill="{GREEN}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
HEAD = (f'<path d="M56 54 C60 44 74 42 78 49 L96 52 C102 53 103 58 99 60 L78 64 C70 67 59 66 56 60 Z" fill="{GREEN}" '
        f'stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
        f'<path d="M75 61 Q87 62 99 58" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<circle cx="98" cy="54" r="1" fill="{INK}"/><ellipse cx="72" cy="60" rx="3" ry="1.8" fill="#F2A7B3" opacity=".8"/>'
        f'<circle cx="68" cy="46" r="6.5" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
        f'<circle cx="68" cy="46" r="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>'
        f'<circle cx="69" cy="46.5" r="2.1" fill="#121212"/><circle cx="69.7" cy="45.8" r=".7" fill="#FFFFFF"/>')
ARM = (f'<path d="M60 66 q10 -6 14 -18" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
       f'<path d="M60 66 q10 -6 14 -18" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>')
CLAW = f'<circle cx="75" cy="45" r="3" fill="{GREEN}" stroke="{INK}" stroke-width="1.6"/>'


SIT_BODY = (f'<path d="M30 80 C14 86 6 78 12 70 C15 66 20 68 18 72 C16 76 22 78 30 75 Z" fill="{GREEN}" stroke="{INK}" '
            f'stroke-width="2" stroke-linejoin="round"/>'
            f'<ellipse cx="42" cy="64" rx="17" ry="21" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
            f'<ellipse cx="46" cy="68" rx="9" ry="14" fill="{LIGHT}" stroke="{INK}" stroke-width="1.2"/>'
            f'<path d="M30 52 Q27 60 28 70" fill="none" stroke="{DARK}" stroke-width="2.4" stroke-linecap="round" '
            f'stroke-dasharray="1 4"/>'
            f'<ellipse cx="36" cy="86" rx="6" ry="3" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
            f'<ellipse cx="51" cy="86" rx="6" ry="3" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>')


FRONT_BODY = (f'<path d="M68 80 C82 86 94 80 90 70 C88 66 84 68 85 72 C86 77 78 79 70 76 Z" fill="{GREEN}" stroke="{INK}" '
              f'stroke-width="2" stroke-linejoin="round"/>'
              f'<ellipse cx="53" cy="68" rx="21" ry="18" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<ellipse cx="53" cy="71" rx="12" ry="13" fill="{LIGHT}" stroke="{INK}" stroke-width="1.2"/>'
              f'<g stroke="{INK}" stroke-width=".8" opacity=".5"><line x1="45" y1="66" x2="61" y2="66"/>'
              f'<line x1="44" y1="71" x2="62" y2="71"/><line x1="45" y1="76" x2="61" y2="76"/></g>'
              f'<ellipse cx="43" cy="87" rx="6.5" ry="3" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<ellipse cx="63" cy="87" rx="6.5" ry="3" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<path d="M35 60 q-6 6 -4 13" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
              f'<path d="M35 60 q-6 6 -4 13" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>')
FRONT_HEAD = (f'<ellipse cx="53" cy="40" rx="21" ry="13" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<ellipse cx="53" cy="47" rx="16" ry="7" fill="{GREEN}" stroke="{INK}" stroke-width="1.6"/>'
              f'<circle cx="49" cy="44" r="1.1" fill="{INK}"/><circle cx="57" cy="44" r="1.1" fill="{INK}"/>'
              f'<path d="M42 49 Q53 56 64 49" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>'
              f'<g fill="#FFFFFF" stroke="{INK}" stroke-width=".6"><path d="M47 51.6 l1.4 2 l1.4 -1.6 Z"/>'
              f'<path d="M56 51.4 l1.4 1.8 l1.4 -2.2 Z"/></g>'
              f'<ellipse cx="37" cy="44" rx="3" ry="1.8" fill="#F2A7B3" opacity=".8"/>'
              f'<ellipse cx="69" cy="44" rx="3" ry="1.8" fill="#F2A7B3" opacity=".8"/>'
              f'<circle cx="44" cy="31" r="6.5" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<circle cx="62" cy="31" r="6.5" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>'
              f'<circle cx="44" cy="31" r="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>'
              f'<circle cx="62" cy="31" r="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>'
              f'<circle cx="45" cy="32" r="2.1" fill="#121212"/><circle cx="61" cy="32" r="2.1" fill="#121212"/>'
              f'<circle cx="45.7" cy="31.3" r=".7" fill="#FFFFFF"/><circle cx="61.7" cy="31.3" r=".7" fill="#FFFFFF"/>')
FRONT_ARM = (f'<path d="M71 62 q8 -6 9 -20" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
             f'<path d="M71 62 q8 -6 9 -20" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>')
FRONT_CLAW = f'<circle cx="80" cy="40" r="3" fill="{GREEN}" stroke="{INK}" stroke-width="1.6"/>'


def scene(behind="", over_body="", on_head="", held="", front="", arm=True, legs=True, tail=True,
          pose="right", view="0 0 106 90", hat_lift=0):
    """pose: "right" (walking right), "left" (mirror image), "sit" (sitting up), or "front" (facing the viewer)."""
    top = [on_head] + ([ARM, held, CLAW] if arm else [])
    if pose == "front":  # facing the viewer; hats and held props are moved onto the front-view head and arm
        parts = [behind, FRONT_BODY, f'<g transform="translate(8 1)">{over_body}</g>', FRONT_HEAD,
                 f'<g transform="translate(-15 {-16 - hat_lift})">{on_head}</g>']
        if arm:
            parts += [FRONT_ARM, f'<g transform="translate(5 -5)">{held}</g>', FRONT_CLAW]
        parts.append(front)
    elif pose == "sit":  # upright body, with the head and everything it wears or holds moved up onto it
        parts = [behind, SIT_BODY, over_body, f'<g transform="translate(-6 -12)">{HEAD}{"".join(top)}</g>', front]
    else:
        parts = [behind, TAIL if tail else "", BODY, LEGS if legs else "", over_body, HEAD, *top, front]
    art = "".join(parts)
    if pose == "left":
        art = f'<g transform="translate(106 0) scale(-1 1)">{art}</g>'
    w, h = (float(x) for x in view.split()[2:])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * 2:.0f}" height="{h * 2:.0f}" viewBox="{view}">'
            + art + "</svg>")


BADGE = ('<path d="M44 58 l1.6 3.4 3.7 .4 -2.8 2.5 .8 3.7 -3.3 -1.9 -3.3 1.9 .8 -3.7 -2.8 -2.5 3.7 -.4 Z" '
         'fill="#F2C230" stroke="#8A6A00" stroke-width=".8"/>')

ART = {
    "Public safety": scene(
        pose="front", view="0 -6 106 96", hat_lift=4, over_body=BADGE.replace("M44 58", "M46 60"), arm=False,
        on_head=('<path d="M57 41 Q58 31 68 30 Q79 30 80 40 Z" fill="#1F2F5A" stroke="#0D1530" stroke-width="1.6"/>'
                 '<rect x="56" y="39" width="25" height="3.4" rx="1" fill="#0D1530"/>'
                 '<path d="M55 42.5 Q68 47 83 41.5" fill="none" stroke="#0D1530" stroke-width="2.6" stroke-linecap="round"/>'
                 '<path d="M68 31.8 l1.3 2.6 2.8 .3 -2.1 1.9 .6 2.8 -2.6 -1.5 -2.6 1.5 .6 -2.8 -2.1 -1.9 2.8 -.3 Z" '
                 'fill="#F2C230" stroke="#8A6A00" stroke-width=".6"/>')),
    "Public spending": scene(
        held=('<path d="M72 22 Q66 34 74 40 Q82 44 90 40 Q98 34 90 22 Z" fill="#C9A35C" stroke="#6B4E1A" stroke-width="1.8"/>'
              '<path d="M73 22 Q81 17 89 22" fill="none" stroke="#6B4E1A" stroke-width="1.8"/>'
              '<path d="M76 19 L81 13 L86 19" fill="#C9A35C" stroke="#6B4E1A" stroke-width="1.6" stroke-linejoin="round"/>'
              '<text x="81.5" y="35.5" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="13" '
              'fill="#1F6B2E">$</text>'),
        front=('<circle cx="96" cy="76" r="4" fill="#F2C230" stroke="#8A6A00" stroke-width="1.2"/>'
               '<circle cx="88" cy="80" r="4" fill="#F2C230" stroke="#8A6A00" stroke-width="1.2"/>'
               '<text x="96" y="78" text-anchor="middle" font-size="5" font-weight="700" fill="#8A6A00">$</text>')),
    "Transportation": scene(
        pose="left", arm=False, legs=False, tail=False,
        behind='<g stroke="#B9B9B9" stroke-width="1.6" stroke-linecap="round"><line x1="0" y1="70" x2="7" y2="70"/><line x1="2" y1="76" x2="8" y2="76"/></g>',
        front=('<path d="M8 70 Q9 64 18 64 L58 64 L62 66 L90 66 Q102 67 104 74 L104 80 L8 80 Z" fill="#C8102E" '
               'stroke="#121212" stroke-width="2" stroke-linejoin="round"/>'
               '<path d="M56 64 L60 55" stroke="#121212" stroke-width="2.2" stroke-linecap="round"/>'
               '<path d="M60 55 L64 56" stroke="#121212" stroke-width="2.2" stroke-linecap="round"/>'
               '<line x1="36" y1="66" x2="36" y2="78" stroke="#7A0A1C" stroke-width="1.2"/>'
               '<rect x="97" y="70" width="6" height="3" rx="1" fill="#F7E27A" stroke="#121212" stroke-width=".8"/>'
               '<circle cx="24" cy="81" r="7" fill="#121212"/><circle cx="24" cy="81" r="2.8" fill="#C9C9C9"/>'
               '<circle cx="84" cy="81" r="7" fill="#121212"/><circle cx="84" cy="81" r="2.8" fill="#C9C9C9"/>')),
    "Education": scene(
        pose="left",
        on_head=('<path d="M54 31 L68 25 L84 31 L68 37 Z" fill="#121212" stroke="#121212" stroke-width="1"/>'
                 '<path d="M61 34 L61 39 Q68 42 76 39 L76 34" fill="#121212"/>'
                 '<path d="M68 31 L82 33 L82 41" fill="none" stroke="#F2C230" stroke-width="1.4"/>'
                 '<circle cx="82" cy="42" r="1.6" fill="#F2C230"/>'),
        held=('<g transform="rotate(-12 84 30)"><rect x="73" y="22" width="22" height="16" rx="1.5" fill="#2E5A88" '
              'stroke="#121212" stroke-width="1.6"/><rect x="75" y="24" width="18" height="12" fill="#F7F3E8"/>'
              '<line x1="84" y1="24" x2="84" y2="36" stroke="#2E5A88" stroke-width="1.4"/>'
              '<g stroke="#9A9A9A" stroke-width=".8"><line x1="76.5" y1="27" x2="82.5" y2="27"/><line x1="76.5" y1="30" x2="82.5" y2="30"/>'
              '<line x1="85.5" y1="27" x2="91.5" y2="27"/><line x1="85.5" y1="30" x2="91.5" y2="30"/></g></g>')),
    "Growth & development": scene(
        pose="left",
        on_head=('<path d="M56 41 Q57 30 68 29 Q80 30 81 41 Z" fill="#F2C230" stroke="#8A6A00" stroke-width="1.6"/>'
                 '<path d="M53 41.5 L85 41.5" stroke="#8A6A00" stroke-width="3" stroke-linecap="round"/>'
                 '<path d="M68 29.5 L68 40" stroke="#8A6A00" stroke-width="1.4"/>'),
        held=('<line x1="76" y1="44" x2="84" y2="22" stroke="#8B5A2B" stroke-width="3.2" stroke-linecap="round"/>'
              '<rect x="77" y="14" width="16" height="7" rx="1.2" fill="#6E6E6E" stroke="#121212" stroke-width="1.4" '
              'transform="rotate(20 85 18)"/>'),
        front=('<path d="M92 86 L97 70 L102 86 Z" fill="#F07F1E" stroke="#121212" stroke-width="1.4" stroke-linejoin="round"/>'
               '<path d="M94 80 L100 80" stroke="#FFFFFF" stroke-width="2"/>')),
    "Local government": scene(
        pose="sit", view="0 -14 106 104",
        behind=('<g fill="#E8E4D8" stroke="#9A9486" stroke-width="1"><path d="M2 30 L20 20 L38 30 Z"/>'
                '<rect x="4" y="30" width="32" height="3"/><rect x="7" y="33" width="3.5" height="14"/>'
                '<rect x="15" y="33" width="3.5" height="14"/><rect x="23" y="33" width="3.5" height="14"/>'
                '<rect x="31" y="33" width="3.5" height="14"/><rect x="4" y="47" width="32" height="3"/></g>'),
        held=('<line x1="76" y1="44" x2="84" y2="24" stroke="#8B5A2B" stroke-width="3" stroke-linecap="round"/>'
              '<rect x="76" y="14" width="18" height="9" rx="2.5" fill="#A0652E" stroke="#4A2A0E" stroke-width="1.6" '
              'transform="rotate(-25 85 18)"/>'
              '<g stroke="#121212" stroke-width="1.4" stroke-linecap="round"><line x1="97" y1="11" x2="101" y2="8"/>'
              '<line x1="98" y1="17" x2="103" y2="17"/></g>')),
    "Environment & climate": scene(
        held=('<line x1="76" y1="44" x2="78" y2="14" stroke="#121212" stroke-width="2" stroke-linecap="round"/>'
              '<path d="M56 18 Q78 -4 100 18 Q94 14 89 18 Q84 14 78 18 Q72 14 67 18 Q62 14 56 18 Z" fill="#2E8BC0" '
              'stroke="#0F3C57" stroke-width="1.6" stroke-linejoin="round"/>'),
        behind=('<g stroke="#5DADE2" stroke-width="1.6" stroke-linecap="round"><line x1="10" y1="10" x2="8" y2="15"/>'
                '<line x1="24" y1="4" x2="22" y2="9"/><line x1="36" y1="14" x2="34" y2="19"/><line x1="46" y1="5" x2="44" y2="10"/>'
                '<line x1="102" y1="26" x2="100" y2="31"/></g>'),
        front=('<path d="M0 84 Q8 79 16 84 T32 84 T48 84 T64 84 T80 84 T96 84 T112 84 L112 90 L0 90 Z" fill="#5DADE2" '
               'fill-opacity=".85" stroke="#2E86C1" stroke-width="1.2"/>')),
    "Housing": scene(
        pose="front",
        behind=('<g transform="translate(-80 14)">'
                '<path d="M84 50 L84 30 L95 20 L106 30 L106 50 Z" fill="#F7F3E8" stroke="#121212" stroke-width="1.6" '
                'stroke-linejoin="round"/><path d="M81 31 L95 17 L109 31" fill="none" stroke="#C8102E" stroke-width="3" '
                'stroke-linecap="round" stroke-linejoin="round"/><rect x="92" y="38" width="7" height="12" fill="#8B5A2B"/>'
                '<rect x="87" y="29" width="5" height="5" fill="#9FD3F0" stroke="#121212" stroke-width=".8"/></g>'),
        held=('<circle cx="80" cy="30" r="5" fill="none" stroke="#C9A12A" stroke-width="2.6"/>'
              '<line x1="78" y1="34.5" x2="76" y2="44" stroke="#C9A12A" stroke-width="2.6" stroke-linecap="round"/>'
              '<line x1="76.6" y1="41" x2="73.8" y2="40.6" stroke="#C9A12A" stroke-width="2"/>')),
    "Events, openings & closings": scene(
        pose="front", view="0 -16 110 106",
        on_head=('<path d="M60 41 L68 22 L77 40 Z" fill="#E94E77" stroke="#121212" stroke-width="1.4" stroke-linejoin="round"/>'
                 '<path d="M62.5 35 L74.5 34.5 M65 29 L72 28.6" stroke="#F2C230" stroke-width="2"/>'
                 '<circle cx="68" cy="21" r="2.4" fill="#F2C230" stroke="#121212" stroke-width=".8"/>'),
        held=('<path d="M75 45 Q80 34 84 24" fill="none" stroke="#555" stroke-width=".9"/>'
              '<ellipse cx="86" cy="15" rx="8" ry="10" fill="#2E8BC0" stroke="#0F3C57" stroke-width="1.4"/>'
              '<path d="M84.5 24.8 L86 22.5 L87.5 24.8 Z" fill="#2E8BC0" stroke="#0F3C57" stroke-width=".8"/>'
              '<ellipse cx="83" cy="11" rx="2" ry="3" fill="#FFFFFF" opacity=".6"/>'),
        behind=('<g><rect x="12" y="20" width="3" height="3" fill="#E94E77" transform="rotate(20 13 21)"/>'
                '<rect x="30" y="12" width="3" height="3" fill="#F2C230" transform="rotate(-15 31 13)"/>'
                '<rect x="46" y="24" width="3" height="3" fill="#2E8BC0" transform="rotate(30 47 25)"/>'
                '<circle cx="22" cy="34" r="1.6" fill="#5FA864"/><circle cx="102" cy="40" r="1.6" fill="#E94E77"/>'
                '<rect x="98" y="30" width="3" height="3" fill="#F2C230" transform="rotate(10 99 31)"/></g>')),
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    out = ROOT / "assets" / "beats"
    out.mkdir(parents=True, exist_ok=True)
    for beat, svg in ART.items():
        (out / f"{slug(beat)}.svg").write_text(svg, encoding="utf-8")
        print(out / f"{slug(beat)}.svg")


if __name__ == "__main__":
    main()
