@echo off
cd /d "C:\Users\Matt\OneDrive\Desktop\Claude\Sessions\mlb_props_model"
python daily_runner.py >> logs\daily_runner.log 2>&1
