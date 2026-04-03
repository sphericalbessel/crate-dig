import hashlib
import logging
import os

import mutagen
from mutagen.id3 import ID3 as ID3Tags
from mutagen.mp4 import MP4Tags

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset({'.mp3', '.flac', '.wav', '.aiff', '.aif', '.m4a'})

_ID3_KEYS = {
    'title': 'TIT2',
    'artist': 'TPE1',
    'album': 'TALB',
    'genre': 'TCON',
    'bpm': 'TBPM',
    'key': 'TKEY',
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


def _get_tag_value(audio, field):
    """Extract a normalized tag value from a mutagen audio object."""
    tags = audio.tags
    if tags is None:
        return None

    if isinstance(tags, ID3Tags):
        frame = tags.get(_ID3_KEYS[field])
        if frame is None:
            return None
        val = frame.text[0] if hasattr(frame, 'text') else str(frame)
        return str(val).strip() or None

    if isinstance(tags, MP4Tags):
        vals = tags.get(_MP4_KEYS[field])
        if not vals:
            return None
        v = vals[0]
        if isinstance(v, bytes):
            return v.decode('utf-8', errors='ignore').strip() or None
        return str(v).strip() or None

    # Vorbis Comment (FLAC)
    vals = tags.get(_VORBIS_KEYS[field])
    if not vals:
        return None
    return str(vals[0]).strip() or None


def find_music_files(directories):
    """Walk directories and return a list of absolute paths of music files.

    Skips hidden directories, hidden files, and iCloud placeholder files.
    Deduplicates directories before walking.
    """
    # Deduplicate while preserving order
    directories = list(dict.fromkeys(os.path.abspath(d) for d in directories))

    files = []
    seen = set()

    for directory in directories:
        if not os.path.isdir(directory):
            logger.warning('Directory not found: %s', directory)
            continue

        for root, dirnames, filenames in os.walk(directory, followlinks=False):
            # Prune hidden directories in-place so os.walk won't descend into them
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]

            for filename in filenames:
                if filename.startswith('.'):
                    if filename.endswith('.icloud'):
                        logger.warning('iCloud offloaded file skipped: %s', os.path.join(root, filename))
                    continue

                ext = os.path.splitext(filename)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                path = os.path.join(root, filename)
                if path not in seen:
                    seen.add(path)
                    files.append(path)

    return files


def read_track_metadata(file_path):
    """Read metadata from a single music file.

    Returns a dict with all track fields. Never raises — errors are captured
    in the 'error' field and all other metadata fields are set to None.
    """
    file_path = os.path.abspath(file_path)
    track = {
        'id': hashlib.md5(file_path.encode('utf-8')).hexdigest(),
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'file_format': os.path.splitext(file_path)[1].lstrip('.').lower(),
        'title': None,
        'artist': None,
        'album': None,
        'genre': None,
        'bpm': None,
        'key': None,
        'duration_seconds': None,
        'file_size_mb': None,
        'error': None,
    }

    try:
        track['file_size_mb'] = round(os.path.getsize(file_path) / (1024 * 1024), 3)
    except OSError as e:
        track['error'] = str(e)
        return track

    try:
        audio = mutagen.File(file_path)
        if audio is None:
            track['error'] = 'mutagen could not identify file format'
            return track

        info = getattr(audio, 'info', None)
        if info is not None:
            length = getattr(info, 'length', None)
            if length:
                track['duration_seconds'] = round(length, 2)

        for field in ('title', 'artist', 'album', 'genre', 'bpm', 'key'):
            track[field] = _get_tag_value(audio, field)

    except Exception as e:
        track['error'] = str(e)

    return track


def scan_library(directories):
    """Scan directories and return a list of track metadata dicts."""
    return [read_track_metadata(f) for f in find_music_files(directories)]
