import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ESPN Endpoints
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={}"
SEARCH_URL = "https://site.api.espn.com/apis/common/v3/search?sport=hockey&league=nhl&query={}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search')
def search_player():
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify([])
    
    try:
        # Search ESPN's database
        resp = requests.get(SEARCH_URL.format(query)).json()
        results = []
        
        for item in resp.get('items', []):
            # Only look for actual athletes
            if 'entity' in item and 'displayName' in item['entity']:
                player = item['entity']
                # Try to find the team name
                team = "Free Agent"
                if 'competitors' in player and len(player['competitors']) > 0:
                    team = player['competitors'][0]['team']['displayName']
                
                results.append({
                    "name": player['displayName'],
                    "team": team,
                    "id": player['id']
                })
        return jsonify(results)
    except Exception as e:
        print(e)
        return jsonify([])

@app.route('/api/track', methods=['POST'])
def track_bets():
    # Receive the list of bets from the frontend
    user_bets = request.json 
    
    # 1. Fetch the Scoreboard ONCE (Efficiency)
    scoreboard = requests.get(SCOREBOARD_URL).json()
    
    # Helper to find game ID based on team name
    def find_game(team_name):
        for event in scoreboard.get('events', []):
            short_name = event['shortName']
            # Match team name loosely
            if team_name.split()[-1].lower() in short_name.lower():
                return event['id'], event['status']['type']['shortDetail']
        return None, "No Game"

    results = []

    # 2. Process each bet
    for bet in user_bets:
        player_name = bet['player']
        team_name = bet['team']
        stat_type = bet['stat'] # 'goals', 'assists', 'shots', 'points'
        target = float(bet['target'])
        
        game_id, status = find_game(team_name)
        current_val = 0
        
        if game_id:
            try:
                # Fetch specific game stats
                box = requests.get(SUMMARY_URL.format(game_id)).json()
                players = box.get('boxscore', {}).get('players', [])
                
                found = False
                for team_section in players:
                    for athlete in team_section.get('statistics', []):
                        for p in athlete.get('athletes', []):
                            if p['athlete']['displayName'] == player_name:
                                stats = p['stats'] # [Goals, Assists, Shots, +/-]
                                # Map stats
                                goals = int(stats[0])
                                assists = int(stats[1])
                                shots = int(stats[2])
                                
                                if stat_type == 'goals': current_val = goals
                                elif stat_type == 'assists': current_val = assists
                                elif stat_type == 'shots': current_val = shots
                                elif stat_type == 'points': current_val = goals + assists
                                
                                found = True
                                break
                    if found: break
            except:
                pass # Keep 0 if error

        # Check Winner
        is_hit = current_val >= target # Assume "Over" logic (e.g. 2+ goals means >= 2)
        if stat_type == 'shots': # Shots are usually Over 2.5
             if current_val > target: is_hit = True

        results.append({
            "id": bet['id'], # Pass back the ID so frontend knows which card to update
            "current": current_val,
            "status": status,
            "is_hit": is_hit
        })
        
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)