import os
from functools import reduce

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO, send
from pymongo import MongoClient

client = MongoClient('mongodb://heroku_56mhcgd8:m38o2mfh3boqq4l7qbil2i01pc@ds237955.mlab.com:37955/heroku_56mhcgd8')
app = Flask(__name__)
app.secret_key = 'fghjkl67890'
CORS(app)
db = client.heroku_56mhcgd8
socketio = SocketIO(app, binary=True)
THRESHOLD = 2
USER_COUNT = db.users.count_documents({})


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


def check_sufficient_files():
    index_set = set()
    split_files = os.listdir("split")
    for file in split_files:
        index = file.split('_')[1].split('.')[0]
        index_set.add(index)

    return (db.count.last.find()[0].count == sorted(list(index_set))[-1]) and (
                len(index_set) == db.count.last.find()[0].count)


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
        users_collection.update_one({"username": username, "password": password}, {"$set": {"login_status": True}})
        file1.save(os.path.join('split', file1.filename))
        file2.save(os.path.join('split', file2.filename))
        return jsonify(response="Logged in successfully")


@app.route('/getDirTree', methods=['GET'])
def get_dir_tree():
    if not check_sufficient_files():
        return jsonify(response=False)
    else:
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


@socketio.on('logout')
def handle_logout(json):
    print(json)
    if db.users.find({'logged_in': False}).length <= THRESHOLD:
        send(jsonify(result='emergency_logout'))
        return
    elif db.users.find({'logged_in': False}).length == USER_COUNT:
        send(jsonify(result='normal_logout'))
    else:
        send(jsonify(result='no_logout'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('Starting app...')
    socketio.run(app, host='0.0.0.0', port=port)
