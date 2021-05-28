import datetime as dt
import sqlite3
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path

import pip._vendor.toml as toml


class Config:
    def __init__(self, path=Path('config.yaml')):
        self.path = path
        self.data = {}
        self.load()

    def load(self):
        self.data.clear()
        self.data.update(toml.loads(self.path.read_text(encoding='utf-8')))

    def __getattr__(self, name):
        if name in self.data:
            return Namespace(**self.data[name])
        else:
            raise AttributeError(name)


class Database:
    def __init__(self, path):
        self.path = Path(path).expanduser()
        if not self.path.exists():
            self.create_db()

    @contextmanager
    def cursor(self):
        with sqlite3.connect(str(self.path)) as conn:
            yield conn.cursor()

    def create_db(self):
        schema = [
            """CREATE TABLE posts (owner_id INTEGER NOT NULL, post_id INTEGER NOT NULL, subject TEXT, body TEXT, PRIMARY KEY (owner_id, post_id))""",
            """CREATE TABLE posts_to_send (owner_id INTEGER NOT NULL, post_id INTEGER NOT NULL, PRIMARY KEY (owner_id, post_id))""",
        ]
        with self.cursor() as curs:
            for stmt in schema:
                curs.execute(stmt)

    def get_max_post_id_for_owner(self, owner_id):
        sql = """SELECT MAX(post_id) FROM posts WHERE owner_id = ?;"""
        with self.cursor() as curs:
            curs.execute(sql, (int(owner_id),))
            row = curs.fetchone()
            return row[0] or 0

    def insert_post(self, post):
        sql1 = "INSERT INTO posts VALUES (:owner_id, :post_id, :subject, :body)"
        sql2 = "INSERT INTO posts_to_send VALUES (:owner_id, :post_id)"
        with self.cursor() as curs:
            curs.execute(sql1, post)
            curs.execute(sql2, post)


def main():
    config_path = Path()
    c = Config(config_path)
    print(c.database)
    print(c.vk)
    db = Database(c.database.path)


if __name__ == '__main__':
    main()
