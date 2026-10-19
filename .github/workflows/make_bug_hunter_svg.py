#!/usr/bin/env python3
"""
Bug Hunter: pesawat menembaki bug (NullPointer, 404, Merge Conflict) lalu melawan bos "Legacy Code".
Seluruh animasi memakai SMIL di dalam satu SVG (tanpa JavaScript), jadi tetap jalan di README GitHub.

Pemakaian:
    python make_bug_hunter_svg.py
Hasil:
    assets/bug-hunter-dark.svg
    assets/bug-hunter-light.svg

Cara mengubah isi: edit ENEMIES, BOSS_NAME, dan teks di bagian KONFIGURASI.
"""
import math
import os
import random
from html import escape

# =====================  KONFIGURASI  =====================
T = 20.0                      # durasi satu putaran animasi (detik)
W, H = 900, 300
OUT_DIR = "assets"
FONT = "'JetBrains Mono','Fira Code','SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Courier New',monospace"

TITLE = "BUG HUNTER"
BOSS_NAME = "LEGACY CODE"
BOSS_FILE = "legacy_v1_final_FINAL(2).js"
VICTORY_1 = "ALL BUGS FIXED"
VICTORY_2 = 'git commit -m "fix: legacy code"'

SHIP_X = 90
BULLET_X0 = SHIP_X + 44       # titik keluarnya peluru (ujung hidung pesawat)
BULLET_SPEED = 1100           # px per detik

# lane = ketinggian (y) jalur musuh; spawn = detik muncul; shots = detik pesawat menembak
ENEMIES = [
    dict(name="NullPointer",    lane=95,  spawn=0.8, hold_x=620, shots=[2.3, 2.9]),
    dict(name="404",            lane=205, spawn=3.6, hold_x=640, shots=[4.9]),
    dict(name="Merge Conflict", lane=150, spawn=6.3, hold_x=600, shots=[7.7, 8.3]),
]
BOSS = dict(lane=150, spawn=9.2, arrive=11.0, hold_x=670, w=220, h=150,
            shots=[11.2, 11.8, 12.4, 13.0, 13.6])
# =========================================================

EPS = 0.02

PALETTES = {
    "dark": dict(
        bg=("#0A1F44", "#10305F", "#17458A"), border="#1E5AA8", star="#BFE6FF", star_op=0.8,
        ship_a="#D6EFFF", ship_b="#4A9BE8", ship_stroke="#D6EFFF", cockpit="#0A1F44",
        flame="#7EC8FF", flame_core="#FFFFFF", bullet="#D6EFFF", glow=True,
        enemy_fill="#0D2247", accent="#FF6B81", enemy_text="#D6EFFF",
        boss_fill="#0B1A38", boss_bar="#12397A", boss_dim="#7EA6D8", boss_hi="#D6EFFF",
        label="#D6EFFF", hud="#7EC8FF", popup="#D6EFFF", hp_bg="#0A1F44",
        boom=("#FF6B81", "#7EC8FF", "#D6EFFF", "#FFFFFF"), victory_a="#7EC8FF", victory_b="#D6EFFF",
        flash="#FFFFFF",
    ),
    "light": dict(
        bg=("#F3F8FF", "#D7EAFF", "#A9D2FA"), border="#1E5AA8", star="#1E5AA8", star_op=0.35,
        ship_a="#4A9BE8", ship_b="#0A1F44", ship_stroke="#0A1F44", cockpit="#D6EFFF",
        flame="#1E5AA8", flame_core="#7EC8FF", bullet="#1E5AA8", glow=False,
        enemy_fill="#FFFFFF", accent="#E5484D", enemy_text="#0A1F44",
        boss_fill="#FFFFFF", boss_bar="#DCEEFF", boss_dim="#4B6FA3", boss_hi="#0A1F44",
        label="#0A1F44", hud="#1E5AA8", popup="#0A1F44", hp_bg="#FFFFFF",
        boom=("#E5484D", "#1E5AA8", "#4A9BE8", "#0A1F44"), victory_a="#1E5AA8", victory_b="#0A1F44",
        flash="#FFFFFF",
    ),
}


# ---------- helper animasi ----------
def fmt(v):
    if isinstance(v, tuple):
        return " ".join(f"{x:g}" for x in v)
    return f"{v:g}"


def track(attr, pts, tag="animate", extra="", discrete=False):
    """Satu animasi yang berputar bersama seluruh timeline (dur = T)."""
    pts = sorted(pts, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0.0, pts[0][1]))
    if not discrete and pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    out, last = [], -1.0
    for t, v in pts:
        t = min(max(t, 0.0), T)
        if t <= last:
            t = last + 0.001
        out.append((t, v))
        last = t
    vals = ";".join(fmt(v) for _, v in out)
    keys = ";".join(f"{t / T:.5f}" for t, _ in out)
    mode = ' calcMode="discrete"' if discrete else ""
    return (f'<{tag} attributeName="{attr}"{(" " + extra) if extra else ""}{mode} '
            f'values="{vals}" keyTimes="{keys}" dur="{T:g}s" repeatCount="indefinite"/>')


def move(pts):
    return track("transform", pts, "animateTransform", 'type="translate"')


def vis(intervals, attr="opacity"):
    """Tampil (1) hanya pada interval waktu tertentu."""
    pts = [(0.0, 0)]
    for a, b in sorted(intervals):
        if a <= 0:
            pts = [(0.0, 1)]
        else:
            pts.append((a, 1))
        pts.append((b, 0))
    return track(attr, pts, discrete=True)


def pulse(t, dur, base, peak):
    return [(t - EPS, base), (t, peak), (t + dur, base)]


def enemy_width(name):
    return len(name) * 7.9 + 62


# ---------- bagian gambar ----------
def bug_icon(color):
    legs = ""
    for sx in (-1, 1):
        legs += (f'<path d="M{sx * 5} -3 L{sx * 12} -7 M{sx * 5.5} 1 L{sx * 13} 2 M{sx * 5} 5 L{sx * 11} 10" '
                 f'stroke="{color}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    return (f'<g>{legs}<path d="M-2 -11 L-5 -16 M2 -11 L5 -16" stroke="{color}" stroke-width="1.4" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="1" rx="6" ry="7.5" fill="{color}"/><circle cx="0" cy="-8" r="3.6" fill="{color}"/>'
            f'<path d="M0 -5 V8" stroke="rgba(0,0,0,0.35)" stroke-width="1"/></g>')


def ship_svg(p):
    glow = ' filter="url(#glow)"' if p["glow"] else ""
    return f'''<g>
      <g transform="translate(-26,0)"><polygon points="0,-5 -18,0 0,5" fill="{p["flame"]}"{glow}>
        <animate attributeName="points" dur="0.18s" repeatCount="indefinite"
                 values="0,-5 -18,0 0,5;0,-4 -28,0 0,4;0,-5 -18,0 0,5"/></polygon>
        <polygon points="0,-2.5 -10,0 0,2.5" fill="{p["flame_core"]}"/></g>
      <path d="M44 0 L-4 -15 L-14 -27 L-23 -27 L-17 -7 L-27 -7 L-27 7 L-17 7 L-23 27 L-14 27 L-4 15 Z"
            fill="url(#shipGrad)" stroke="{p["ship_stroke"]}" stroke-width="1.4" stroke-linejoin="round"/>
      <ellipse cx="12" cy="0" rx="11" ry="5" fill="{p["cockpit"]}" stroke="{p["ship_stroke"]}" stroke-width="1"/>
      <path d="M6 -2 L16 -2" stroke="{p["flame"]}" stroke-width="1.2" stroke-linecap="round"/>
    </g>'''


def enemy_svg(p, name):
    w = enemy_width(name)
    x0 = -w / 2
    return f'''<rect x="{x0:.1f}" y="-19" width="{w:.1f}" height="38" rx="11" fill="{p["enemy_fill"]}" stroke="{p["accent"]}" stroke-width="1.8"/>
      <g transform="translate({x0 + 22:.1f},0)">{bug_icon(p["accent"])}</g>
      <text x="{x0 + 40:.1f}" y="5" font-size="13" font-weight="700" fill="{p["enemy_text"]}">{escape(name)}</text>''', w


def boss_svg(p):
    w, h = BOSS["w"], BOSS["h"]
    x0, y0 = -w / 2, -h / 2
    code = [
        ("function doEverything() {", p["boss_hi"]),
        ("  // TODO: refactor later", p["boss_dim"]),
        ("  if (a) { if (b) { if (c)", p["boss_dim"]),
        ("    goto line_10;", p["accent"]),
        ("  eval(userInput); // lol", p["boss_dim"]),
        ("  setTimeout(fix, 99999);", p["boss_dim"]),
        ("}", p["boss_hi"]),
    ]
    lines = "".join(
        f'<text x="{x0 + 12}" y="{y0 + 46 + i * 14.5:.1f}" font-size="9.5" fill="{c}">{escape(t).replace(" ", "&#160;")}</text>'
        for i, (t, c) in enumerate(code)
    )
    return f'''<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="14" fill="{p["boss_fill"]}" stroke="{p["accent"]}" stroke-width="2.2">
        <animate attributeName="stroke-opacity" values="1;0.45;1" dur="1.1s" repeatCount="indefinite"/></rect>
      <path d="M{x0} {y0 + 14} a14 14 0 0 1 14 -14 h{w - 28} a14 14 0 0 1 14 14 v14 h-{w} z" fill="{p["boss_bar"]}"/>
      <circle cx="{x0 + 16}" cy="{y0 + 14}" r="3.6" fill="{p["accent"]}"/><circle cx="{x0 + 30}" cy="{y0 + 14}" r="3.6" fill="{p["boss_dim"]}"/><circle cx="{x0 + 44}" cy="{y0 + 14}" r="3.6" fill="{p["boss_dim"]}"/>
      <text x="{x0 + 58}" y="{y0 + 18}" font-size="9" fill="{p["boss_dim"]}">{escape(BOSS_FILE)}</text>
      {lines}
      <text x="{x0 + w - 12}" y="{y0 + h - 10}" font-size="9.5" text-anchor="end" fill="{p["accent"]}">
        ! 4,812 warnings
        <animate attributeName="opacity" values="1;0.2;1" dur="0.9s" repeatCount="indefinite"/></text>'''


def explosion(p, cx, cy, t0, R, n, rng):
    parts = []
    c = p["boom"]
    glow = ' filter="url(#glow)"' if p["glow"] else ""
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="0" fill="none" stroke="{c[1]}" stroke-width="3" opacity="0">'
        + track("r", [(t0 - EPS, 0), (t0, 4), (t0 + 0.7, R * 1.25)])
        + track("opacity", [(t0 - EPS, 0), (t0, 0.95), (t0 + 0.7, 0)]) + "</circle>")
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="0" fill="{c[0]}" opacity="0"{glow}>'
        + track("r", [(t0 - EPS, 0), (t0, R * 0.35), (t0 + 0.35, R * 0.8)])
        + track("opacity", [(t0 - EPS, 0), (t0, 0.95), (t0 + 0.35, 0)]) + "</circle>")
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="0" fill="{c[3]}" opacity="0">'
        + track("r", [(t0 - EPS, 0), (t0, R * 0.2), (t0 + 0.2, R * 0.45)])
        + track("opacity", [(t0 - EPS, 0), (t0, 1), (t0 + 0.2, 0)]) + "</circle>")
    glyphs = ["{", "}", ";", "<", ">", "/", "0", "1", "()", "[]", "=>"]
    for k in range(n):
        ang = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        dist = R * rng.uniform(0.9, 1.7)
        dx, dy = math.cos(ang) * dist, math.sin(ang) * dist
        col = c[k % len(c)]
        end = t0 + rng.uniform(0.7, 1.0)
        if k % 2 == 0:
            body = f'<text x="0" y="4" font-size="{rng.choice([11, 13, 15])}" font-weight="700" text-anchor="middle" fill="{col}">{escape(rng.choice(glyphs))}</text>'
        else:
            body = f'<rect x="-2.5" y="-2.5" width="5" height="5" rx="1" fill="{col}"/>'
        parts.append(
            f'<g opacity="0">{body}'
            + move([(0.0, (cx, cy)), (t0, (cx, cy)), (end, (round(cx + dx, 1), round(cy + dy, 1)))])
            + track("opacity", [(t0 - EPS, 0), (t0, 1), (end - 0.25, 1), (end, 0)]) + "</g>")
    return "\n    ".join(parts)


def popup(p, cx, cy, t0, text, size=14):
    return (f'<text x="0" y="0" font-size="{size}" font-weight="700" text-anchor="middle" fill="{p["popup"]}" opacity="0">{escape(text)}'
            + move([(0.0, (cx, cy)), (t0, (cx, cy)), (t0 + 0.9, (cx, cy - 34))])
            + track("opacity", [(t0 - EPS, 0), (t0, 1), (t0 + 0.55, 1), (t0 + 0.9, 0)]) + "</text>")


def build(theme):
    p = PALETTES[theme]
    rng = random.Random(7)
    glow = ' filter="url(#glow)"' if p["glow"] else ""
    layers_bullets, layers_enemies, layers_fx = [], [], []
    kills, events_ship = [], [(0.0, 150)]
    cur = 150

    # ----- musuh biasa -----
    for e in ENEMIES:
        body, w = enemy_svg(p, e["name"])
        left = e["hold_x"] - w / 2
        hits = []
        for s in e["shots"]:
            travel = (left - BULLET_X0) / BULLET_SPEED
            hits.append(s + travel)
            layers_bullets.append(bullet(p, e["lane"], s, s + travel, left))
        kill = hits[-1]
        kills.append(("enemy", kill, e["hold_x"], e["lane"]))
        x_start = W + w / 2 + 30
        x_track = [(0.0, (x_start, e["lane"])), (e["spawn"], (x_start, e["lane"])),
                   (e["spawn"] + 1.6, (e["hold_x"], e["lane"])), (kill, (e["hold_x"], e["lane"])),
                   (kill + EPS, (x_start + 200, e["lane"]))]
        flash_pts = []
        for h in hits[:-1]:
            flash_pts += pulse(h, 0.12, 0, 0.75)
        flash = (f'<rect x="{-w / 2:.1f}" y="-19" width="{w:.1f}" height="38" rx="11" fill="{p["flash"]}" opacity="0">'
                 + (track("opacity", flash_pts) if flash_pts else "") + "</rect>")
        layers_enemies.append(
            f'<g>{move(x_track)}{vis([(0, kill)])}'
            f'<g>{body}{flash}<animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0;0 4;0 0" '
            f'dur="{rng.choice([1.5, 1.8, 2.1])}s" repeatCount="indefinite"/></g></g>')
        layers_fx.append(explosion(p, e["hold_x"], e["lane"], kill, 48, 14, rng))
        layers_fx.append(popup(p, e["hold_x"], e["lane"] - 26, kill, "+100"))
        events_ship += [(e["spawn"] + 0.2, cur), (e["spawn"] + 0.8, e["lane"])]
        cur = e["lane"]

    # ----- bos -----
    b = BOSS
    left = b["hold_x"] - b["w"] / 2
    bhits = []
    for s in b["shots"]:
        travel = (left - BULLET_X0) / BULLET_SPEED
        bhits.append(s + travel)
        layers_bullets.append(bullet(p, b["lane"], s, s + travel, left))
    bkill = bhits[-1] + 0.1
    kills.append(("boss", bkill, b["hold_x"], b["lane"]))
    events_ship += [(b["spawn"] + 0.2, cur), (b["spawn"] + 0.8, b["lane"])]
    bx0 = W + b["w"] / 2 + 40
    bpts = [(0.0, (bx0, b["lane"])), (b["spawn"], (bx0, b["lane"])), (b["arrive"], (b["hold_x"], b["lane"]))]
    for h in bhits[:-1]:
        bpts += [(h - EPS, (b["hold_x"], b["lane"])), (h + 0.04, (b["hold_x"] + 5, b["lane"] - 2)),
                 (h + 0.08, (b["hold_x"] - 5, b["lane"] + 2)), (h + 0.13, (b["hold_x"], b["lane"]))]
    bpts += [(bkill - EPS, (b["hold_x"], b["lane"])), (bkill, (b["hold_x"], b["lane"])), (bkill + EPS, (bx0 + 300, b["lane"]))]
    bflash = []
    for h in bhits:
        bflash += pulse(h, 0.14, 0, 0.6)
    layers_enemies.append(
        f'<g>{move(bpts)}{vis([(0, bkill)])}{boss_svg(p)}'
        f'<rect x="{-b["w"] / 2}" y="{-b["h"] / 2}" width="{b["w"]}" height="{b["h"]}" rx="14" fill="{p["flash"]}" opacity="0">{track("opacity", bflash)}</rect></g>')
    layers_fx.append(explosion(p, b["hold_x"], b["lane"], bkill, 100, 26, rng))
    layers_fx.append(explosion(p, b["hold_x"] - 50, b["lane"] - 25, bkill + 0.2, 55, 10, rng))
    layers_fx.append(explosion(p, b["hold_x"] + 55, b["lane"] + 30, bkill + 0.35, 55, 10, rng))
    layers_fx.append(popup(p, b["hold_x"], b["lane"] - 60, bkill + 0.1, "+1000", 20))

    # ----- bar HP bos + peringatan -----
    bar_x, bar_w = b["hold_x"] - b["w"] / 2, b["w"]
    hp_pts = [(0.0, bar_w)]
    per = bar_w / len(b["shots"])
    cur_hp = bar_w
    for h in bhits:
        hp_pts += [(h - EPS, cur_hp), (h + 0.12, cur_hp - per)]
        cur_hp -= per
    hp_bar = f'''<g opacity="0">{vis([(b["arrive"] - 0.9, bkill + 0.4)])}
      <text x="{bar_x}" y="45" font-size="11" font-weight="700" fill="{p["label"]}">{escape(BOSS_NAME)}</text>
      <text x="{bar_x + bar_w}" y="45" font-size="10" text-anchor="end" fill="{p["accent"]}">HP</text>
      <rect x="{bar_x}" y="50" width="{bar_w}" height="11" rx="5.5" fill="{p["hp_bg"]}" stroke="{p["accent"]}" stroke-width="1.4"/>
      <rect x="{bar_x}" y="50" width="{bar_w}" height="11" rx="5.5" fill="url(#hpGrad)">{track("width", hp_pts)}</rect></g>'''
    blink = []
    t = b["spawn"]
    while t < b["arrive"] - 0.2:
        blink.append((t, t + 0.28))
        t += 0.56
    warning = (f'<text x="{W / 2}" y="{H / 2 + 6}" font-size="17" font-weight="700" text-anchor="middle" fill="{p["accent"]}" opacity="0" '
               f'letter-spacing="2">WARNING: LEGACY CODE APPROACHING{vis(blink)}</text>')

    # ----- kemenangan -----
    tv = bkill + 0.9
    victory = f'''<g opacity="0">{track("opacity", [(0.0, 0), (tv, 0), (tv + 0.5, 1), (T - 1.0, 1), (T - 0.4, 0)])}
      <text x="{W / 2}" y="{H / 2 - 4}" font-size="30" font-weight="700" text-anchor="middle" fill="url(#vicGrad)" letter-spacing="3">{escape(VICTORY_1)} ✓</text>
      <g clip-path="url(#typeClip)"><text x="{W / 2}" y="{H / 2 + 26}" font-size="14" text-anchor="middle" fill="{p["label"]}">$ {escape(VICTORY_2)}</text></g></g>'''
    type_w = (len(VICTORY_2) + 3) * 8.6
    type_clip = (f'<clipPath id="typeClip"><rect x="{W / 2 - type_w / 2:.1f}" y="{H / 2 + 8}" width="0" height="26">'
                 + track("width", [(0.0, 0), (tv + 0.5, 0), (tv + 1.9, type_w)]) + "</rect></clipPath>")

    # ----- HUD -----
    ev = [k[1] for k in kills]
    bounds = [0.0] + ev + [T]
    hud_states = ""
    for i in range(len(bounds) - 1):
        label = f"BUGS FIXED {i}/{len(kills)}"
        hud_states += (f'<text x="24" y="49" font-size="11" fill="{p["hud"]}" opacity="0">{label}'
                       f'{vis([(bounds[i], bounds[i + 1])])}</text>')

    # ----- pesawat -----
    ship_track = move([(t, (SHIP_X, y)) for t, y in events_ship]
                      + [(T - 0.6, (SHIP_X, b["lane"])), (T - 0.2, (SHIP_X, 150))])
    ship = (f'<g>{ship_track}<g>{ship_svg(p)}'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0;0 3;0 0" dur="1.4s" repeatCount="indefinite"/></g></g>')

    # ----- bintang -----
    stars = []
    for _ in range(46):
        x, y = rng.uniform(0, W), rng.uniform(8, H - 8)
        r = rng.choice([0.8, 1.1, 1.5])
        stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" opacity="{rng.uniform(0.3, 1) * p["star_op"]:.2f}"/>')
    star_set = "".join(stars)
    stars_svg = (f'<g fill="{p["star"]}"><g>{star_set}<g transform="translate({W},0)">{star_set}</g>'
                 f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{W} 0" dur="16s" repeatCount="indefinite"/></g></g>')

    guides = "".join(
        f'<line x1="{BULLET_X0 + 20}" y1="{y}" x2="{W - 20}" y2="{y}" stroke="{p["star"]}" stroke-opacity="{0.10 if theme == "dark" else 0.16}" stroke-dasharray="2 8"/>'
        for y in (95, 150, 205))

    glow_def = ('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/>'
                '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>') if p["glow"] else ""

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}" role="img" aria-label="Animasi Bug Hunter: pesawat menembaki bug dan bos Legacy Code">
  <defs>
    {glow_def}
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0.4"><stop offset="0" stop-color="{p["bg"][0]}"/><stop offset="0.6" stop-color="{p["bg"][1]}"/><stop offset="1" stop-color="{p["bg"][2]}"/></linearGradient>
    <linearGradient id="shipGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["ship_a"]}"/><stop offset="1" stop-color="{p["ship_b"]}"/></linearGradient>
    <linearGradient id="hpGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["accent"]}"/><stop offset="1" stop-color="{p["boom"][1]}"/></linearGradient>
    <linearGradient id="vicGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["victory_a"]}"/><stop offset="1" stop-color="{p["victory_b"]}"/></linearGradient>
    <clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="14"/></clipPath>
    {type_clip}
  </defs>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    {stars_svg}
    {guides}
    <text x="24" y="30" font-size="15" font-weight="700" letter-spacing="3" fill="{p["label"]}">{escape(TITLE)}</text>
    {hud_states}
    {"".join(layers_bullets)}
    {"".join(layers_enemies)}
    {hp_bar}
    {ship}
    {chr(10).join("    " + f for f in layers_fx)}
    {warning}
    {victory}
  </g>
  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="13.5" fill="none" stroke="{p["border"]}" stroke-width="1.5"/>
</svg>
'''
    return svg


def bullet(p, lane, t_fire, t_hit, hit_x):
    glow = ' filter="url(#glow)"' if p["glow"] else ""
    return (f'<g opacity="0">{vis([(t_fire, t_hit)])}'
            f'{move([(0.0, (BULLET_X0, lane)), (t_fire, (BULLET_X0, lane)), (t_hit, (round(hit_x - 22, 1), lane))])}'
            f'<rect x="0" y="-2" width="22" height="4" rx="2" fill="{p["bullet"]}"{glow}/></g>'
            f'<circle cx="{BULLET_X0 + 2}" cy="{lane}" r="6" fill="{p["bullet"]}" opacity="0"{glow}>{vis([(t_fire, t_fire + 0.1)])}</circle>'
            f'<circle cx="{round(hit_x, 1)}" cy="{lane}" r="0" fill="{p["bullet"]}" opacity="0">'
            f'{track("r", [(t_hit - EPS, 0), (t_hit, 3), (t_hit + 0.18, 9)])}'
            f'{track("opacity", [(t_hit - EPS, 0), (t_hit, 1), (t_hit + 0.18, 0)])}</circle>')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme in PALETTES:
        path = os.path.join(OUT_DIR, f"bug-hunter-{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build(theme))
        print("dibuat:", path, f"({os.path.getsize(path) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
