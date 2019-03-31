import json
import os
from functools import reduce

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO
from pymongo import MongoClient

client = MongoClient('mongodb://heroku_56mhcgd8:m38o2mfh3boqq4l7qbil2i01pc@ds237955.mlab.com:37955/heroku_56mhcgd8')
app = Flask(__name__)
app.secret_key = 'fghjkl67890'
CORS(app)
db = client.heroku_56mhcgd8
socketio = SocketIO(app, binary=True)


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


@app.route('/login', methods=['POST'])
def login():
    users_collection = db.users

    username = request.form.get('username')
    password = request.form.get('password')

    if (not username) or (not password):
        return jsonify(response="NoUsernameOrPasswordException")
    if ('file1' not in request.files) or ('file2' not in request.files):
        return jsonify(response="FilesNotFoundException")
    if not users_collection.find_one({"username": username}):
        return jsonify(response="UserNotFoundException")
    if not users_collection.find_one({"username": username, "password": password}):
        return jsonify(response="IncorrectPasswordException")
    else:
        return jsonify(response="Logged in successfully")


@app.route('/getDirTree', methods=['GET'])
def get_dir_tree():
    return json.dumps(get_directory_structure('./files/'))


@app.route('/getFileCode', methods=['GET'])
def get_file_code():
    path = request.args.get('path')
    if not path:
        return jsonify(response="PathNotSuppliedException")
    try:
        with open(path) as f:
            return jsonify(response=f.read())
    except Exception as e:
        return jsonify(response=e)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print('Starting app...')
    app.run(host='0.0.0.0', port=port)
