#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import random

from flask import Flask, render_template, request, url_for, redirect
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

    dicts = db.relationship('Dictionary', backref='users')

    def __init__(self, username, password, privilege=0):
        self.username = username
        self.password = password
        self.privilege = privilege


class Dictionary(db.Model):
    __tablename__ = 'dicts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    n_lists = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    words = db.relationship('Word', backref='dicts')

    def __init__(self, name, n_lists=1):
        self.name = name
        self.n_lists = n_lists


class Word(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer, primary_key=True)
    dict_id = db.Column(db.Integer, db.ForeignKey('dicts.id'))
    spelling = db.Column(db.String)
    n_def = db.Column(db.Integer)
    definitions = db.Column(db.String)
    n_list = db.Column(db.Integer)

    def __init__(self, spelling, n_def=1, definitions='', n_list=1):
        self.spelling = spelling
        self.n_def = n_def
        self.definitions = definitions
        self.n_list = n_list


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    # status: stores the current status of the quiz
    # open: 1
    # closed: 0
    status = db.Column(db.Integer)

    tests = db.relationship('Test', backref='quizzes')

    def __init__(self, name, status=1):
        self.name = name
        self.status = status


class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    id_in_quiz = db.Column(db.Integer)
    word_id = db.Column(db.Integer)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'))

    def __init__(self, word_id, id_in_quiz):
        self.id_in_quiz = id_in_quiz
        self.word_id = word_id


@app.route('/')
def index():
    return render_template('index.html')


def render_redirect(redirect_url, redirect_template='redirect.html',
                    message='', delay=1):
    return render_template(
        redirect_template,
        redirect_url=redirect_url,
        message=message,
        delay=delay
    )


@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template('sign_up.html')
    else:
        username = request.form['username']
        password = request.form['password']
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        return render_redirect(
            redirect_url=url_for('index'),
            message='Signed up successfully',
        )


@app.route('/signin', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'GET':
        return render_template('sign_in.html')
    else:
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if password == user.password:
            return render_redirect(
                redirect_url=url_for('user', username=username),
                message='Signed in',
            )
        else:
            return render_redirect(
                redirect_url=url_for('sign_in'),
                message='Login failed',
            )


@app.route('/u/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    return render_template('u.html', user=user)


@app.route('/u/<username>/upload', methods=['GET', 'POST'])
def upload(username):
    user = User.query.filter_by(username=username).first()
    if request.method == 'GET':
        dicts = user.dicts
        n_dicts = len(dicts)
        return render_template('upload.html', username=username,
                               dicts=dicts, n_dicts=n_dicts)
    else:
        dict_file = request.files['dict_file']
        dict_name = request.form['dict_name']
        d = Dictionary(dict_name)
        # TODO: write into a function
        words = []
        lines = [l.decode('utf-8') for l in dict_file.readlines()]
        reader = csv.reader(lines)
        for row in reader:
            word = Word(row[0], row[1], row[2], row[3])
            words.append(word)
        d.words = words
        d.user_id = user.id
        db.session.add(d)
        db.session.commit()
        return render_redirect(
            url_for('user', username=username),
            message='Upload succeed'
        )


@app.route('/u/<username>/quiz', methods=['GET'])
def quiz(username):
    user = User.query.filter_by(username=username).first()
    dicts = user.dicts
    n_dicts = len(dicts)
    req_args = request.args
    if len(req_args) == 0:
        return render_template('quiz.html',
                               username=username,
                               dicts=dicts,
                               n_dicts=n_dicts)
    elif len(req_args) == 1:
        if 'dictid' in req_args:
            dict_id = req_args.get('dictid')
            lists = set([l[0] for l in db.session.query(Word.n_list).all()])
            return render_template('lists.html',
                                   username=username,
                                   dict_id=dict_id,
                                   lists=lists)
    elif len(req_args) == 2:
        if 'n_list' in req_args and 'dictid' in req_args:
            n_list = req_args.get('n_list')
            dict_id = req_args.get('dictid')
            quiz = Quiz.query.filter_by(name=n_list).first()
            if quiz is None:
                quiz = Quiz(n_list)
                word_ids = db.session.query(Word.id).filter_by(n_list=n_list).all()
                word_ids = [id[0] for id in word_ids]
                random.shuffle(word_ids)
                tests = []
                for i, word_id in enumerate(word_ids):
                    test = Test(word_id, i)
                    tests.append(test)
                quiz.tests = tests
                db.session.add(quiz)
                db.session.commit()
            return redirect(
                url_for(
                    'quiz',
                    username=username,
                    n_list=n_list,
                    dictid=dict_id,
                    idinquiz=0,
                )
            )
    elif len(req_args) == 3:
        if 'n_list' in req_args and 'dictid' in req_args and 'idinquiz' in req_args:
            n_list = req_args.get('n_list')
            dict_id = req_args.get('dictid')
            id_in_quiz = req_args.get('idinquiz')
            test = Test.query.filter_by(id_in_quiz=id_in_quiz).first()
            word = Word.query.filter_by(id=test.word_id).first()
            return render_template(
                'test.html',
                username=username,
                word=word,
                dictid=dict_id,
                n_list=n_list,
                next_id=int(id_in_quiz)+1,
            )


if __name__ == '__main__':
    app.run()
    # db.create_all()