"""
Main Application and routing logic for WhoTweetedIt
"""

from decouple import config
from flask import Flask, render_template, request
from .models import DB, User


def create_app():
	""" Create and configure an instance of the Flask application."""
	app = Flask(__name__)
	app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	app.config['ENV'] = config('ENV')
	DB.init_app(app)

	@app.route('/')
	def root():
		users = User.query.all()
		return render_template('base.html', title = 'Home', users=users)

	@app.route('/reset')
	def reset():
		DB.drop_all()
		DB.create_all()
		return render_template('base.html', title='DB Reset!', users=[])

	return app