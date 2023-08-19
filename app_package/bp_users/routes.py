
from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response, \
        jsonify
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from pb_models import dict_sess, dict_engine, text, Users, PhotoDirectories, UsersToDirectories

from app_package.bp_users.utils import send_reset_email, send_confirm_email, \
    create_token, create_dict_user_ios
from app_package.bp_main.utils import create_dict_directory_ios
import datetime
import requests
from app_package.token_decorator import token_required

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_users = logging.getLogger(__name__)
logger_bp_users.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','bp_users.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_users.addHandler(file_handler)
logger_bp_users.addHandler(stream_handler)


salt = bcrypt.gensalt()


bp_users = Blueprint('bp_users', __name__)
sess_users = dict_sess['sess_users']

# @bp_users.before_request
# def before_request():
#     logger_bp_users.info("- in bp_users.before_request ")
#     ###### Keeps user logged in 31 days ########
#     session.permanent = True
#     current_app.permanent_session_lifetime = datetime.timedelta(days=31)
#     session.modified = True
#     logger_bp_users.info(f"!--> current_app.permanent_session_lifetime: {current_app.permanent_session_lifetime}")
#     ###### END Keeps user logged in 31 days ######## 
#     ###### TEMPORARILY_DOWN: redirects to under construction page ########
#     if os.environ.get('TEMPORARILY_DOWN') == '1':
#         if request.url != request.url_root + url_for('bp_main.temporarily_down')[1:]:
#             # logger_bp_users.info("*** (logger_bp_users) Redirected ")
#             logger_bp_users.info(f'- request.referrer: {request.referrer}')
#             logger_bp_users.info(f'- request.url: {request.url}')
#             return redirect(url_for('bp_main.temporarily_down'))



@bp_users.route('/login', methods = ['GET', 'POST'])
def login():
    logger_bp_users.info(f"-- in user/login route --")

    data_headers = request.headers
    logger_bp_users.info(f"--- current app SQL_URI_USERS: {current_app.config.get('SQL_URI_USERS')}")

    try:
        auth = request.authorization
    except:
        return jsonify({"status": "Auth not read-able."})

    if not auth or not auth.username or not auth.password:
        logger_bp_users.info("auth not sent")
        return make_response('Could not verify', 400, {'message' : 'missing auth body i.e. need auth= (username, password)'})
    user = sess_users.query(Users).filter_by(email = auth.username).first()
    
    if not user:
        return make_response('Could note verify - user not found', 401, {'message' : f'{auth.username} is not a user'})

    if bcrypt.checkpw(auth.password.encode(), user.password):

        token = create_token(user)
        user_directories = [[str(i.directory.id), i.directory.display_name, i.directory.display_name_no_spaces] for i in user.directories]
        # user_rincons = create_dict_rincon_ios(user_id, rincon_id)
        
        user_dirs_ios = []
        for dir_info in user_directories:
            user_dirs_ios.append(create_dict_directory_ios(user.id, dir_info[0]))
            # logger_bp_users.info(f"--- user_rincons_w_permisssions: {user_rincons}")
        # return jsonify({'token': token,'user_id':str(user.id), 'user_dirs': user_dirs_ios})
        dict_user_ios = create_dict_user_ios(user.id)
        # dict_user_ios={}
        dict_user_ios['token'] = token
        dict_user_ios['user_directories'] = user_dirs_ios


        logger_bp_users.info(f"--- dict_user_ios: {dict_user_ios}")
        return jsonify(dict_user_ios)

    return make_response('Could not verify', 401, {'message' : 'email/password are not valid'})

@bp_users.route('/register', methods = ['GET', 'POST'])
def register():
    logger_bp_users.info(f"-- in register route --")

    data_headers = request.headers

    try:
        request_json = request.json
        print("request_json:",request_json)
    except Exception as e:
        logger_bp_users.info(e)
        return jsonify({"status": "httpBody data recieved not json not parse-able."})
        
    new_email = request_json.get('new_email')

    check_email = sess_users.query(Users).filter_by(email = new_email).all()
    if len(check_email)==1:
        logger_bp_users.info(f"- email already in database -")
        existing_emails = [i.email for i in sess_users.query(Users).all()]
        # logger_bp_users.info(f"- sending: {jsonify({'existing_emails': existing_emails})} -")
        return jsonify({"existing_emails": existing_emails})

    hash_pw = bcrypt.hashpw(request_json.get('new_password').encode(), salt)
    new_user = Users(email = new_email, password = hash_pw)
    try:
        sess_users.add(new_user)
        sess_users.commit()
    except:
        return jsonify({"status": f"failed to add to database."})

    
    logger_bp_users.info(f"- new_user.id: {new_user.id} for email: {new_user.email} -")

    # create new user dir
    unique_dir_name = str(new_user.id) + "_" + new_user.username
    new_dir_path_and_name = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), unique_dir_name)
    display_name = new_user.username+"'s photos"
    display_name_no_spaces = display_name.replace(" ", "_")

    if not os.path.exists(new_dir_path_and_name):
        os.makedirs(new_dir_path_and_name)
        logger_bp_users.info(f"Created: {unique_dir_name}")

    # add dir to PhotoDirectories
    new_dir = PhotoDirectories(unique_dir_name=unique_dir_name, display_name=display_name,
            display_name_no_spaces=display_name_no_spaces)
    sess_users.add(new_dir)
    sess_users.commit()
    logger_bp_users.info(f"- new_user dir: {new_dir.unique_dir_name}, display_name: {new_dir.unique_dir_name} ---")
    # ad dir to Ust To Dir
    new_user_to_dir = UsersToDirectories(user_id=new_user.id,directory_id=new_dir.id,
        permission_delete=True, permission_add_to_dir=True, permission_admin=True)
    sess_users.add(new_user_to_dir)
    sess_users.commit()
    logger_bp_users.info(f"- new_user is member of : {new_dir.display_name} ---")

    new_user_dict_response = {}
    new_user_dict_response["id"]=str(new_user.id)
    new_user_dict_response["email"]=new_user.email
    new_user_dict_response["username"]=new_user.username

    logger_bp_users.info('- successfully added new user, sending response')
    logger_bp_users.info(new_user_dict_response)

    return jsonify(new_user_dict_response)

@bp_users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('bp_main.home'))

@bp_users.route('/reset_password', methods = ["GET", "POST"])
def reset_password():
    page_name = 'Request Password Change'
    if current_user.is_authenticated:
        return redirect(url_for('bp_main.user_home'))
    # form = RequestResetForm()
    # if form.validate_on_submit():
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')
        user = sess_users.query(Users).filter_by(email=email).first()
        if user:
        # send_reset_email(user)
            logger_bp_users.info('Email reaquested to reset: ', email)
            send_reset_email(user)
            flash('Email has been sent with instructions to reset your password','info')
            # return redirect(url_for('bp_users.login'))
        else:
            flash('Email has not been registered with What Sticks','warning')

        return redirect(url_for('bp_users.reset_password'))
    return render_template('users/reset_request.html', page_name = page_name)

@bp_users.route('/reset_password/<token>', methods = ["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('bp_main.user_home'))
    user = Users.verify_reset_token(token)
    logger_bp_users.info('user::', user)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('bp_users.reset_password'))
    if request.method == 'POST':

        formDict = request.form.to_dict()
        if formDict.get('password_text') != '':
            hash_pw = bcrypt.hashpw(formDict.get('password_text').encode(), salt)
            user.password = hash_pw
            sess_users.commit()
            flash('Password successfully updated', 'info')
            return redirect(url_for('bp_users.login'))
        else:
            flash('Must enter non-empty password', 'warning')
            return redirect(url_for('bp_users.reset_token', token=token))

    return render_template('users/reset_request.html', page_name='Reset Password')


# ########################
# # recaptcha
# ########################

# @bp_users.route("/sign-user-up", methods=['POST'])
# def sign_up_user():
#     # print(request.form)
#     secret_response = request.form['g-recaptcha-response']

#     verify_response = requests.post(url=f"{current_app.config.get('VERIFY_URL_CAPTCHA')}?secret={current_app.config.get('SECRET_KEY_CAPTCHA')}&response={secret_response}").json()
#     print(verify_response)
#     if verify_response['success'] == False or verify_response['score'] < 0.5:
#         abort(401)

#     formDict = request.form.to_dict()
#     print(formDict)
    
#     # get email, name and message

#     senders_name = formDict.get('name')
#     senders_email = formDict.get('email')
#     senders_message = formDict.get('message')

#     #send message to nick@dashanddata.com

#     # Send email confirming succesfully sent message to nick@dashanddata.com
#     try:
#         send_message_to_nick(senders_name, senders_email, senders_message)
#     except:
#         print('*** not successsuflly send_message_to_nick ***')
#     try:
#         send_confirm_email(senders_name, senders_email, senders_message)
#     except:
#         print('*** not successsuflly send_confirm_email')
#         flash(f'Problem with email: {new_email}', 'warning')
#         return redirect(url_for('bp_users.login'))



#     flash(f'Message has been sent to nick@dashanddata.com. A verification has been sent to your email as well.', 'success')
#     return redirect(url_for('bp_users.home'))


    # return redirect(url_for('home'))





