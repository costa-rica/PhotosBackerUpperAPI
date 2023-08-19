from flask import Blueprint
from flask import render_template, jsonify, request,current_app
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from werkzeug.utils import secure_filename


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
def create_directory():

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
def receive_image():
    logger_bp_main.info(f"- in receive_image endpoint")

    # Check if the post request has the file and json object
    if 'file' not in request.files:
        return jsonify(error='No file received'), 400
    elif 'json' not in request.form:
        return jsonify(error='No json received'), 400

    file = request.files['file']

    try:

        request_form = request.form
        logger_bp_main.info(f"request_form: {request_form}")
        request_files = request.files
        logger_bp_main.info(f"request_files:  {request_files}")

        data_json = json.loads(request_form.get('json'))
        logger_bp_main.info(f"request_form.get:  {data_json.get('directory')}")
        dir_sub_name = data_json['directory']
        
        if file.filename == '':
            return jsonify(error='No selected file'), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_dir = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), dir_sub_name)
            
            # Create the subdirectory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)

            filepath = os.path.join(save_dir, filename)
            file.save(filepath)
            return jsonify(status='success', message=f'File saved to {filepath}')
        
        return jsonify(error='Invalid file type'), 400
    except Exception as e:
        return jsonify(error=str(e)), 500






@bp_main.route('/receive_image_old', methods=['POST'])
def receive_image_old():
    logger_bp_main.info(f"- in receive_image endpoint")

    try:
        requestFiles = request.files
        logger_bp_main.info(f"reqeustFiles: {requestFiles}")

    except Exception as e:
        logger_bp_main.info(e)
        logger_bp_main.info(f"requestFiles not found")
        return jsonify({"status": "Image Not found."})

    
    for file_name, post_image in requestFiles.items():

        post_image_filename = post_image.filename
        filename_no_extension, file_extension = os.path.splitext(post_image_filename)
        # logger_bp_main.info(f"-- post_image_filename: {post_image_filename} --")
        file_size = post_image.content_length
        # file_size = get_file_size(post_image.stream)
        logger_bp_main.info(f"-- file_size: {file_size} --")

        new_dir_name = "interesting_photos_endpoint"

        new_dir_path_and_name = os.path.join(current_app.config.get('DIR_DB_PHOTOS_MAIN'), new_dir_name)
        post_image.save(os.path.join(new_dir_path_and_name, post_image_filename))

    logger_bp_main.info(f"- finished receive_image endpoint")

    return jsonify({"image_received_status":"Successfully send images and executed /receive_image endpoint "})


# def get_file_size(file_storage):
#     file_storage.seek(0, os.SEEK_END)  # Seek to the end of the file
#     size = file_storage.tell()         # Get the position, which is the size
#     file_storage.seek(0)               # Reset the file stream to the beginning
#     return size