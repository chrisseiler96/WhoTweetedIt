"""SQLAlchemy models for WhoTweetedIt"""
from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()

class TwitterUser(DB.Model):
	"""Twitter users that we pull and analyze Tweets for."""
	id = DB.Column(DB.BigInteger, primary_key=True)
	name = DB.Column(DB.String(15), nullable=False)
	newest_tweet_id = DB.Column(DB.BigInteger)

	def __repr__(self):
		return '<User {}>'.format(self.name)

class Tweet(DB.Model):
	'''Tweets'''
	id = DB.Column(DB.BigInteger, primary_key=True)
	text = DB.Column(DB.Unicode(500))
	embedding = DB.Column(DB.PickleType, nullable = False)
	user_id = DB.Column(DB.BigInteger, DB.ForeignKey('twitter_user.id'), nullable=False)
	user = DB.relationship('TwitterUser', backref=DB.backref('twitter_user', lazy=True))

	def __repr__(self):
		return '<Tweet {}>'.format(self.text)


class PredictModel(DB.Model):
    """Scikit-Learn Logistic Regression model for predicting probability of
    twitter text to user."""
    id = DB.Column(DB.Integer, primary_key=True)
    user_id_1 = DB.Column(DB.BigInteger, DB.ForeignKey('twitter_user.id'),
                          nullable=False)
    user_id_2 = DB.Column(DB.BigInteger, DB.ForeignKey('twitter_user.id'),
                          nullable=False)
    embed = DB.Column(DB.PickleType, nullable=False)