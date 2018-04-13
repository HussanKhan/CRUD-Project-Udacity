#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
from flask import make_response, jsonify, flash
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Games
from sqlalchemy import create_engine, asc
from flask import session as current_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

engine = create_engine('sqlite:///videogame.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


def retrieve_table(name):
    table = session.query(name).all()
    return table


def retrieve_table_filter(tablename, attr, name):
    table = session.query(tablename).filter_by(attr=name).all()
    return table


@app.route('/login')
def user_login():
    content = string.ascii_uppercase + string.digits
    state_token = ''.join(random.choice(content) for x in xrange(32))
    current_session['state'] = state_token
    return render_template('login.html', STATE=state_token)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check to make sure we recived same state token
    # from /gconnect?state=xxxxxxxxxxxxxxxxxxxxxxxxxxx
    if request.args.get('state') != current_session['state']:
        response = make_response(json.dumps('INVALID STATE TOKEN'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Stored data from client here
    code = request.data

    # try to exhange token from client for access token from Google
    try:
        auth_flow = flow_from_clientsecrets(
            '''client_secret.json''', scope='')
        auth_flow.redirect_uri = 'postmessage'
        credentials = auth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(json.dumps('FLOW EXCHANGE ERROR'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify access token
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dump(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    g_id = credentials.id_token['sub']

    if result['user_id'] != g_id:
        response = make_response(
                    json.dumps('TOKEN USER ID DOES NOT MATCH'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    api1_id = '1042477957154-m19nsa3matbjbe61are8vta5e278onpp'
    api2_id = '.apps.googleusercontent.com'
    if result['issued_to'] != api1_id + api2_id:
        response = make_response(json.dumps('CLIENT ID DOES NOT MATCH'), 401)
        print('client id does not match')
        response.headers['Content-Type'] = 'application/json'
        return response

    # Is user already logged in?
    stored_credentials = current_session.get('credentials')
    stored_g_id = current_session.get('g_id')

    if stored_credentials is not None and g_id == stored_g_id:
        response = make_response(json.dumps('USER ALREADY LOGGED IN'), 200)
        response.headers['Content-Type'] = 'application/json'


# store for current session
    current_session['access_token'] = credentials.access_token
    current_session['g_id'] = g_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    current_session['username'] = data['name']
    current_session['email'] = data['email']

    # check to see if user exists, if they don't, add them to database

    check = session.query(User).filter_by(
            username=current_session['email']).all()

    if not check:
        add_user = User(username=current_session['email'])
        session.add(add_user)
        session.commit()
        check = session.query(User).filter_by(
                username=current_session['email']).one()
        print(check.username)
    else:
        pass
    flash('LOGGED IN SUCCESSFULLY')
    return "DONE"


@app.route('/gdisconnect')
def gdisconnect():
    print('G DISCONNECT RUN')
    # Making sure to only disconnect this user
    access_token = current_session.get('access_token')
    if access_token is None:
        flash('NO USER LOGGED IN')
        return redirect(url_for('homepage'))

    # if there is a token, send it to google to revoke it
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    # If good response recieved delete variables stored for user
    if result['status'] == '200':
        del current_session['username']
        del current_session['email']
        flash('SIGNED OUT')
        return redirect(url_for('homepage'))
    else:
        # if I got an error or other than 200
        response = make_response(json.dumps('''Failed to revoke
                                               token for given user.''', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/home')
def homepage():
    genre_list = []
    game_title = retrieve_table(Games)
    for game in game_title:
        if game.genre in genre_list:
            pass
        else:
            genre_list.append(game.genre)
    return render_template('homepage.html', genre_list=sorted(genre_list),
                           user=current_session.get('email'))


@app.route('/<path:genre>')
def list_games(genre):
    filtered_game = session.query(Games).filter_by(genre=str(genre)).all()
    return render_template('games_list.html', filtered_game=filtered_game,
                           user=current_session.get('email'))


@app.route('/<path:genre>/<int:id>/<path:gametitle>')
def show_trailer(genre, gametitle, id):
    game_trailer = session.query(Games).filter_by(id=id).first()
    filtered_game = session.query(Games).filter_by(genre=str(genre)).all()

    # Making stored youtube link embedable
    trailer_link = game_trailer.trailers
    fix = trailer_link.replace('/watch?v=', '/embed/')
    end_link = '?rel=0&amp;controls=0&amp;showinfo=0'
    the_link = 'https://www.youtube.com' + fix + end_link
    sumy = game_trailer.summary

    # Appending wiki links
    wiki_app = '<a href="https://en.wikipedia.org'

    return render_template('show_trailer.html', thelink=the_link,
                           more_info=game_trailer.more_info,
                           similar_games=filtered_game,
                           g=game_trailer,
                           summary=sumy.replace('<a href="', wiki_app),
                           user=current_session.get('email'))


@app.route('/create')
def create_new():
    if current_session.get('email'):
        genre_list = []
        game_title = session.query(Games).all()
        for game in game_title:
            if game.genre in genre_list:
                pass
            else:
                genre_list.append(game.genre)
        return render_template('create_entry.html',
                               genre_list=sorted(genre_list),
                               user=current_session.get('email'))
    else:
        flash('MUST BE LOGGED IN TO CREATE NEW ENTRY')
        return redirect(url_for('user_login'))


@app.route('/create', methods=['POST'])
def create_new_post():
    if request.method == 'POST' and current_session.get('email'):
        # Extracting data from form
        title = request.form.get('Title')
        genre = request.form.get('genre')
        more_info = request.form.get('wikilink')
        summary = request.form.get('summary')
        trailers = request.form.get('Trailer')
        trailers = trailers.replace('https://www.youtube.com', '')
        theuser = session.query(User).filter_by(
                                username=current_session['email']).one()
        creation = Games(title=title.title(),
                         genre=genre,
                         more_info=str(more_info),
                         trailers=trailers,
                         user_id=theuser.id,
                         summary=str(summary))

        session.add(creation)
        session.commit()
        flash('GAME SUCCESSFULLY ADDED')
        return redirect(url_for('homepage'))
    else:
        return redirect('/create')


@app.route('/<path:genre>/<int:id>/<path:gametitle>/edit')
def edit_game(genre, gametitle, id):
    if current_session.get('email'):
        userid = session.query(User).filter_by(
                               username=current_session.get('email')).one()

        user_game = session.query(Games).filter_by(title=gametitle).one()

        if userid.id == user_game.user_id:
            # Oddly named because of variable conflict
            gamee = session.query(Games).filter_by(title=gametitle).one()
            print(gamee.title)
            genre_list = []
            gamee_title = session.query(Games).all()
            for game in gamee_title:
                if game.genre in genre_list:
                    pass
                else:
                    genre_list.append(game.genre)
            genre_list.remove(gamee.genre)
            title = gamee.title
            return render_template('edit_entry.html', game=gamee,
                                   genre_list=genre_list,
                                   title=title)
        else:
            flash('YOUR ACCOUNT DOES NOT HAVE PERMISSION TO EDIT THIS GAME')
            return redirect('/' + str(genre) + '/' + str(id) +
                            '/' + str(gametitle))

    else:
        flash('MUST BE LOGGED IN TO EDIT GAME')
        return redirect(url_for('user_login'))


@app.route('/<path:genre>/<int:id>/<path:gametitle>/edit', methods=['POST'])
def ret_edited_game(genre, id, gametitle):
    userid = session.query(User).filter_by(
                           username=current_session.get('email')).one()

    user_game = session.query(Games).filter_by(title=gametitle).one()

    if request.method == 'POST' and userid.id == user_game.user_id:
        the_game = session.query(Games).filter_by(id=id).one()
        tl = request.form.get('Title')
        gen = request.form.get('genre')
        more = request.form.get('wikilink')
        summ = request.form.get('summary')
        trail = request.form.get('Trailer')
        trail = trail.replace('https://www.youtube.com', '')

        # Assigning new values to selected row
        the_game.title = tl
        the_game.genre = gen
        the_game.more_info = more
        the_game.summary = summ
        the_game.trailers = trail

        session.add(the_game)
        session.commit()

        flash('GAME SUCCESSFULLY EDITED')
        return redirect(url_for('homepage'))
    else:
        return redirect('/' + str(genre) + '/' + str(id) +
                        '/' + str(gametitle))


@app.route('/<path:genre>/<int:id>/<path:gametitle>/delete')
def delete_game(genre, gametitle, id):
    the_game = session.query(Games).filter_by(title=gametitle).one()
    if current_session.get('email'):
        userid = session.query(User).filter_by(
                               username=current_session.get('email')).one()
    else:
        flash('MUST BE LOGGED IN TO DELETE')
        return redirect(url_for('user_login'))

    if the_game.user_id == userid.id:
        ana = session.query(Games).filter_by(title=gametitle).one()
        session.delete(ana)
        session.commit()
        flash('SUCCESSFULLY DELETED: ' + str(ana.title))
        return redirect(url_for('homepage'))
    else:
        flash('YOUR ACCOUNT DOES NOT HAVE PERMISSION TO DELETE THIS GAME')
        return redirect('/' + str(genre) + '/' + str(id) +
                        '/' + str(gametitle))


@app.route('/<path:genre>/json')
def json_response(genre):
    # Moba stored in all caps in database
    if genre == 'moba':
        genre = 'MOBA'
    else:
        genre = genre.capitalize()
    games = session.query(Games).filter_by(genre=genre).all()
    return jsonify(Games=[g.serialize for g in games])


if __name__ == '__main__':
    app.secret_key = 'Udacity_Project'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
