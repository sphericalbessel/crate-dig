import json
import logging
import os
import sys

from flask import Flask, jsonify, request, send_file

sys.path.insert(0, os.path.dirname(__file__))
from fileops import delete_file, move_file, rename_from_tags
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


def _find_track_path(track_id):
    config = _read_config()
    tracks = scan_library(config.get('folders', []))
    for track in tracks:
        if track['id'] == track_id:
            return track['file_path']
    return None


@app.get('/tracks')
def get_tracks():
    config = _read_config()
    folders = config.get('folders', [])
    tracks = scan_library(folders)
    return jsonify(tracks)


@app.post('/api/tracks/move')
def move_track():
    body = request.get_json(silent=True)
    if not body or 'track_id' not in body or 'destination_dir' not in body:
        return jsonify({'error': 'Request body must include "track_id" and "destination_dir"'}), 400

    file_path = _find_track_path(body['track_id'])
    if file_path is None:
        return jsonify({'error': 'Track not found'}), 404

    return jsonify(move_file(file_path, body['destination_dir']))


@app.post('/api/tracks/delete')
def delete_track():
    body = request.get_json(silent=True)
    if not body or 'track_id' not in body:
        return jsonify({'error': 'Request body must include "track_id"'}), 400

    file_path = _find_track_path(body['track_id'])
    if file_path is None:
        return jsonify({'error': 'Track not found'}), 404

    return jsonify(delete_file(file_path))


@app.post('/api/tracks/rename')
def rename_track():
    body = request.get_json(silent=True)
    if not body or 'track_id' not in body or 'pattern' not in body:
        return jsonify({'error': 'Request body must include "track_id" and "pattern"'}), 400

    file_path = _find_track_path(body['track_id'])
    if file_path is None:
        return jsonify({'error': 'Track not found'}), 404

    return jsonify(rename_from_tags(file_path, body['pattern']))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
