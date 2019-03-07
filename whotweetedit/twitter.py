"""Retrieve Tweets, Embeddings and persist in the database"""


import basilica
import tweepy
import numpy as np
import pickle
from sqlalchemy.sql import text
from sklearn.linear_model import LogisticRegression
from flask import jsonify
from decouple import config
from .models import DB, Tweet, TwitterUser, PredictModel

TWITTER_AUTH = tweepy.OAuthHandler(config('TWITTER_CONSUMER_KEY'), config('TWITTER_CONSUMER_SECRET'))

TWITTER_AUTH.set_access_token(config('TWITTER_ACCESS_TOKEN'), config('TWITTER_ACCESS_TOKEN_SECRET'))

TWITTER = tweepy.API(TWITTER_AUTH)


BASILICA = basilica.Connection(config('BASILICA_KEY'))


def add_user(user_id):
    print("ADDING:", user_id)
    t_user = TWITTER.get_user(user_id=user_id)
    tweets = t_user.timeline(count=200, exclude_replies=True, include_rts=False, tweet_mode='extended')
    n_user = TwitterUser(id=t_user.id, name=t_user.screen_name,newest_tweet_id=tweets[0].id)
    DB.session.add(n_user)
    for tweet in tweets:
        embedding = BASILICA.embed_sentence(tweets[0].full_text, model="twitter")
        n_tweet = Tweet(id=tweet.id, text=tweet.full_text, embedding=embedding, user_id=tweet.author.id, user=n_user)
        DB.session.add(n_tweet)
        DB.session.commit()
    return t_user.screen_name, t_user.id


def get_tweets(name):
    name = int(name)
    statement = text("""SELECT name, id FROM twitter_user WHERE id=:id""")
    data = {"id": name}
    rs = DB.engine.execute(statement, **data)
    user_id = None
    user_name = None
    for tup in rs:
        if name == tup[1]:
            user_name = tup[0]
            user_id = tup[1]
            break
    tweets = None
    if user_id is None:
        user_name, user_id = add_user(int(name))
    statement = text("""SELECT text
        FROM tweet
        WHERE user_id=:user_id""")
    data = {"user_id": user_id}
    rs = DB.engine.execute(statement, **data)
    tweets = [x[0] for x in rs]
    return tweets, user_name




def find_poss(user_name):
    res = TWITTER.search_users(user_name, 5)
    res = [{"name": x.screen_name, "id": x.id} for x in res]
    return jsonify(res)


def predict_tweet(full_text, user_1, user_2):
    def learn_model(local_x, other_x):
        X = np.array(local_x[0]).reshape(1, len(local_x[0]))
        Y = [1]
        for x in local_x[1:]:
            X = np.append(X, np.array(x).reshape(1, len(x)), axis=0)
            Y.append(1)
        for x in other_x:
            X = np.append(X, np.array(x).reshape(1, len(x)), axis=0)
            Y.append(0)
        return LogisticRegression().fit(X, Y)

    embedding = BASILICA.embed_sentence(full_text, model="twitter")
    statement = text("""SELECT name, id FROM twitter_user""")
    rs = DB.engine.execute(statement)
    user_id_1 = None
    user_id_2 = None
    for tup in rs:
        if user_1.upper() == tup[0].upper():
            user_id_1 = tup[1]
        elif user_2.upper() == tup[0].upper():
            user_id_2 = tup[1]
        if user_id_1 is not None and user_id_2 is not None:
            break
    if user_id_1 is not None and user_id_2 is not None:
        statement = text("""SELECT embed
            FROM predict_model
            WHERE
                user_id_1=:id1
                AND user_id_2=:id2""")
        ids = sorted([user_id_1, user_id_2])
        data = {"id1": ids[0], "id2": ids[1]}
        db_res = DB.engine.execute(statement, **data)
        rs = [pickle.loads(x[0]) for x in db_res]
        if len(rs) == 0:
            statement = text("""SELECT embedding
                FROM tweet
                WHERE
                    user_id=:user_id""")
            data = {"user_id": ids[0]}
            rs = list(DB.engine.execute(statement, **data))
            local_x = [pickle.loads(x[0]) for x in rs]
            data = {"user_id": ids[1]}
            rs = list(DB.engine.execute(statement, **data))
            other_x = [pickle.loads(x[0]) for x in rs]
            m = learn_model(local_x, other_x)
            n_model = PredictModel(user_id_1=ids[0], user_id_2=ids[1], embed=m)
            DB.session.add(n_model)
            DB.session.commit()
        else:
            m = rs[0]
        id_names = [user_2, user_1]
        if user_id_1 == ids[0]:
            id_names = [user_1, user_2]
        return (id_names,
                m.predict_proba(np.array(embedding).reshape(1, -1))[0])