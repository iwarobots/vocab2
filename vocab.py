#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    privilege = db.Column(db.Integer, default=0)

    def __init__(self, username, password, privilege=0):
        self.username = username
        self.password = password
        self.privilege = privilege


class Dictionary(db.Model):
    __tablename__ = 'dicts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    words = db.relationship('Word', backref='dicts')

    def __init__(self, name):
        self.name = name


class Word(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer, primary_key=True)
    dict_id = db.Column(db.Integer, db.ForeignKey('dicts.id'))
    spelling = db.Column(db.String)
    n_def = db.Column(db.Integer)
    definitions = db.Column(db.String)

    dictionary = db.relationship('Dictionary', backref=db.backref('words'))

    def __init__(self, spelling, n_def=1, definitions=''):
        self.spelling = spelling
        self.n_def = n_def
        self.definitions = definitions


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template('sign_up.html')
    else:
        username = request.form['username']
        password = request.form['password']
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        return render_template('signed_up.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'GET':
        return render_template('sign_in.html')
    else:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if password == user.password:
            return render_template('signed_in.html', username=username)
        else:
            return render_template('login_failed.html')


@app.route('/u/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    return render_template('u.html', user=user)


if __name__ == '__main__':
    # app.run()
    db.create_all()