import os

import mutagen
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TALB, TBPM, TCON, TKEY, TIT2, TPE1
from mutagen.mp4 import MP4, MP4FreeForm
from mutagen.wave import WAVE

EDITABLE_FIELDS = frozenset({'title', 'artist', 'album', 'genre', 'bpm', 'key'})

_ID3_FRAME = {
    'title': TIT2,
    'artist': TPE1,
    'album': TALB,
    'genre': TCON,
    'bpm': TBPM,
    'key': TKEY,
}

_VORBIS_KEYS = {
    'title': 'title',
    'artist': 'artist',
    'album': 'album',
    'genre': 'genre',
    'bpm': 'bpm',
    'key': 'key',
}

_MP4_KEYS = {
    'title': '\xa9nam',
    'artist': '\xa9ART',
    'album': '\xa9alb',
    'genre': '\xa9gen',
    'bpm': 'tmpo',
    'key': '----:com.apple.iTunes:initialkey',
}


def write_tag(file_path: str, field: str, value: str) -> None:
    """Write one metadata field to an audio file.

    Strips whitespace from value before writing.
    Raises ValueError for an unsupported field or file format.
    Raises OSError or mutagen.MutagenError if the file cannot be read or written.
    """
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"'{field}' is not an editable field")

    value = value.strip()
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.mp3':
        _write_id3(file_path, field, value)
    elif ext == '.wav':
        _write_wav(file_path, field, value)
    elif ext == '.flac':
        _write_vorbis(file_path, field, value)
    elif ext in ('.m4a', '.aiff', '.aif'):
        _write_mp4(file_path, field, value)
    else:
        raise ValueError(f"Unsupported format: {ext!r}")


def _write_id3(file_path, field, value):
    audio = ID3(file_path)
    frame_cls = _ID3_FRAME[field]
    audio.add(frame_cls(encoding=3, text=[value]))
    audio.save()


def _write_wav(file_path, field, value):
    audio = WAVE(file_path)
    if audio.tags is None:
        audio.add_tags()
    frame_cls = _ID3_FRAME[field]
    audio.tags.add(frame_cls(encoding=3, text=[value]))
    audio.save()


def _write_vorbis(file_path, field, value):
    audio = FLAC(file_path)
    audio[_VORBIS_KEYS[field]] = [value]
    audio.save()


def _write_mp4(file_path, field, value):
    audio = MP4(file_path)
    key = _MP4_KEYS[field]

    if key == '----:com.apple.iTunes:initialkey':
        audio[key] = [MP4FreeForm(value.encode('utf-8'))]
    elif key == 'tmpo':
        try:
            audio[key] = [int(value)]
        except ValueError:
            audio[key] = [value]
    else:
        audio[key] = [value]

    audio.save()
