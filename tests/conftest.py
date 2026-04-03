import os
import struct
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


def _make_minimal_wav():
    """Return bytes for a valid silent WAV file (46 bytes total)."""
    data = b'\x00\x00'  # 1 silent 16-bit sample
    fmt = struct.pack('<HHIIHH', 1, 1, 44100, 88200, 2, 16)
    return (
        b'RIFF' + struct.pack('<I', 36 + len(data)) +
        b'WAVE' +
        b'fmt ' + struct.pack('<I', 16) + fmt +
        b'data' + struct.pack('<I', len(data)) + data
    )


@pytest.fixture
def wav_factory(tmp_path):
    """Returns a function that creates WAV files with optional ID3 tags."""
    from mutagen.wave import WAVE
    from mutagen.id3 import TIT2, TPE1, TALB, TCON, TBPM, TKEY

    frame_map = [
        ('title', TIT2),
        ('artist', TPE1),
        ('album', TALB),
        ('genre', TCON),
        ('bpm', TBPM),
        ('key', TKEY),
    ]

    def make(filename='test.wav', title=None, artist=None, album=None,
             genre=None, bpm=None, key=None):
        path = tmp_path / filename
        path.write_bytes(_make_minimal_wav())

        kwargs = {'title': title, 'artist': artist, 'album': album,
                  'genre': genre, 'bpm': bpm, 'key': key}

        if any(v is not None for v in kwargs.values()):
            audio = WAVE(str(path))
            audio.add_tags()
            for field, cls in frame_map:
                val = kwargs[field]
                if val is not None:
                    audio.tags.add(cls(encoding=3, text=[str(val)]))
            audio.save()

        return str(path)

    return make
