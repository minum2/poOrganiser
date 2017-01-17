#!/usr/bin/env python3.5
import sqlite3
from config import porg_config


def drop_tables(c):
    try:
        c.execute('DROP TABLE events')
        c.execute('DROP TABLE users')
        c.execute('DROP TABLE attendance')
        c.execute('DROP TABLE questions')
        c.execute('DROP TABLE choices')
    except sqlite3.OperationalError:
        pass


def create_tables(c):
    c.execute('''CREATE TABLE events(
        id INTEGER PRIMARY KEY,
        owner_id INTEGER,
        name TEXT NOT NULL,
        location TEXT,
        time DATETIME,
        attendance_ids BLOB);
    ''')

    c.execute('''CREATE TABLE users(
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        events_organised_ids BLOB,
        events_attending_ids BLOB);
    ''')

    c.execute('''CREATE TABLE attendance(
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        going_status TEXT NOT NULL,
        roles BLOB);
    ''')

    c.execute('''CREATE TABLE questions(
        question_id INTEGER PRIMARY KEY,
        event_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        num_choices INTEGER NOT NULL,
        preferential BOOLEAN NOT NULL,
        yet_to_vote TEXT);
    ''')

    c.execute('''CREATE TABLE choices(
        id INTEGER PRIMARY KEY,
        question_id INTEGER NOT NULL,
        choice text NOT NULL);
    ''')


def generate(c):
    drop_tables(c)
    create_tables(c)

if __name__ == '__main__':
    conn = sqlite3.connect(porg_config.DB_NAME)
    c = conn.cursor()
    generate(c)
    conn.commit()
    conn.close()
