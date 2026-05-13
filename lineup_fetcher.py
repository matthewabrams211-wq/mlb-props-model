"""
Fetches today's MLB lineups and probable/confirmed starting pitchers.

Lineup availability:
  - Probable pitchers: available 1-2 days in advance
  - Official lineups:  posted ~2-3 hours before first pitch
"""
import statsapi
from datetime import datetime


def get_todays_games(date_str: str = None) -> list:
    """Returns raw schedule list for the given date (default: today)."""
    if date_str is None:
        date_str = datetime.now().strftime('%m/%d/%Y')
    return statsapi.schedule(date=date_str, sportId=1)


def get_game_context(game_pk: int) -> dict:
    """
    Returns lineup + pitcher info for a game.
    Tries official lineups first; falls back to probable pitchers.
    """
    result = {
        'game_pk': game_pk,
        'home_team': '',
        'away_team': '',
        'home_batters': [],   # list of player IDs in batting order
        'away_batters': [],
        'home_pitcher_id': None,
        'away_pitcher_id': None,
        'lineups_official': False,
    }

    # Pull schedule entry with probablePitcher + lineups hydration
    try:
        sched = statsapi.get('schedule', {
            'gamePk': game_pk,
            'hydrate': 'probablePitcher,lineups',
        })
        dates = sched.get('dates', [])
        game = dates[0].get('games', [{}])[0] if dates else {}

        teams = game.get('teams', {})
        result['home_team'] = teams.get('home', {}).get('team', {}).get('abbreviation', '')
        result['away_team'] = teams.get('away', {}).get('team', {}).get('abbreviation', '')

        # Probable pitchers (pre-game)
        result['home_pitcher_id'] = (
            teams.get('home', {}).get('probablePitcher', {}).get('id')
        )
        result['away_pitcher_id'] = (
            teams.get('away', {}).get('probablePitcher', {}).get('id')
        )

        # Official lineups (posted closer to game time)
        lineups = game.get('lineups', {})
        home_players = lineups.get('homePlayers', [])
        away_players = lineups.get('awayPlayers', [])

        if home_players:
            result['home_batters'] = [p['id'] for p in home_players]
            result['lineups_official'] = True
        if away_players:
            result['away_batters'] = [p['id'] for p in away_players]

    except Exception:
        pass

    # If official lineups aren't up yet, try the boxscore (works mid/post-game)
    if not result['home_batters']:
        try:
            box = statsapi.boxscore_data(game_pk)
            home = box.get('home', {})
            away = box.get('away', {})
            result['home_batters'] = home.get('batters', [])
            result['away_batters'] = away.get('batters', [])
            if result['home_batters']:
                result['lineups_official'] = True
            # Starting pitchers from boxscore
            if not result['home_pitcher_id']:
                hp = home.get('pitchers', [])
                result['home_pitcher_id'] = hp[0] if hp else None
            if not result['away_pitcher_id']:
                ap = away.get('pitchers', [])
                result['away_pitcher_id'] = ap[0] if ap else None
        except Exception:
            pass

    return result


def get_todays_lineups(date_str: str = None) -> list:
    """
    Returns a list of game context dicts for all games today.
    Each entry has home/away batters, pitcher IDs, and team abbreviations.
    """
    games = get_todays_games(date_str)
    contexts = []
    for game in games:
        ctx = get_game_context(game['game_id'])
        ctx['start_time'] = game.get('game_datetime', '')
        ctx['status'] = game.get('status', '')
        contexts.append(ctx)
    return contexts
