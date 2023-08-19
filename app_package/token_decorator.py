from functools import wraps
from flask import request, jsonify,current_app
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous.url_safe import URLSafeTimedSerializer
# from pb_models import sess, engine, text, Base, \
#     Users
from pb_models import dict_sess, dict_engine, text, Users

sess_users = dict_sess['sess_users']

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print('- in token_required decorator -')
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
            
        if not token:
            print("Token is missing ")
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # s=Serializer(current_app.config['SECRET_KEY'])
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            decrypted_token_dict = serializer.loads(token)
            current_user = sess_users.query(Users).filter_by(id = decrypted_token_dict['user_id']).first()
        except:
            print("Token is invalid ")
            return jsonify({'message': 'Token is invalid'}), 401
        
        
        return f(current_user, *args, **kwargs)
    
    return decorated