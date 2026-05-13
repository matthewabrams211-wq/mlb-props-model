"""
MLB Hitter Props Predictor
--------------------------
Usage:
    python predict.py "Freddie Freeman"
    python predict.py "Mookie Betts" --away --pitcher "Zack Wheeler"
    python predict.py "Aaron Judge" --home-team NYY --temp 68 --wind-speed 12 --wind-dir out
    python predict.py "Freddie Freeman" --no-weather
"""

import argparse
import warnings
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

from data_collector import lookup_player, get_game_logs
from feature_engineering import build_features, get_feature_cols, TARGET_COL
from weather import get_park_factor, parse_wind
from pitcher_data import get_pitcher_season_stats, get_pitcher_name
from bvp_stats import get_bvp
from statcast_features import get_batter_statcast, get_pitcher_statcast

warnings.filterwarnings('ignore')

WIND_DIR_MAP = {'out': 1, 'in': -1, 'cross': 0, 'calm': 0}


def train_and_predict(df: pd.DataFrame, prediction_overrides: dict,
                      fetch_weather: bool, pitcher_id: int = None) -> dict:
    df = build_features(df, fetch_weather=fetch_weather, override_pitcher_id=pitcher_id)
    feature_cols = get_feature_cols()

    df_clean = df.dropna(subset=feature_cols).reset_index(drop=True)
    if len(df_clean) < 20:
        raise ValueError(f"Not enough data after feature building ({len(df_clean)} games). Need at least 20.")

    X = df_clean[feature_cols]
    y = df_clean[TARGET_COL]

    tscv = TimeSeriesSplit(n_splits=5)
    cv_maes = []
    for train_idx, val_idx in tscv.split(X):
        m = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=4,
                         subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
        m.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = m.predict(X.iloc[val_idx])
        cv_maes.append(mean_absolute_error(y.iloc[val_idx], preds))

    model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=4,
                         subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
    model.fit(X, y)

    # Apply user-supplied game conditions for the prediction
    latest = df_clean.iloc[-1:].copy()
    for col, val in prediction_overrides.items():
        latest[col] = val

    pred = float(model.predict(latest[feature_cols])[0])
    pred = max(0.0, pred)

    return {
        'prediction': round(pred, 2),
        'cv_mae': round(float(np.mean(cv_maes)), 3),
    }


def show_recent_form(df: pd.DataFrame, n: int = 10):
    recent = df.tail(n)
    recent_total = recent['h'] + recent['r'] + recent['rbi']
    print(f"\nRecent {n}-game H+R+RBI averages:")
    print(f"  Per game: {recent_total.mean():.2f}  |  Total: {int(recent_total.sum())}")


def main():
    parser = argparse.ArgumentParser(description='MLB Hitter Props Predictor')
    parser.add_argument('player', help='Player name, e.g. "Freddie Freeman"')
    parser.add_argument('--away', action='store_true', help='Player is away (default: home)')
    parser.add_argument('--pitcher', default=None,
                        help='Opposing pitcher name, e.g. "Zack Wheeler"')
    parser.add_argument('--home-team', default=None,
                        help='Home team abbreviation for park factor, e.g. LAD, NYY')
    parser.add_argument('--temp', type=float, default=None, help='Temperature in °F')
    parser.add_argument('--wind-speed', type=float, default=None, help='Wind speed in mph')
    parser.add_argument('--wind-dir', choices=['out', 'in', 'cross', 'calm'], default=None,
                        help='Wind direction: out (hitter-friendly), in, cross, calm')
    parser.add_argument('--seasons', nargs='+', type=int, default=None,
                        help='Seasons to use, e.g. --seasons 2023 2024 2025')
    parser.add_argument('--no-weather', action='store_true',
                        help='Skip weather fetching (faster, less accurate)')
    args = parser.parse_args()

    # Resolve pitcher
    pitcher_id = None
    pitcher_label = ''
    if args.pitcher:
        pitcher_info = lookup_player(args.pitcher)
        pitcher_id = pitcher_info['id']
        pitcher_label = pitcher_info['fullName']
        print(f"Pitcher: {pitcher_label} (ID: {pitcher_id})")

    print(f"\nLooking up: {args.player}")
    player = lookup_player(args.player)
    print(f"Found: {player['fullName']} (ID: {player['id']})")

    print("Fetching game logs...")
    df = get_game_logs(player['id'], seasons=args.seasons)

    if df.empty:
        print("No game log data found.")
        return

    print(f"Loaded {len(df)} games across seasons: {sorted(df['season'].unique())}")

    fetch_weather = not args.no_weather

    # Build overrides for the prediction row from CLI args
    is_home = not args.away
    overrides = {'is_home': int(is_home)}

    if args.home_team:
        overrides['park_factor'] = get_park_factor(args.home_team)
    if args.temp is not None:
        overrides['temp_f'] = args.temp
    if args.wind_speed is not None:
        overrides['wind_speed'] = args.wind_speed
    if args.wind_dir is not None:
        overrides['wind_dir'] = WIND_DIR_MAP[args.wind_dir]

    print("Fetching weather & training model..." if fetch_weather else "Training model (weather skipped)...")
    try:
        results = train_and_predict(df, overrides, fetch_weather, pitcher_id=pitcher_id)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Build display info
    venue = 'Home' if is_home else 'Away'
    park_label = f"  Park ({args.home_team}): {get_park_factor(args.home_team):.2f}x" if args.home_team else ''
    temp_label = f"  Temp:       {args.temp}°F" if args.temp is not None else ''
    wind_label = (f"  Wind:       {args.wind_speed} mph {args.wind_dir}"
                  if args.wind_speed is not None else '')

    bar = '=' * 50
    print(f"\n{bar}")
    print(f"  {player['fullName']}  |  {venue}")
    print(f"  Last game in dataset: {df['date'].iloc[-1].date()}")
    if pitcher_label:
        season = df['season'].iloc[-1]
        p_stats = get_pitcher_season_stats(pitcher_id)
        p_sc    = get_pitcher_statcast(pitcher_id, season)
        b_sc    = get_batter_statcast(player['id'], season)
        bvp     = get_bvp(player['id'], pitcher_id)

        print(f"  Pitcher:    {pitcher_label}  "
              f"ERA {p_stats['opp_era']:.2f}  WHIP {p_stats['opp_whip']:.2f}  "
              f"K% {p_stats['opp_k_pct']:.1%}")
        print(f"  Pitch mix (thrown):  "
              f"FB {p_sc['pitcher_fb_thrown_pct']:.0%}  "
              f"BK {p_sc['pitcher_bk_thrown_pct']:.0%}  "
              f"OS {p_sc['pitcher_os_thrown_pct']:.0%}")
        print(f"  Barrel% allowed:     "
              f"FB {p_sc['pitcher_fb_barrel_pct']:.1%}  "
              f"BK {p_sc['pitcher_bk_barrel_pct']:.1%}  "
              f"OS {p_sc['pitcher_os_barrel_pct']:.1%}")
        print(f"  Batter pitch mix (seen):  "
              f"FB {b_sc['batter_fb_seen_pct']:.0%}  "
              f"BK {b_sc['batter_bk_seen_pct']:.0%}  "
              f"OS {b_sc['batter_os_seen_pct']:.0%}")
        print(f"  Batter barrel%:      "
              f"FB {b_sc['batter_fb_barrel_pct']:.1%}  "
              f"BK {b_sc['batter_bk_barrel_pct']:.1%}  "
              f"OS {b_sc['batter_os_barrel_pct']:.1%}")
        if bvp['bvp_ab'] > 0:
            print(f"  BvP:        {bvp['bvp_ab']} AB  .{int(bvp['bvp_avg']*1000):03d} AVG  {bvp['bvp_hr']} HR")
    if park_label:
        print(park_label)
    if temp_label:
        print(temp_label)
    if wind_label:
        print(wind_label)
    print(bar)
    print(f"  Predicted H + R + RBI:  {results['prediction']:.2f}")
    print(f"  Model MAE:              {results['cv_mae']:.3f}")
    print(bar)
    print("  MAE = mean absolute error from cross-validation (lower is better)")

    show_recent_form(df)


if __name__ == '__main__':
    main()
