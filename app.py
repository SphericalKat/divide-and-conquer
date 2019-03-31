import json
import os
from functools import reduce

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from pymongo import MongoClient

from utils.splitter import split_file
from utils.ziputil import zip_files

client = MongoClient('mongodb://heroku_56mhcgd8:m38o2mfh3boqq4l7qbil2i01pc@ds237955.mlab.com:37955/heroku_56mhcgd8')
app = Flask(__name__)
app.secret_key = 'fghjkl67890'
CORS(app)
db = client.heroku_56mhcgd8
socketio = SocketIO(app, binary=True)
THRESHOLD = 2
USER_COUNT = db.users.count_documents({})
COUNT = 0
logout_queue = set()


def get_directory_structure(rootdir):
    directory = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], directory)
        parent[folders[-1]] = subdir
    return directory


@app.route('/checkSufficientFiles', methods=['GET'])
def check_sufficient_files():
    index_set = set()
    if not os.path.exists('split'):
        os.makedirs('split')
    split_files = os.listdir("split")
    split_files.sort()
    print(split_files)
    for file in split_files:
        print(file)
        index = file.split('_')[-1]

        index_set.add(index)

    return (COUNT == sorted(list(index_set))[-1]) and (
            len(index_set) == COUNT)


@app.route('/saveFile', methods=['POST'])
def save_file():
    path = request.form.get('path')
    if 'file' not in request.files:
        return jsonify(response='FilesNotFoundException')
    else:
        newfile = request.files.get('file')

    if not path:
        dir_path = 'worktree'
    else:
        dir_path = os.path.join('worktree', path)

    work_path = os.path.join(dir_path, newfile.filename)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    try:
        newfile.save(work_path)
    except Exception as e:
        return jsonify(result=str(e))
    return jsonify(result='Successfully saved file')


@app.route('/login', methods=['POST'])
def login():
    users_collection = db.users

    username = request.form.get('username')
    password = request.form.get('password')

    if (not username) or (not password):
        return jsonify(response="NoUsernameOrPasswordException")
    if ('file1' not in request.files) or ('file2' not in request.files):
        return jsonify(response="FilesNotFoundException")
    file1 = request.files.get('file1')
    file2 = request.files.get('file2')
    if not users_collection.find_one({"username": username}):
        return jsonify(response="UserNotFoundException")
    if not users_collection.find_one({"username": username, "password": password}):
        return jsonify(response="IncorrectPasswordException")
    else:
        users_collection.update_one({"username": username, "password": password}, {"$set": {"logged_in": True}})
        file1.save(os.path.join('split', file1.filename))
        file2.save(os.path.join('split', file2.filename))
        return jsonify(response="Logged in successfully", username=username)


@app.route('/getDirTree', methods=['GET'])
def get_dir_tree():
    try:
        return_data = get_directory_structure('worktree/')
        return jsonify(return_data)
    except FileNotFoundError as e:
        return jsonify(result=e)


@app.route('/getFileCode', methods=['GET'])
def get_file_code():
    path = request.args.get('path')
    if not path:
        return jsonify(response="PathNotSuppliedException")
    path = os.path.join('worktree', path)
    try:
        with open(path) as f:
            return jsonify(response=f.read())
    except FileNotFoundError as e:
        return jsonify(response=str(e))
    except IsADirectoryError as e:
        return jsonify(response=str(e))


@app.route('/getSignedInUsers', methods=['GET'])
def get_signed_in_users():
    users = []
    for user in db.users.find({'logged_in': True}):
        users.append(user['username'])
    return jsonify(result=users)


@app.route('/getUserCount', methods=['GET'])
def get_user_count():
    return db.users.count_documents({})


@socketio.on('logout')
def handle_logout(message):
    print(message)
    emit('good-job', {'response': 'Hello World'})
    data = json.loads(message)
    username = data['username']
    if (db.users.count_documents({'logged_in': False})) <= THRESHOLD:
        send({'result': 'emergency_logout'})
        db.users.update_one({'username': username, 'logged_in': False}, {"$set": {'logged_in': True}})
        return
    elif len(list(logout_queue)) == db.users.count_documents({'logged_in': True}):
        emit('queue_full', broadcast=True)
        zip_files('worktree', 'codebase')
        split_file('codebase.zip', USER_COUNT)
        users = get_signed_in_users()

        for i in range(1, USER_COUNT + 1):
            file1 = str(i)
            file2 = str(i + 1)

            emit('split_files', jsonify(
                username=users.pop(),
                file1=file1,
                file2=file2
            ))
            COUNT += 1

    else:
        if username not in logout_queue:
            logout_queue.add(data['username'])
        send({'result': False})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('Starting app...')
    socketio.run(app, host='0.0.0.0', port=port)
