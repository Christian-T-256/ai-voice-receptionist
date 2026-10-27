"""Build a static per-location call operations dashboard."""

from __future__ import annotations

import html
import json
from pathlib import Path

STYLES = """
:root{--ink:#13231f;--muted:#64736f;--paper:#f4f1e8;--card:#fffdf7;--line:#d9d8ce;--pine:#164d43;--mint:#b9dfcf;--coral:#e66a4e;--amber:#eebc5c;--shadow:0 18px 50px rgba(19,35,31,.10)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 Inter,ui-sans-serif,system-ui,sans-serif}a{color:inherit}.shell{width:min(1160px,calc(100% - 36px));margin:auto}.topbar{padding:22px 0;display:flex;align-items:center;justify-content:space-between}.brand{font-weight:850;letter-spacing:-.03em}.brand span{display:inline-grid;place-items:center;width:32px;height:32px;margin-right:10px;border-radius:50%;background:var(--pine);color:white}.quiet{color:var(--muted)}.hero{margin:12px 0 28px;padding:42px;border:1px solid var(--line);border-radius:28px;background:linear-gradient(125deg,#fffdf7 45%,#dceee7);box-shadow:var(--shadow)}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:var(--pine)}h1{max-width:780px;margin:10px 0;font-size:clamp(36px,6vw,70px);line-height:.98;letter-spacing:-.055em}h2{font-size:23px;letter-spacing:-.03em}.lede{max-width:720px;color:var(--muted);font-size:17px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.location{padding:26px;border:1px solid var(--line);border-radius:22px;background:var(--card);transition:.2s transform,.2s box-shadow}.location:hover{transform:translateY(-3px);box-shadow:var(--shadow)}.type{display:inline-block;padding:5px 9px;border-radius:999px;background:var(--mint);font-size:12px;font-weight:800}.location h2{margin:16px 0 4px}.arrow{display:inline-block;margin-top:18px;color:var(--pine);font-weight:800}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:26px 0}.stat{padding:18px;border:1px solid var(--line);border-radius:18px;background:var(--card)}.stat b{display:block;font-size:28px;letter-spacing:-.04em}.stat span{font-size:12px;color:var(--muted)}.panel{margin:18px 0;padding:24px;border:1px solid var(--line);border-radius:22px;background:var(--card)}.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{padding:7px 10px;background:#edf4ef;border-radius:999px;font-size:13px}.rules{display:grid;grid-template-columns:1fr 1fr;gap:18px}.rule{border-left:3px solid var(--coral);padding-left:14px}.rule b{display:block}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{text-align:left;padding:14px 12px;border-bottom:1px solid var(--line)}th{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}.status{font-weight:800;color:var(--pine)}.after{color:#9a4f18}footer{padding:38px 0 55px;color:var(--muted);font-size:13px}@media(max-width:760px){.hero{padding:28px}.grid,.rules{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.topbar .quiet{display:none}}
""".strip()


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _hours_summary(location: dict) -> str:
    open_days = []
    for day, periods in location["hours"].items():
        if periods:
            open_days.append(f"{day.title()} {', '.join(f'{start} to {end}' for start, end in periods)}")
    return "; ".join(open_days)


def _metrics(calls: list[dict]) -> dict:
    return {
        "Calls": len(calls),
        "Leads captured": sum(call["lead_captured"] for call in calls),
        "Requests": sum(call["appointment_requested"] for call in calls),
        "After hours": sum(call["after_hours"] for call in calls),
    }


def _layout(title: str, body: str, asset_prefix: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Fictional AI receptionist operations dashboard">
  <title>{_e(title)}</title>
  <link rel="stylesheet" href="{asset_prefix}assets/styles.css">
</head>
<body>
  <header class="shell topbar"><div class="brand"><span>CR</span>Clinic Reception</div><div class="quiet">Fictional demo data</div></header>
  <main class="shell">{body}</main>
  <footer class="shell">Static portfolio demo. No patient data and no live Retell calls.</footer>
</body>
</html>
"""


def _call_rows(calls: list[dict]) -> str:
    if not calls:
        return '<tr><td colspan="6" class="quiet">No calls in this fixture.</td></tr>'
    rows = []
    for call in calls:
        period_class = "after" if call["after_hours"] else ""
        rows.append(
            "<tr>"
            f"<td>{_e(call['started_at'])}</td>"
            f"<td>{_e(call['caller_name'])}</td>"
            f"<td>{_e(call['reason'])}</td>"
            f"<td class=\"status\">{_e(call['outcome'])}</td>"
            f"<td>{_e(call['duration_seconds'])} sec</td>"
            f"<td class=\"{period_class}\">{'After hours' if call['after_hours'] else 'Open hours'}</td>"
            "</tr>"
        )
    return "".join(rows)


def _location_page(location: dict, calls: list[dict]) -> str:
    metrics = _metrics(calls)
    stats = "".join(f'<div class="stat"><b>{value}</b><span>{_e(label)}</span></div>' for label, value in metrics.items())
    services = "".join(f'<span class="chip">{_e(service)}</span>' for service in location["services"])
    body = f"""
    <p><a class="quiet" href="../index.html">Back to locations</a></p>
    <section class="hero"><div class="eyebrow">{_e(location['practice_type'].replace('_', ' '))} voice agent</div><h1>{_e(location['practice_name'])}</h1><p class="lede">{_e(location['agent_name'])} handles routine calls, captures appointment requests, and escalates clinical or urgent issues without inventing answers.</p></section>
    <section class="stats">{stats}</section>
    <section class="panel"><div class="eyebrow">Configured operation</div><h2>What the receptionist knows</h2><div class="chips">{services}</div><p class="quiet">Hours: {_e(_hours_summary(location))}</p></section>
    <section class="panel"><div class="eyebrow">Safety boundary</div><h2>Guardrails visible in the workflow</h2><div class="rules"><div class="rule"><b>No clinical advice</b><span class="quiet">Routes medical questions to clinic staff and sends emergencies to 911.</span></div><div class="rule"><b>No false confirmation</b><span class="quiet">Records a request, then waits for staff confirmation.</span></div><div class="rule"><b>Minimum data</b><span class="quiet">Captures only contact details, service, and requested time.</span></div><div class="rule"><b>Configured facts only</b><span class="quiet">Never invents hours, prices, services, or insurance coverage.</span></div></div></section>
    <section class="panel"><div class="eyebrow">Call log</div><h2>Recent fictional calls</h2><div class="table-wrap"><table><thead><tr><th>Started</th><th>Caller</th><th>Reason</th><th>Outcome</th><th>Duration</th><th>Period</th></tr></thead><tbody>{_call_rows(calls)}</tbody></table></div></section>
    """
    return _layout(f"{location['practice_name']} | Clinic Reception", body, "../")


def _index_page(locations: list[dict], calls: list[dict]) -> str:
    cards = []
    for location in locations:
        location_calls = [call for call in calls if call["location_id"] == location["id"]]
        metrics = _metrics(location_calls)
        cards.append(f"""<a class="location" href="./{_e(location['id'])}/index.html"><span class="type">{_e(location['practice_type'].replace('_', ' '))}</span><h2>{_e(location['practice_name'])}</h2><div class="quiet">{_e(location['city'])}, {_e(location['state'])}</div><p>{metrics['Calls']} sample calls, {metrics['Requests']} appointment requests</p><span class="arrow">Open dashboard &gt;</span></a>""")
    body = f"""<section class="hero"><div class="eyebrow">Retell AI receptionist</div><h1>Every call has a safe next step.</h1><p class="lede">Two fictional clinics demonstrate configuration-driven agents, strict healthcare guardrails, and an operations view that turns calls into clear follow-up.</p></section><section class="grid">{''.join(cards)}</section>"""
    return _layout("Clinic Reception | Demo", body, "./")


def build_site(config: dict, calls_path: str | Path, output_dir: str | Path) -> list[Path]:
    calls_data = json.loads(Path(calls_path).read_text(encoding="utf-8"))
    calls = calls_data.get("calls", [])
    location_ids = {location["id"] for location in config["locations"]}
    unknown = sorted({call.get("location_id") for call in calls} - location_ids)
    if unknown:
        raise ValueError(f"call fixture has unknown locations: {', '.join(unknown)}")

    output = Path(output_dir)
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    written = []
    style_path = assets / "styles.css"
    style_path.write_text(STYLES + "\n", encoding="utf-8")
    written.append(style_path)
    index_path = output / "index.html"
    index_path.write_text(_index_page(config["locations"], calls), encoding="utf-8")
    written.append(index_path)
    for location in config["locations"]:
        page_dir = output / location["id"]
        page_dir.mkdir(parents=True, exist_ok=True)
        page_path = page_dir / "index.html"
        location_calls = [call for call in calls if call["location_id"] == location["id"]]
        page_path.write_text(_location_page(location, location_calls), encoding="utf-8")
        written.append(page_path)
    return written
