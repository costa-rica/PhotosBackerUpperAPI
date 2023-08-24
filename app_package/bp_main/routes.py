from flask import Blueprint
from flask import render_template, jsonify, request,current_app, send_from_directory
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from werkzeug.utils import secure_filename
from pb_models import dict_sess, dict_engine, text, Users, PhotoDirectories, \
    UsersToDirectories
import time
from app_package.token_decorator import token_required

sess_users = dict_sess['sess_users']

bp_main = Blueprint('bp_main', __name__)

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


@bp_main.route("/", methods=["GET","POST"])
def home():
    logger_bp_main.info(f"-- in home page route --")

    return render_template('main/home.html')

@bp_main.route('/are_we_running', methods=['GET'])
def are_we_running():
    
    try:
        hostname = socket.gethostname()
    except:
        hostname = "not sure of my name"
    logger_bp_main.info(f"are_we_working endpoint pinged")

    # Get current date and time
    current_datetime = datetime.now()

    # Format to "YYYY-MM-DD HH:MM:SS"
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(f"Yes! We're up! in the {hostname} machine, time is: {formatted_datetime}")


@bp_main.route('/create_directory', methods=['GET'])
@token_required
def create_directory(current_user):

    try:
        request_json = request.json
        print("request_json:",request_json)

    except Exception as e:
        logger_bp_main.info(e)
        return jsonify({"status": "httpBody data recieved not json not parse-able."})
    
    new_dir_name = request_json.get("new_dir_name")
    logger_bp_main.info(f"Directory name: {new_dir_name}")

    new_dir_path_and_name = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), new_dir_name)

    if not os.path.exists(new_dir_path_and_name):
        os.makedirs(new_dir_path_and_name)
        logger_bp_main.info(f"Created: {new_dir_name}")


    return jsonify({"new_dir_name": new_dir_name})

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp_main.route('/receive_image', methods=['POST'])
@token_required
def receive_image(current_user):
    logger_bp_main.info(f"- in receive_image endpoint")

    logger_bp_main.info("------------")
    request_form = request.form
    logger_bp_main.info(f"request_form: {request_form}")
    request_files = request.files
    logger_bp_main.info(f"request_files:  {request_files}")
    logger_bp_main.info("------------")


    # Check if the post request has the file and json object
    if 'uiimage' not in request.files:
        return jsonify(error='No file received'), 400
    elif 'directory_id' not in request.form:
        return jsonify(error='No directory_id received'), 400

    file = request.files['uiimage']

    try:

        # request_form = request.form
        # logger_bp_main.info(f"request_form: {request_form}")
        # request_files = request.files
        # logger_bp_main.info(f"request_files:  {request_files}")

        # data_json = json.loads(request_form.get('directory_id'))
        # data_json = json.loads(request_form)
        # dict_request_form = request.form
        # logger_bp_main.info(f"request_form.get:  {data_json.get('directory_id')}")
        dir_id = request.form.get('directory_id')
        directory = sess_users.get(PhotoDirectories, int(dir_id))
        
        if file.filename == '':
            return jsonify(error='No selected file'), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_dir = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), directory.unique_dir_name)
            
            # Create the subdirectory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)

            filepath = os.path.join(save_dir, filename)
            file.save(filepath)

            # logger_bp_main.info(f"* Sleep for 5 seconds *")
            # time.sleep(5)

            return jsonify(status='success', message=f'File saved to {filepath}')
        
        return jsonify(error='Invalid file type'), 400
    except Exception as e:
        logger_bp_main.info(f"Error receiving request:  {e}")
        return jsonify(error=str(e)), 500


@bp_main.route('/get_dir_image_list',methods=['POST'])
@token_required
def get_dir_image_list(current_user):
    logger_bp_main.info(f"- in get_dir_image_count endpoint")

    request_json = request.json
    logger_bp_main.info(f"- request_json: {request_json}")

    if 'directory_id' not in request_json:
        return jsonify(error='No directory_id received'), 400

    dir_id = request_json.get('directory_id')
    directory = sess_users.get(PhotoDirectories, int(dir_id))

    directory_path = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), directory.unique_dir_name)
    # Get the list of file names in the directory
    file_names = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]

    return jsonify(file_names) 


@bp_main.route("/send_image", methods=["POST"])
@token_required
def send_image(current_user):

    logger_bp_main.info(f"- in send_image endpoint")
    request_json = request.json

    if 'directory_id' not in request_json:
        logger_bp_main.info(f"- Error: No directory_id received")
        return jsonify(error='No directory_id received'), 400

    dir_id = request_json.get('directory_id')
    file_name = request_json.get('file_name')
    directory = sess_users.get(PhotoDirectories, int(dir_id))

    directory_path = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), directory.unique_dir_name)

    logger_bp_main.info(f"- /send_image respose with filename sent: {file_name}") 

    return send_from_directory(directory_path, file_name)

