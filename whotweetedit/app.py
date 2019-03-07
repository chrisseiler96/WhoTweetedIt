"""
Main Application and routing logic for WhoTweetedIt
"""

from decouple import config
from flask import Flask, render_template, request, redirect, url_for, flash
from .models import DB, TwitterUser
from .twitter import get_tweets, find_poss, predict_tweet
from .predict import predict_user

def create_app():
	""" Create and configure an instance of the Flask application."""
	app = Flask(__name__)
	app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	DB.init_app(app)


	@app.route('/')
	def root():
		users = TwitterUser.query.all()
		return render_template('root.html', title = 'Home', users=users)
	
	
	@app.route('/user/<name>')
	def read_tweets(name=None):
		tweets, user_name = get_tweets(name)
		return render_template('user.html', title=user_name, name=user_name,tweets=tweets)

	@app.route('/reset')
	def reset():
		DB.drop_all()
		DB.create_all()
		return redirect(url_for('root'))


	@app.route('/compare', methods=['POST'])
	def compare():
		user1, user2 = request.values['user1'], request.values['user2']
		if user1 == user2:
			return 'Cannot compare a user to themselves!'
		else:
			prediction = predict_user(user1, user2, request.values['tweet_text'])
			return user1 if prediction else user2

	@app.route('/search', methods=['POST'])
	def search():
		user_name = request.form.get('q')
		return find_poss(user_name)

	@app.route('/predict', methods=['POST'])
	def predict():
		text = request.form.get('text')
		user_1 = request.form.get('user_1')
		user_2 = request.form.get('user_2')
		ids, res = predict_tweet(text, user_1, user_2)
		if res[0] >= 0.5:
			return render_template('predict.html', name_1=ids[0],
                                   name_2=ids[1], res="{:.3%}".format(res[0]),
                                   tweet=text)
		return render_template('predict.html', name_1=ids[1], name_2=ids[0],
                               res="{:.3%}".format(res[1]), tweet=text)
	
	return app