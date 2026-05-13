"""
Player rating engine — scores a batter 0-100 for a given matchup.

Components:
  Form        (0-30)  — recent H+R+RBI rolling averages
  Season Avg  (0-20)  — season-long H+R+RBI baseline
  Matchup     (0-25)  — opposing pitcher quality + BvP history
  Barrel Edge (0-15)  — batter barrel rate advantage over pitcher, weighted by pitch mix
  Park & Wind (0-10)  — ballpark factor + wind direction/speed
"""


def compute_rating(
    recent_7g: float,
    recent_30g: float,
    season_avg: float,
    opp_era: float,
    opp_whip: float,
    batter_fb_barrel: float, batter_bk_barrel: float, batter_os_barrel: float,
    pitcher_fb_barrel: float, pitcher_bk_barrel: float, pitcher_os_barrel: float,
    batter_fb_seen: float,   batter_bk_seen: float,   batter_os_seen: float,
    park_factor: float,
    wind_speed: float,
    wind_dir: int,
    bvp_avg: float   = 0.250,
    bvp_sample: int  = 0,
) -> dict:
    scores = {}

    # ── Form (0-30) ──────────────────────────────────────────────────────────
    # Weighted blend of 7g and 30g rolling avg; 3.5 H+R+RBI/game = max
    form_raw = 0.65 * recent_7g + 0.35 * recent_30g
    scores['Form'] = (round(min(30.0, (form_raw / 3.5) * 30), 1), 30)

    # ── Season Avg (0-20) ────────────────────────────────────────────────────
    scores['Season Avg'] = (round(min(20.0, (season_avg / 3.0) * 20), 1), 20)

    # ── Matchup (0-25) ───────────────────────────────────────────────────────
    # ERA: 3.00 → 25 pts, league avg 4.30 → ~13 pts, 6.00+ → 0 pts
    era_score = max(0.0, min(25.0, 25.0 * (6.0 - opp_era) / (6.0 - 3.0)))
    # BvP adjustment: ±3 pts when we have a real sample (10+ AB)
    if bvp_sample:
        era_score = max(0.0, min(25.0, era_score + (bvp_avg - 0.250) * 20))
    scores['Matchup'] = (round(era_score, 1), 25)

    # ── Barrel Edge (0-15) ───────────────────────────────────────────────────
    # For each pitch group: (batter barrel% - pitcher barrel% allowed) × how often batter sees it
    barrel_edge = (
        batter_fb_seen * (batter_fb_barrel - pitcher_fb_barrel) +
        batter_bk_seen * (batter_bk_barrel - pitcher_bk_barrel) +
        batter_os_seen * (batter_os_barrel - pitcher_os_barrel)
    )
    # Scale: 0 edge → 7.5 pts, +0.05 edge → 15 pts, -0.05 edge → 0 pts
    scores['Barrel Edge'] = (round(max(0.0, min(15.0, 7.5 + barrel_edge * 150)), 1), 15)

    # ── Park & Wind (0-10) ───────────────────────────────────────────────────
    park_score = max(0.0, min(7.0, (park_factor - 0.90) / (1.15 - 0.90) * 7.0))
    wind_score = max(-3.0, min(3.0, wind_dir * min(wind_speed, 20) / 20 * 3.0))
    scores['Park & Wind'] = (round(max(0.0, min(10.0, park_score + wind_score)), 1), 10)

    total = round(min(100, max(0, sum(v[0] for v in scores.values()))))

    grade = (
        'A+' if total >= 90 else 'A'  if total >= 85 else 'A-' if total >= 80 else
        'B+' if total >= 75 else 'B'  if total >= 70 else 'B-' if total >= 65 else
        'C+' if total >= 60 else 'C'  if total >= 55 else 'C-' if total >= 50 else
        'D+' if total >= 45 else 'D'  if total >= 40 else 'F'
    )

    color = (
        '#22c55e' if total >= 75 else   # green
        '#eab308' if total >= 55 else   # yellow
        '#ef4444'                        # red
    )

    return {
        'total':      total,
        'grade':      grade,
        'color':      color,
        'components': scores,  # {label: (score, max_score)}
    }
