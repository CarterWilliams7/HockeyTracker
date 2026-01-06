# app.py
# query (For IP purposes) "How can I build a script to pull from the espn website the live stats of each hockey game, and be able to run it on a website so I can access it on my phone"

import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# The hidden ESPN API endpoint for NHL scores
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

def get_live_scores():
    try:
        # Fetch data from ESPN
        response = requests.get(ESPN_API_URL)
        response.raise_for_status()
        data = response.json()

        games = []
        
        # Loop through each game event
        for event in data.get('events', []):
            competition = event['competitions'][0]
            status_desc = event['status']['type']['detail'] # e.g., "Final", "2nd Period - 10:00"
            short_status = event['status']['type']['shortDetail'] # e.g. "Final", "2nd 10:00"

            # Get competitors (Home vs Away)
            competitors = competition['competitors']
            home_team = next(c for c in competitors if c['homeAway'] == 'home')
            away_team = next(c for c in competitors if c['homeAway'] == 'away')

            game_info = {
                "matchup": event['name'],
                "status": short_status,
                "home_team": home_team['team']['displayName'],
                "home_score": home_team['score'],
                "home_logo": home_team['team']['logo'],
                "away_team": away_team['team']['displayName'],
                "away_score": away_team['score'],
                "away_logo": away_team['team']['logo']
            }
            games.append(game_info)
            
        return games
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

@app.route('/')
def index():
    games = get_live_scores()
    return render_template_string(HTML_TEMPLATE, games=games)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
