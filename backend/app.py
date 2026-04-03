import json
import logging
import os
import sys

from flask import Flask, jsonify, request, send_file

sys.path.insert(0, os.path.dirname(__file__))
from scanner import scan_library

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')


def _read_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {'folders': []}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning('Could not read config.json: %s', e)
        return {'folders': []}


def _write_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


@app.get('/')
def index():
    return send_file(FRONTEND_PATH)


@app.get('/config')
def get_config():
    return jsonify(_read_config())


@app.post('/config')
def post_config():
    body = request.get_json(silent=True)
    if not body or 'folders' not in body:
        return jsonify({'error': 'Request body must be JSON with a "folders" key'}), 400

    folders = body['folders']
    if not isinstance(folders, list):
        return jsonify({'error': '"folders" must be a list'}), 400

    invalid = [f for f in folders if not os.path.isdir(f)]
    if invalid:
        return jsonify({'error': f'Paths do not exist or are not directories: {invalid}'}), 400

    config = {'folders': folders}
    _write_config(config)
    return jsonify(config)


@app.get('/tracks')
def get_tracks():
    config = _read_config()
    folders = config.get('folders', [])
    tracks = scan_library(folders)
    return jsonify(tracks)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
