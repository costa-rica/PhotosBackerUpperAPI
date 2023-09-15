from flask import current_app, url_for
from flask_login import current_user
import json
# import requests
# from datetime import datetime, timedelta
from pb_models import dict_sess, Users
# import time
from flask_mail import Message
from app_package import mail
import os
# from werkzeug.utils import secure_filename
# import zipfile
import shutil
import logging
from logging.handlers import RotatingFileHandler
# import re
import pandas as pd
from datetime import datetime
import csv
from itsdangerous.url_safe import URLSafeTimedSerializer

sess_users = dict_sess['sess_users']

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_users = logging.getLogger(__name__)
logger_bp_users.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),"logs",'bp_users.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_users.addHandler(file_handler)
logger_bp_users.addHandler(stream_handler)



def create_token(user):
    # expires_sec=60*20#set to 20 minutes
    # s=Serializer(current_app.config['SECRET_KEY'], expires_sec)
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    # token = serializer.dumps({'user_id': user.id}).decode('utf-8')
    token = serializer.dumps({'user_id': user.id})
    # token = s.dumps({'user_id': user.id})# This is not right just testing to get Swift  response
    # print("token sending back: ", token)
    # print(type(token))
    return token

# #Kinetic Metrics, LLC
# def userPermission(email):
#     kmPermissions=['nickapeed@yahoo.com','test@test.com',
#         'emily.reichard@kineticmetrics.com']
#     if email in kmPermissions:
#         return (True,'1,2,3,4,5,6,7,8')
    
#     return (False,)

def send_reset_email(user):
    token = user.get_reset_token()
    logger_bp_users.info(f"current_app.config.get(MAIL_USERNAME): {current_app.config.get('MAIL_USERNAME')}")
    msg = Message('Password Reset Request',
                  sender=current_app.config.get('MAIL_USERNAME'),
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('bp_users.reset_token', token=token, _external=True)}

If you did not make this request, ignore email and there will be no change
'''

    mail.send(msg)


def send_confirm_email(email):
    if os.environ.get('CONFIG_TYPE') == 'prod':
        logger_bp_users.info(f"-- sending email to {email} --")
        msg = Message('Welcome to Dashboards and Databases',
            sender=current_app.config.get('MAIL_USERNAME'),
            recipients=[email])
        msg.body = 'You have succesfully signed up.'
        mail.send(msg)
        logger_bp_users.info(f"-- email sent --")
    else :
        logger_bp_users.info(f"-- Non prod mode, no email sent --")


def create_dict_user_ios(user_id):
    logger_bp_users.info(f"- create_dict_user: user_id: {user_id}")
    user = sess_users.get(Users, user_id)

    
    dict_user_ios = {}
    dict_user_ios['id']=str(user.id)
    dict_user_ios['email']=user.email
    dict_user_ios['username']=user.username
    # dict_user_ios['admin']=user.admin
    # dict_user_ios['rincons']=user.rincons

    return dict_user_ios

def check_user_directories(user):
    # print("- in check_user_directories(user)")
    dirs_in_db_dir = current_app.config.get('DIR_DB_PHOTOS_MAIN')

    for dir in user.directories:
        # print(f"Dir: {dir.directory.unique_dir_name}")
        users_dir_path_and_name = os.path.join(dirs_in_db_dir,dir.directory.unique_dir_name)
        # print(f"Directory to make: {users_dir_path_and_name}")
        if not os.path.exists(users_dir_path_and_name):
            os.makedirs(users_dir_path_and_name)
            logger_bp_users.info(f"Created: {users_dir_path_and_name}")

