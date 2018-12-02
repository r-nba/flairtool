from flask import Flask, flash, render_template, session, request, redirect, url_for, jsonify
import os
import praw
import pickle
import pandas as pd
from uuid import uuid4

client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
client_redirect = os.environ['client_redirect']
bot_id = os.environ['bot_id']
bot_secret = os.environ['bot_secret']
bot_refresh = os.environ['bot_refresh']

app = Flask(__name__)
app.secret_key = 'secret'

reddit = praw.Reddit(client_id=bot_id,
                     client_secret=bot_secret,
                     refresh_token=bot_refresh,
                     user_agent='r-nba flair app')

players = pickle.load(open('players_single.pickle', 'rb'))

@app.route('/auth/', methods=['GET'])
def auth():
    r = praw.Reddit(client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=client_redirect,
                    user_agent='r-nba flair tool')
    code = request.args.get('code')
    refresh_code = r.auth.authorize(code)
    user = r.user.me()
    session['username'] = user.name
    session['userflair_text'] = next(reddit.subreddit('nba').flair(user.name))['flair_text']
    session['userflair_class'] = next(reddit.subreddit('nba').flair(user.name))['flair_css_class']
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session['username'] = None
    return redirect(url_for('home'))


@app.route('/')
def home():
    r = praw.Reddit(client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=client_redirect,
                    user_agent='r-nba flair tool')
    state = str(uuid4())
    authorize_url = r.auth.url(['identity'], state, 'permanent')
    return render_template('players.html', data=players, authorize_url=authorize_url)


@app.route('/submit')
def submit():
    css_class = request.args.get('css_class', type=str)[6:]
    player_name = request.args.get('player_name', type=str)
    user_name = request.args.get('user_name', type=str)
    team_code = request.args.get('team_code', type=str)
    df = pd.DataFrame(players)
    team = df.team.apply(lambda x: team_code in x)
    team_df = df[team]
    player_check = team_df.loc[(team_df['name'] == player_name)]
    if player_check.empty:
        return jsonify({'error': 'Team name and Player name do not match'})
    else:
        session['userflair_text'] = player_name
        session['userflair_class'] = request.args.get('css_class', type=str)[6:]
        player_name = "[{team_code}] {player_name}".format(team_code=team_code, player_name=player_name)
        reddit.subreddit('nba').flair.set(redditor=user_name, text=player_name, css_class=css_class)
        return jsonify({'success': 'Flair set successfully!'})

@app.route('/autocomplete')
def autocomplete():
    team_input = request.args.get('team_input', type=str)
    team_input = team_input[:-1]
    df = pd.DataFrame(players)
    if team_input == 'flair-NB':
        df.loc[:,'team'] = 'NBA'
        df.drop_duplicates(inplace=True)
    elif isinstance(team_map[team_input], list):
        dfList = []
        for team_code in team_map[team_input]:
            print(team_code)
            team = df.team.apply(lambda x: team_code in x)
            team_df = df[team]
            team_df.loc[:,'team'] = team_map[team_input][0]        
            dfList.append(team_df)
        df = pd.concat(dfList)
        df = pd.DataFrame(df)
        df.drop_duplicates(inplace=True)

    p = []
    for player in df.itertuples():
        if (player.team != "TOT"):
            p.append(player.name)
    return jsonify(p)


if __name__ == "__main__":
    app.run(debug=True)

team_map = {
    'flair-Hawks': ['ATL', 'MLH', 'STL', 'TRI'],
    'flair-Celtics': ['BOS'],
    'flair-Nets': ['BRK', 'NYA', 'NYN', 'NJN', 'NJA'],
    'flair-ChaHornets': ['CHO', 'CHA', 'CHH'],
    'flair-Bulls': ['CHI'],
    'flair-Cavaliers': ['CLE'],
    'flair-Mavs': ['DAL'],
    'flair-Nuggets': ['DEN', 'DNA', 'DNR'],
    'flair-Pistons': ['DET', 'FTW'],
    'flair-Warriors': ['GSW', 'SFW', 'PHW'],
    'flair-Rockets': ['HOU', 'SDR'],
    'flair-Pacers': ['IND', 'INA'],
    'flair-Clippers': ['LAC', 'SDC', 'BUF'],
    'flair-Lakers': ['LAL', 'MNL'],
    'flair-Grizzlies': ['MEM', 'VAN'],
    'flair-Heat': ['MIA'],
    'flair-Bucks': ['MIL'],
    'flair-Timberwolves': ['MIN'],
    'flair-Pelicans': ['NOP', 'NOK', 'NOH'],
    'flair-Knicks': ['NYK'],
    'flair-Thunder': ['OKC', 'SEA'],
    'flair-Magic': ['ORL'],
    'flair-76ers': ['PHI', 'SYR'],
    'flair-Suns': ['PHO'],
    'flair-TrailBlazers': ['POR'],
    'flair-Kings': ['SAC', 'CIN', 'KCO', 'KCK', 'ROC'],
    'flair-Spurs': ['SAS', 'TEX', 'SAA', 'DLC'],
    'flair-Raptors': ['TOR'],
    'flair-Jazz': ['UTA', 'NOJ'],
    'flair-Wizards': ['WAS', 'CHZ', 'BAL', 'CAP', 'WSB', 'CHP'],
    'flair-SuperSonics': ['SEA'],
}
