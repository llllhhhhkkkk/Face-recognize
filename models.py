from app import app, db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Document, UserMixin):
    meta = {
        "collection": "user",
        "ordering": ["-id"],
        "strict": True
    }
    gender = db.StringField()
    username = db.StringField()
    password_hash = db.StringField()
    nickname = db.StringField()
    email = db.StringField()
    age = db.StringField()
    phone = db.StringField()
    birthday = db.StringField()
    avatar = db.StringField()

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.save()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Time(db.Document):
    meta = {
        "collection": "time",
        "ordering": ["-id"],
        "strict": True
    }
    nickname = db.StringField()
    name = db.StringField()
    year = db.StringField()
    month = db.StringField()
    date = db.StringField()
    hour = db.StringField()
    minute = db.StringField()
    second = db.StringField()


class UserComment(db.Document):
    meta = {
        "collection": "userComment",
        "ordering": ["-id"],
        "strict": True
    }
    avatar = db.StringField()
    name = db.StringField()
    nickname = db.StringField()
    info = db.StringField()
    year = db.StringField()
    month = db.StringField()
    date = db.StringField()
    hour = db.StringField()
    minute = db.StringField()


class UserReplay(db.Document):
    meta = {
        "collection": "userReplay",
        "ordering": ["-id"],
        "strict": True
    }
    userId = db.StringField()
    avatar = db.StringField()
    name = db.StringField()
    content = db.StringField()
    userIdBack = db.StringField()
    userNameBack = db.StringField()


class User_Manager(db.Document, UserMixin):
    meta = {
        "collection": "user_manager",
        "ordering": ["-id"],
        "strict": True
    }
    gender = db.StringField()
    username = db.StringField()
    password_hash = db.StringField()
    nickname = db.StringField()
    email = db.StringField()
    age = db.StringField()
    phone = db.StringField()
    birthday = db.StringField()
    avatar = db.StringField()

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.save()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
