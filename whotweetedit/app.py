"""
Main Application and routing logic for WhoTweetedIt
"""


from flask import Flask, render_template, request
from .models import DB


def create_app():
	""" Create and configure an instance of the Flask application."""
	app = Flask(__name__)
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
	DB.init_app(app)

	@app.route('/')
	def root():
		return render_template('base.html')



	return app