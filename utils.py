#!/usr/bin/env python
# -*- coding: utf-8 -*-


from vocab import db, User


def create_db():
    db.create_all()
    user = User('derek', '1', -1)
    db.session.add(user)
    db.session.commit()


if __name__ == '__main__':
    create_db()