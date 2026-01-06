# app.py
# query (For IP purposes) "How can I build a script to pull from the espn website the live stats of each hockey game, and be able to run it on a website so I can access it on my phone"
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ESPN Hidden API
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

@app.route('/')
def home():
    # This serves the actual HTML file
    return render_template('index.html')

@app.route('/api/scores')
def scores_api():
    # This acts as your custom data source
    try:
        response = requests.get(ESPN_API_URL)
        response.raise_for_status()
        data = response.json()

        games = []
        for event in data.get('events', []):
            competition = event['competitions'][0]
            status_desc = event['status']['type']['shortDetail']
            
            competitors = competition['competitors']
            home = next(c for c in competitors if c['homeAway'] == 'home')
            away = next(c for c in competitors if c['homeAway'] == 'away')

            games.append({
                "status": status_desc,
                "home_team": home['team']['displayName'],
                "home_score": home['score'],
                "home_logo": home['team']['logo'],
                "away_team": away['team']['displayName'],
                "away_score": away['score'],
                "away_logo": away['team']['logo']
            })
        return jsonify(games)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
