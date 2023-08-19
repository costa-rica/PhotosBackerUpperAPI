import logging
from logging.handlers import RotatingFileHandler
# from tr01_models import sess, Users, Rincons, RinconsPosts, UsersToRincons, \
#     RinconsPostsComments, RinconsPostsLikes, RinconsPostsCommentsLikes
from pb_models import dict_sess, dict_engine, text, Users, PhotoDirectories, \
    UsersToDirectories
import os
import re
import urlextract
from flask_login import current_user
from datetime import datetime

sess_users = dict_sess['sess_users']

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_bp_main = logging.getLogger(__name__)
logger_bp_main.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','main_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

logger_bp_main.addHandler(file_handler)
logger_bp_main.addHandler(stream_handler)


def create_dict_directory_ios(user_id, dir_id):
    # logger_bp_main.info(f"- create_dict_directory_ios: user_id: {user_id}, directory_id: {directory_id}")
    directory = sess_users.get(PhotoDirectories, dir_id)
    # logger_bp_main.info(f"- directory: {directory}")
    user_to_directory = sess_users.get(UsersToDirectories,(user_id,dir_id))
    # logger_bp_main.info(f"- user_to_directory: {user_to_directory}")
    

    dict_directory_ios = {}
    dict_directory_ios['id']=str(dir_id)
    dict_directory_ios['display_name']=directory.display_name
    dict_directory_ios['display_name_no_spaces']=directory.display_name_no_spaces
    dict_directory_ios['public_status']=directory.public
    if user_to_directory:
        dict_directory_ios['member']=True
        dict_directory_ios['permission_view']=user_to_directory.permission_view
        dict_directory_ios['permission_delete']=user_to_directory.permission_delete
        dict_directory_ios['permission_add_to_dir']=user_to_directory.permission_add_to_dir
        dict_directory_ios['permission_admin']=user_to_directory.permission_admin

    return dict_directory_ios