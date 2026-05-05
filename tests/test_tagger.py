import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scanner import read_track_metadata
from tagger import EDITABLE_FIELDS, write_tag


# ── write_tag — WAV/ID3 ────────────────────────────────────────────────────────

def test_write_tag_creates_tag_in_untagged_wav(wav_factory):
    path = wav_factory('untagged.wav')
    write_tag(path, 'artist', 'New Artist')
    track = read_track_metadata(path)
    assert track['artist'] == 'New Artist'


def test_write_tag_overwrites_existing_tag(wav_factory):
    path = wav_factory('tagged.wav', artist='Old Artist')
    write_tag(path, 'artist', 'New Artist')
    track = read_track_metadata(path)
    assert track['artist'] == 'New Artist'


@pytest.mark.parametrize('field,value', [
    ('title', 'Test Title'),
    ('artist', 'Test Artist'),
    ('album', 'Test Album'),
    ('genre', 'Test Genre'),
    ('bpm', '128'),
    ('key', 'Am'),
])
def test_write_all_editable_fields(wav_factory, field, value):
    path = wav_factory(f'test_{field}.wav')
    write_tag(path, field, value)
    track = read_track_metadata(path)
    assert track[field] == value


def test_write_tag_strips_whitespace(wav_factory):
    path = wav_factory('whitespace.wav')
    write_tag(path, 'artist', '  Padded Artist  ')
    track = read_track_metadata(path)
    assert track['artist'] == 'Padded Artist'


def test_write_empty_string_clears_field(wav_factory):
    path = wav_factory('clear.wav', artist='Some Artist')
    write_tag(path, 'artist', '')
    track = read_track_metadata(path)
    assert track['artist'] is None


# ── write_tag — validation errors ─────────────────────────────────────────────

def test_write_tag_invalid_field_raises(wav_factory):
    path = wav_factory('invalid_field.wav')
    with pytest.raises(ValueError, match="not an editable field"):
        write_tag(path, 'track_number', '1')


def test_write_tag_unsupported_format_raises(tmp_path):
    txt = tmp_path / 'not_audio.txt'
    txt.write_bytes(b'hello')
    with pytest.raises(ValueError, match="Unsupported format"):
        write_tag(str(txt), 'artist', 'Someone')


def test_write_tag_nonexistent_file_raises(tmp_path):
    missing = str(tmp_path / 'missing.wav')
    with pytest.raises(Exception):
        write_tag(missing, 'artist', 'Someone')


# ── EDITABLE_FIELDS constant ───────────────────────────────────────────────────

def test_editable_fields_contains_expected():
    assert EDITABLE_FIELDS == {'title', 'artist', 'album', 'genre', 'bpm', 'key'}
