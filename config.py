import os

class Config:
    SECRET_KEY = os.urandom(24)  # or specify your own secret key
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Password123!'
    MYSQL_DB = 'mcq'
