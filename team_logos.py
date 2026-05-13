"""ESPN CDN team logo URLs, keyed by MLB Stats API team abbreviation."""

LOGO_URLS = {
    'ARI': 'https://a.espncdn.com/i/teamlogos/mlb/500/ari.png',
    'ATL': 'https://a.espncdn.com/i/teamlogos/mlb/500/atl.png',
    'BAL': 'https://a.espncdn.com/i/teamlogos/mlb/500/bal.png',
    'BOS': 'https://a.espncdn.com/i/teamlogos/mlb/500/bos.png',
    'CHC': 'https://a.espncdn.com/i/teamlogos/mlb/500/chc.png',
    'CWS': 'https://a.espncdn.com/i/teamlogos/mlb/500/chw.png',
    'CIN': 'https://a.espncdn.com/i/teamlogos/mlb/500/cin.png',
    'CLE': 'https://a.espncdn.com/i/teamlogos/mlb/500/cle.png',
    'COL': 'https://a.espncdn.com/i/teamlogos/mlb/500/col.png',
    'DET': 'https://a.espncdn.com/i/teamlogos/mlb/500/det.png',
    'HOU': 'https://a.espncdn.com/i/teamlogos/mlb/500/hou.png',
    'KC':  'https://a.espncdn.com/i/teamlogos/mlb/500/kc.png',
    'LAA': 'https://a.espncdn.com/i/teamlogos/mlb/500/laa.png',
    'LAD': 'https://a.espncdn.com/i/teamlogos/mlb/500/lad.png',
    'MIA': 'https://a.espncdn.com/i/teamlogos/mlb/500/mia.png',
    'MIL': 'https://a.espncdn.com/i/teamlogos/mlb/500/mil.png',
    'MIN': 'https://a.espncdn.com/i/teamlogos/mlb/500/min.png',
    'NYM': 'https://a.espncdn.com/i/teamlogos/mlb/500/nym.png',
    'NYY': 'https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png',
    'OAK': 'https://a.espncdn.com/i/teamlogos/mlb/500/oak.png',
    'PHI': 'https://a.espncdn.com/i/teamlogos/mlb/500/phi.png',
    'PIT': 'https://a.espncdn.com/i/teamlogos/mlb/500/pit.png',
    'SD':  'https://a.espncdn.com/i/teamlogos/mlb/500/sd.png',
    'SEA': 'https://a.espncdn.com/i/teamlogos/mlb/500/sea.png',
    'SF':  'https://a.espncdn.com/i/teamlogos/mlb/500/sf.png',
    'STL': 'https://a.espncdn.com/i/teamlogos/mlb/500/stl.png',
    'TB':  'https://a.espncdn.com/i/teamlogos/mlb/500/tb.png',
    'TEX': 'https://a.espncdn.com/i/teamlogos/mlb/500/tex.png',
    'TOR': 'https://a.espncdn.com/i/teamlogos/mlb/500/tor.png',
    'WSH': 'https://a.espncdn.com/i/teamlogos/mlb/500/was.png',
}

FALLBACK_LOGO = 'https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png'


def get_logo(team_abbr: str) -> str:
    return LOGO_URLS.get((team_abbr or '').upper(), FALLBACK_LOGO)


def logo_img_tag(team_abbr: str, size: int = 32) -> str:
    url = get_logo(team_abbr)
    return f'<img src="{url}" width="{size}" height="{size}" style="vertical-align:middle; margin-right:6px;">'
