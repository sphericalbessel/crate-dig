import os
import re
import shutil

import mutagen
import send2trash
from mutagen.id3 import ID3 as ID3Tags
from mutagen.mp4 import MP4Tags

SUPPORTED_PATTERN_FIELDS = {"title", "artist", "album", "genre", "bpm", "key", "track"}

_INVALID_FILENAME_CHARS = re.compile(r'[/\\:*?"<>|\x00]')
_MULTI_SPACE = re.compile(r' {2,}')

_ID3_KEYS = {
    "title": "TIT2", "artist": "TPE1", "album": "TALB",
    "genre": "TCON", "bpm": "TBPM", "key": "TKEY", "track": "TRCK",
}
_MP4_KEYS = {
    "title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb",
    "genre": "\xa9gen", "bpm": "tmpo", "key": "----:com.apple.iTunes:initialkey",
    "track": "trkn",
}
_VORBIS_KEYS = {
    "title": "title", "artist": "artist", "album": "album",
    "genre": "genre", "bpm": "bpm", "key": "key", "track": "tracknumber",
}


def _read_tag(audio, field):
    tags = audio.tags
    if tags is None:
        return None

    if isinstance(tags, ID3Tags):
        frame = tags.get(_ID3_KEYS[field])
        if frame is None:
            return None
        val = frame.text[0] if hasattr(frame, "text") else str(frame)
        return str(val).strip() or None

    if isinstance(tags, MP4Tags):
        vals = tags.get(_MP4_KEYS[field])
        if not vals:
            return None
        v = vals[0]
        if isinstance(v, bytes):
            return v.decode("utf-8", errors="ignore").strip() or None
        if isinstance(v, tuple):
            return str(v[0]).strip() or None
        return str(v).strip() or None

    # Vorbis Comment (FLAC, OGG)
    vals = tags.get(_VORBIS_KEYS[field])
    if not vals:
        return None
    return str(vals[0]).strip() or None


def move_file(source_path, destination_dir):
    source_path = os.path.abspath(source_path)
    destination_dir = os.path.abspath(destination_dir)

    if not os.path.isfile(source_path):
        return {"success": False, "error": f"Source file does not exist: {source_path}"}

    if not os.path.isdir(destination_dir):
        return {"success": False, "error": f"Destination directory does not exist: {destination_dir}"}

    source_dir = os.path.dirname(source_path)
    if source_dir == destination_dir:
        return {"success": True, "new_path": source_path, "note": "File is already in the destination directory"}

    filename = os.path.basename(source_path)
    dest_path = os.path.join(destination_dir, filename)

    if os.path.exists(dest_path):
        return {"success": False, "error": f"A file named '{filename}' already exists in the destination directory"}

    try:
        shutil.move(source_path, dest_path)
    except OSError as e:
        return {"success": False, "error": str(e)}

    return {"success": True, "new_path": dest_path}


def delete_file(file_path):
    file_path = os.path.abspath(file_path)

    if not os.path.isfile(file_path):
        return {"success": False, "error": f"File does not exist: {file_path}"}

    try:
        send2trash.send2trash(file_path)
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": True}


def rename_from_tags(file_path, pattern):
    file_path = os.path.abspath(file_path)

    if not os.path.isfile(file_path):
        return {"success": False, "error": f"File does not exist: {file_path}"}

    audio = mutagen.File(file_path)
    if audio is None:
        return {"success": False, "error": f"Could not read tags from file: {file_path}"}

    tag_map = {field: _read_tag(audio, field) for field in SUPPORTED_PATTERN_FIELDS}

    warnings = []

    def _substitute(match):
        field = match.group(1).lower()
        if field not in SUPPORTED_PATTERN_FIELDS:
            return match.group(0)
        value = tag_map.get(field)
        if not value:
            warnings.append(f"'{field}' tag is missing or empty, substituted 'Unknown'")
            return "Unknown"
        return value

    stem = re.sub(r'\{(\w+)\}', _substitute, pattern)
    stem = _INVALID_FILENAME_CHARS.sub("-", stem)
    stem = _MULTI_SPACE.sub(" ", stem).strip()

    if not stem:
        return {"success": False, "error": "Pattern resolved to an empty filename after sanitization"}

    ext = os.path.splitext(file_path)[1]
    new_filename = stem + ext
    new_path = os.path.join(os.path.dirname(file_path), new_filename)

    if new_path == file_path:
        result = {"success": True, "new_path": new_path, "note": "Filename is already correct"}
        if warnings:
            result["warnings"] = warnings
        return result

    if os.path.exists(new_path):
        return {"success": False, "error": f"A file named '{new_filename}' already exists in the same directory"}

    try:
        os.rename(file_path, new_path)
    except OSError as e:
        return {"success": False, "error": str(e)}

    result = {"success": True, "new_path": new_path}
    if warnings:
        result["warnings"] = warnings
    return result
