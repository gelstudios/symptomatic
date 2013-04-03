#! /usr/bin/env python

from flask import Flask, render_template, request, url_for, redirect, session
from flask_oauth import OAuth
import os
import mongo
import datetime

app = Flask(__name__) 

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

oauth = OAuth()
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key="109598425902918",
    consumer_secret="21599ff47fc62fcbee95a5b3453f5a63",
    request_token_params={'scope': 'email'}
)


@facebook.tokengetter
def get_facebook_token(token=None):
	return session.get('facebook_token')

@app.route('/oauth-authorized')
@facebook.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['facebook_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    session['facebook_user'] = resp['screen_name']

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect('/show_symptoms')

@app.route('/')
def index():
	return redirect(url_for('login'))

@app.route('/login')
def login():
    return facebook.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

# Handler for HTTP POST to http://symptomatic.me/messages
@app.route('/messages', methods=['GET', 'POST'])
def on_incoming_message():
	if request.method == 'POST':
		sender = request.form.get('sender')
		recipient = request.form.get('recipient')

		body_plain = request.form.get('body-plain', '')
		timestamp = request.form.get('timestamp', '')

		mongo.saving_email(timestamp, sender, body_plain.splitlines(), body_plain)

		return "OK"
		

@app.route('/show_symptoms', methods=['GET', 'POST'])
def show_symptoms():
	if request.method == 'GET':
		return render_template('select.html')
	else:
		if request.form.get('Submit'):
			email = request.form.get('email')
			
			start_date = request.form.get('start_date')
			end_date = request.form.get('end_date')

			if not start_date and end_date and email:
				return render_template('select.html')

			#converts date into datetime object to be able to compare
			start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
			end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d") 
 
 			#timedelta(1) adds one day to end_datetime compare the entire day
			symptoms = mongo.reading_email(email, start_datetime, end_datetime + datetime.timedelta(1))
			return render_template('show_symptoms.html', start_date=start_date, end_date=end_date, symptoms=symptoms)
		
		elif request.form.get("Find All"):
			email = request.form.get('email')
			if not email:
				return render_template('select.html')

			symptoms = mongo.reading_email(email, None, None, True)
			return render_template('show_symptoms.html', start_date=None, end_date=None, symptoms=symptoms)


if __name__ == '__main__':
	#port = int(os.environ.get('PORT', 5000))
	app.run(debug=True)#, host='0.0.0.0', port=port)