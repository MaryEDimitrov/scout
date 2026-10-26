"""Build docs/slides.html: a self-contained reveal.js deck (screenshots and drawings embedded).

Usage:  python scripts/build_slides.py
Edit the three settings below, then rebuild.
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = Path(__file__).resolve().parent.parent / "docs" / "screenshots"

# ---- settings to fill in -------------------------------------------------------------------------
REPO_URL = "https://github.com/MaryEDimitrov/scout"  # e.g. "https://github.com/your-username/scout" (required by the professor)
REPO_PRIVATE = False   # True if the repo is private (then add GitHub user zlisto as a collaborator)
USER_TEST = ""         # e.g. "By hand: 0 of 5 leads in 20 min · With Scout: 3 leads in 2 min" (after colleagues test)
USER_QUOTE = ""        # e.g. '"I would use this every week." (former colleague, The Island Packet)'
# ---------------------------------------------------------------------------------------------------


def data_uri(path: Path) -> str:
    kind = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    return f"data:{kind};base64,{base64.b64encode(path.read_bytes()).decode()}"


def art(name: str) -> str:
    return data_uri(ROOT / "assets" / name)


def shot(name: str) -> str:
    return data_uri(SHOTS / name)


def todo(text: str) -> str:
    return f'<span class="todo">{text}</span>'


repo = (f'<a href="{REPO_URL}">{REPO_URL}</a>' if REPO_URL else todo("ADD GITHUB REPO URL"))
private = ' <span class="small">(private repo; grader access via GitHub user <b>zlisto</b>)</span>' if REPO_PRIVATE else ""
user_test = USER_TEST or todo("ADD: time by hand vs. with Scout, from colleague tests")
user_quote = USER_QUOTE or todo("ADD: a colleague's quote")

SLIDES = f"""
<section class="title">
  <div class="topline">Beaufort County, S.C. · Public Records Desk</div>
  <div class="brand"><img src="{art('scout_gator.svg')}" class="gator-big" alt="Scout"><h1>Scout</h1></div>
  <p class="pitch">I spent years digging through county records for stories. Scout does the digging,
  so reporters can get back to reporting.</p>
  <p class="byline">Mary Dimitrov · Former local government reporter, now at Yale SOM · MGT 409 AI Foundations</p>
  <p class="repo">Code: {repo}{private}</p>
</section>

<section>
  <div class="kicker">The problem</div>
  <h2>The stories are buried in public records. Newsrooms don't have the hours to dig.</h2>
  <div class="cols">
    <div>
      <ul>
        <li>When I covered local government, the best stories never came from press releases. They came from
            a number that didn't match between two documents.</li>
        <li>In Beaufort County, those documents live on <b>six different websites</b>: project lists, Council
            minutes, school board agendas, two town calendars and the jail roster.</li>
        <li>One lead Scout found: a <b>$900,000 building overage</b> the Finance Committee chairman said Council
            had never heard about. Spotting it means lining up three documents from two systems.</li>
      </ul>
      <p class="who">Who has this problem: every local reporter with too many meetings and not enough hours.
      I was one of them.</p>
    </div>
    <img src="{art('beats/local-government.svg')}" class="scout-side" alt="">
  </div>
</section>

<section>
  <div class="kicker">What's new</div>
  <h2>Most tools wait for the right question. Scout goes looking.</h2>
  <table class="compare">
    <tr><th></th><th>Google Pinpoint, DocumentCloud</th><th>ChatGPT, NotebookLM</th><th class="us">Scout</th></tr>
    <tr><td>Finds stories without being asked</td><td>No: you search</td><td>No: you ask</td><td class="us">Yes</td></tr>
    <tr><td>Compares versions and checks approvals</td><td>No</td><td>Only if asked</td><td class="us">Yes</td></tr>
    <tr><td>Tries to knock down its own leads</td><td>No</td><td>No</td><td class="us">Yes, a Skeptic agent</td></tr>
    <tr><td>Every quote checked word for word</td><td>n/a</td><td>No, can invent</td><td class="us">Yes, in code</td></tr>
    <tr><td>Ranks by news value, checks local coverage</td><td>No</td><td>No</td><td class="us">Yes</td></tr>
  </table>
  <p>Reporters don't need another chatbot. They need a second set of eyes that brings receipts.</p>
  <div class="corner"><img src="{art('scout_newspaper.svg')}" alt=""></div>
</section>

<section>
  <div class="kicker">How the agents work</div>
  <h2>It works like a newsroom, and the copy desk is code</h2>
  <div class="flow">
    <div class="step"><div class="tag">Reporter</div><b>Picks a beat</b><span>adds this week's minutes, a jail log or event calendars</span></div>
    <div class="arrow">→</div>
    <div class="step"><img src="{art('scout_gator.svg')}" alt=""><b>Scout</b><span>lists, searches and reads the records<br>pitches possible stories</span></div>
    <div class="arrow">→</div>
    <div class="step"><img src="{art('scout_newspaper.svg')}" alt=""><b>Connector</b><span>looks up each project, compares figures<br>builds the evidence</span></div>
    <div class="arrow">→</div>
    <div class="step"><img src="{art('scout_x.svg')}" alt=""><b>Skeptic</b><span>pulls the exact passages<br>tries to kill each lead</span></div>
    <div class="arrow">→</div>
    <div class="step code"><div class="tag">Plain code</div><b>Copy desk</b><span>checks every quote word for word, enforces the rules, blocks accusations</span></div>
  </div>
  <p class="note">A reporter finds it, an editor connects it, a skeptic tries to kill it, and nothing runs without the
  quotes checking out. Every dismissed lead is logged with the reason. Model: gpt-6-luna on the course key.</p>
</section>

<section>
  <div class="kicker">Demo</div>
  <h2>Pick a beat. Get leads you can actually report.</h2>
  <div class="shots two">
    <figure><img src="{shot('s_beats.png')}" alt="Beat picker"><figcaption>Choose a beat. (Scout dresses for each one.)</figcaption></figure>
    <figure><img src="{shot('s_card.png')}" alt="A lead card"><figcaption>A real lead from county records: the quotes, why it matters, and who to call</figcaption></figure>
  </div>
</section>

<section>
  <div class="kicker">Demo</div>
  <h2>Built for how I used to work</h2>
  <div class="shots two">
    <figure><img src="{shot('s_docs.png')}" alt="Add documents"><figcaption>Drop in this week's minutes or school board agendas, or pull today's jail log in one click</figcaption></figure>
    <figure><img src="{shot('s_sections.png')}" alt="Coverage and set-aside leads"><figcaption>What local outlets already covered, and every lead Scout threw out, with the reason</figcaption></figure>
  </div>
</section>

<section>
  <div class="kicker">Cost to run</div>
  <h2>Less than a penny a search</h2>
  <div class="stats">
    <div class="stat"><b>$0.009</b><span>per search: ~114K input tokens (67% cached) and ~6.5K output, average of 4 real runs</span></div>
    <div class="stat"><b>$0.18</b><span>per reporter per month, at 20 searches (about one per workday)</span></div>
    <div class="stat"><b>$17.60</b><span>a month for 100 reporters</span></div>
    <div class="stat"><b>$1,760</b><span>a month for 10,000 reporters. Repeat searches cost $0 (the app's own cache)</span></div>
  </div>
  <p>I tried to cut costs by feeding the agents shorter pages. It backfired: they made more calls, used 9% more
  tokens and missed a planted lead (2.7 vs. 3.0 of 3). I kept the full pages.</p>
  <p class="note">gpt-6-luna list prices from Portkey: $0.10 per 1M input tokens, $0.01 cached, $0.50 output.</p>
</section>

<section>
  <div class="kicker">Safety</div>
  <h2>A wrong lead can hurt a real person. Every risk has a guardrail and a test.</h2>
  <div class="cols">
    <ul class="safety">
      <li><b>Made-up facts:</b> every quote is checked word for word against its source file. If it isn't there, it's cut.</li>
      <li><b>Prompt injection:</b> I planted a document telling the AI to "ignore your instructions." It held in 3 of 3 runs and flagged the file.</li>
      <li><b>Runaway agents and spending:</b> 20 tool calls per agent, 50 per run, and a 250K-token budget that stops cleanly.</li>
      <li><b>Accusations:</b> code blocks accusatory wording. Arrest cards say "an accusation, not a conviction."</li>
      <li><b>Privacy:</b> jail-log addresses, birth dates and race are stripped in code. Contact info is for officials only.</li>
      <li><b>It caught me, too:</b> my own code flagged "28 grams or less" as trafficking. The agents threw it out.</li>
    </ul>
    <img src="{art('beats/public-safety.svg')}" class="scout-side" alt="">
  </div>
  <p class="note">78 automated tests, and none of them need an API key to run.</p>
</section>

<section>
  <div class="kicker">Impact</div>
  <h2>It finds what I found by hand, in a couple of minutes</h2>
  <div class="stats">
    <div class="stat"><b>3 of 3</b><span>planted stories found in my test documents (3 runs)</span></div>
    <div class="stat"><b>3 of 3</b><span>decoys correctly thrown out or never raised</span></div>
    <div class="stat"><b>3 of 5</b><span>of the real Beaufort leads I checked by hand surfaced in one search, including the $900K overage</span></div>
    <div class="stat"><b>1–2 min</b><span>per search, across 27+ county records</span></div>
  </div>
  <p><b>Real reporters:</b> {user_test}</p>
  <p>{user_quote}</p>
</section>

<section class="title last">
  <div class="kicker">What's next</div>
  <h2>From class project to a tool in the newsroom every week</h2>
  <ul class="next">
    <li><b>This year's records by default,</b> with saved snapshots of the county's live project dashboard.</li>
    <li><b>"What's new since my last scan,"</b> every Monday morning.</li>
    <li><b>One-click public records requests</b> (S.C. FOIA) drafted from a lead.</li>
    <li><b>A social media monitor,</b> once the platforms allow it within the rules.</li>
  </ul>
  <div class="parade">
    <img src="{art('beats/events-openings-closings.svg')}" alt=""><img src="{art('beats/transportation.svg')}" alt="">
    <img src="{art('beats/education.svg')}" alt=""><img src="{art('beats/housing.svg')}" alt="">
  </div>
  <p class="repo">Code: {repo}{private}</p>
</section>
"""

CSS = """
:root { --ink:#121212; --muted:#5F5F5F; --rule:#D9D9D9; --accent:#A6192E; --tint:#F6F6F4; }
.reveal { font-family:'Libre Franklin', Arial, sans-serif; color:var(--ink); font-size:30px; }
.reveal-viewport { background:#FFFFFF; }
.reveal .slides section { text-align:left; }
.reveal h1, .reveal h2 { font-family:'Source Serif 4', Georgia, serif; color:var(--ink); text-transform:none; letter-spacing:-.01em; }
.reveal h1 { font-size:3.4em; margin:0; }
.reveal h2 { font-size:1.65em; line-height:1.15; margin:.1em 0 .6em; border-bottom:3px double var(--ink); padding-bottom:.3em; }
.reveal ul { margin:0 0 0 1em; } .reveal li { margin:.35em 0; line-height:1.35; }
.reveal a { color:var(--accent); }
.kicker { font-size:.55em; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); }
.topline { font-size:.5em; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--muted);
           border-top:2px solid var(--ink); border-bottom:1px solid var(--rule); padding:.3em 0; text-align:center; }
.title { text-align:center !important; }
.title .brand { display:flex; align-items:center; justify-content:center; gap:.4em; margin:.6em 0 .2em; }
.gator-big { width:330px; }
.pitch { font-family:'Source Serif 4', Georgia, serif; font-style:italic; font-size:1.05em; max-width:900px; margin:.4em auto; }
.byline { font-weight:700; margin-top:1em; } .repo { font-size:.7em; margin-top:.8em; } .small { font-size:.85em; color:var(--muted); }
.cols { display:flex; gap:1.2em; align-items:center; } .cols > div, .cols > ul { flex:1; }
.scout-side { width:300px; flex:none; }
.who { font-style:italic; color:var(--muted); font-size:.85em; margin-top:.8em; }
.compare { font-size:.78em; width:100%; border-collapse:collapse; }
.compare th, .compare td { border-bottom:1px solid var(--rule); padding:.45em .5em; text-align:left; }
.compare th { font-size:.85em; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
.compare .us { background:#FBEDEF; font-weight:700; color:var(--accent); }
.flow { display:flex; align-items:stretch; gap:.25em; margin-top:.6em; }
.flow .step { flex:1; border:2px solid var(--ink); border-radius:4px; padding:.5em; text-align:center; font-size:.66em;
              display:flex; flex-direction:column; align-items:center; justify-content:flex-start; gap:.25em; }
.flow .step img { width:150px; height:105px; object-fit:contain; }
.flow .step b { font-family:'Source Serif 4', Georgia, serif; font-size:1.5em; }
.flow .step span { color:var(--muted); line-height:1.3; }
.flow .step.code { background:var(--tint); }
.flow .tag { font-size:.85em; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); margin-top:.5em; }
.flow .arrow { align-self:center; font-size:1.4em; color:var(--accent); font-weight:800; }
.note { font-size:.66em; color:var(--muted); margin-top:.9em; }
.shots { display:flex; gap:.6em; align-items:flex-start; }
.shots figure { flex:1; margin:0; }
.shots img { width:100%; max-height:520px; object-fit:contain; object-position:top; border:1px solid var(--rule); box-shadow:0 4px 18px rgba(0,0,0,.08); }
.shots figcaption { font-size:.62em; color:var(--muted); margin-top:.35em; }
.stats { display:grid; grid-template-columns:repeat(4, 1fr); gap:.5em; margin:.3em 0 .8em; }
.stat { border-top:3px solid var(--ink); padding-top:.3em; }
.stat b { display:block; font-family:'Source Serif 4', Georgia, serif; font-size:2.1em; color:var(--accent); }
.stat span { font-size:.62em; color:var(--muted); line-height:1.3; display:block; }
.reveal p { font-size:.85em; line-height:1.4; }
.safety li { font-size:.8em; }
.next li { font-size:.95em; }
.title ul.next { display:inline-block; text-align:left; margin:0 auto; }
.parade { display:flex; justify-content:center; gap:.4em; margin-top:.4em; } .parade img { height:130px; }
.corner { text-align:right; margin-top:-.2em; } .corner img { height:120px; }
.todo { background:#FFE14D; color:#000; font-weight:800; padding:.05em .3em; border-radius:3px; }
"""

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scout · Slides</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;600;700;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="reveal"><div class="slides">{SLIDES}</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.js"></script>
<script>Reveal.initialize({{ hash: true, slideNumber: "c/t", width: 1280, height: 720, margin: 0.05, transition: "slide" }});</script>
</body>
</html>
"""

if __name__ == "__main__":
    out = ROOT / "docs" / "slides.html"
    out.write_text(HTML, encoding="utf-8")
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB)")
