#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import random

from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

import read_alg


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
    mastered = db.Column(db.Boolean)

    def __init__(self, word_id, id_in_quiz, mastered=False):
        self.id_in_quiz = id_in_quiz
        self.word_id = word_id
        self.mastered = mastered


def render_redirect(redirect_url, redirect_template='redirect.html',
                    message='', delay=1):
    return render_template(
        redirect_template,
        redirect_url=redirect_url,
        message=message,
        delay=delay
    )


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/reader', methods=['GET', 'POST'])
def reader():
    keys = set(request.args.keys())
    args = request.args

    if request.method == 'GET':
        if keys == set():
            return render_template('reader.html')

        elif keys == {'url'}:
            url = args['url']
            return read_alg.read(url)

    elif request.method == 'POST':
        form = request.form
        article = form['article']
        words = Word.query.all()
        spellings = set([w.spelling for w in words])
        article_words = article.lower().split()
        words_in_article = set(article_words)
        common = words_in_article.intersection(spellings)

        common_spellings = []
        common_definitions = []
        for w in words:
            s = w.spelling
            if (s in common) and not (s in common_spellings):
                common_spellings.append(s)
                common_definitions.append(w.definitions)

        return jsonify({'spellings': common_spellings, 'definitions': common_definitions})



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
    req_arg_keys = set(request.args.keys())

    if req_arg_keys == set():
        return render_template('quiz.html',
                               username=username,
                               dicts=dicts,
                               n_dicts=n_dicts)

    elif req_arg_keys == {'dictid'}:
        dict_id = req_args.get('dictid')
        lists = set([l[0] for l in db.session.query(Word.n_list).all()])
        return render_template('lists.html',
                               username=username,
                               dict_id=dict_id,
                               lists=lists)

    elif req_arg_keys == {'dictid', 'n_list'}:
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

    elif req_arg_keys == {'dictid', 'n_list', 'idinquiz'}:
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
            idinquiz=id_in_quiz
        )

    elif req_arg_keys == {'dictid', 'n_list', 'idinquiz', 'mastered'}:
        n_list = req_args.get('n_list')
        dict_id = req_args.get('dictid')
        id_in_quiz = req_args.get('idinquiz')
        masterd = req_args.get('mastered')
        test = Test.query.filter_by(id_in_quiz=id_in_quiz).first()
        test.mastered = masterd
        db.session.commit()
        return redirect(
            url_for(
                'quiz',
                username=username,
                dictid=dict_id,
                n_list=n_list,
                idinquiz=int(id_in_quiz)+1
            )
        )


if __name__ == '__main__':
    app.run()
    # db.create_all()