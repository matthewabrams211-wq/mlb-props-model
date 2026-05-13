import statsapi
import pandas as pd
import numpy as np
from datetime import datetime

CURRENT_YEAR = datetime.now().year


def lookup_player(name: str) -> dict:
    results = statsapi.lookup_player(name)
    if not results:
        raise ValueError(f"No player found for '{name}'")
    if len(results) > 1:
        names = [r['fullName'] for r in results[:3]]
        print(f"Multiple matches: {names} — using first")
    return results[0]


def get_game_logs(player_id: int, seasons: list = None) -> pd.DataFrame:
    if seasons is None:
        seasons = [CURRENT_YEAR - 2, CURRENT_YEAR - 1, CURRENT_YEAR]

    all_rows = []
    for season in seasons:
        try:
            data = statsapi.player_stat_data(
                player_id,
                group='hitting',
                type='gameLog',
                season=season
            )
            for split in data.get('stats', []):
                stat = split.get('stat', {})
                game_info = split.get('game', {})
                is_home = split.get('isHome', True)
                player_team = split.get('team', {}).get('abbreviation', '')
                opponent = split.get('opponent', {}).get('abbreviation', '')
                home_team = player_team if is_home else opponent

                row = {
                    'player_id': player_id,
                    'season': season,
                    'date': game_info.get('gameDate', split.get('date', '')),
                    'game_pk': str(game_info.get('gamePk', '')),
                    'opponent': opponent,
                    'home_team': home_team,
                    'is_home': int(is_home),
                    'ab': int(stat.get('atBats', 0)),
                    'h': int(stat.get('hits', 0)),
                    'r': int(stat.get('runs', 0)),
                    'rbi': int(stat.get('rbi', 0)),
                    'd': int(stat.get('doubles', 0)),
                    't': int(stat.get('triples', 0)),
                    'hr': int(stat.get('homeRuns', 0)),
                    'bb': int(stat.get('baseOnBalls', 0)),
                    'k': int(stat.get('strikeOuts', 0)),
                    'sb': int(stat.get('stolenBases', 0)),
                }
                all_rows.append(row)
        except Exception as e:
            print(f"  Warning: Could not fetch {season} data — {e}")

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Only keep games where the player actually batted
    df = df[df['ab'] > 0].reset_index(drop=True)
    return df
