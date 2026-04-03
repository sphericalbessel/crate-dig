import os

import pytest

from scanner import find_music_files, read_track_metadata, scan_library


# ---------------------------------------------------------------------------
# find_music_files
# ---------------------------------------------------------------------------

def test_find_music_files_returns_only_supported_extensions(tmp_path):
    for name in ('track.mp3', 'track.flac', 'track.wav', 'track.aiff',
                 'track.aif', 'track.m4a', 'notes.txt', 'cover.jpg'):
        (tmp_path / name).write_bytes(b'')

    results = find_music_files([str(tmp_path)])
    names = {os.path.basename(p) for p in results}

    assert 'track.mp3' in names
    assert 'track.flac' in names
    assert 'track.wav' in names
    assert 'track.aiff' in names
    assert 'track.aif' in names
    assert 'track.m4a' in names
    assert 'notes.txt' not in names
    assert 'cover.jpg' not in names


def test_find_music_files_recurses_subdirectories(tmp_path):
    subdir = tmp_path / 'subdir'
    subdir.mkdir()
    (tmp_path / 'top.mp3').write_bytes(b'')
    (subdir / 'nested.mp3').write_bytes(b'')

    results = find_music_files([str(tmp_path)])
    names = {os.path.basename(p) for p in results}

    assert 'top.mp3' in names
    assert 'nested.mp3' in names


def test_find_music_files_skips_hidden_directories(tmp_path):
    hidden = tmp_path / '.hidden'
    hidden.mkdir()
    (hidden / 'secret.mp3').write_bytes(b'')
    (tmp_path / 'visible.mp3').write_bytes(b'')

    results = find_music_files([str(tmp_path)])
    names = {os.path.basename(p) for p in results}

    assert 'visible.mp3' in names
    assert 'secret.mp3' not in names


def test_find_music_files_skips_icloud_placeholder_files(tmp_path, caplog):
    import logging
    (tmp_path / '.track.mp3.icloud').write_bytes(b'')
    (tmp_path / 'real.mp3').write_bytes(b'')

    with caplog.at_level(logging.WARNING, logger='scanner'):
        results = find_music_files([str(tmp_path)])

    names = {os.path.basename(p) for p in results}
    assert 'real.mp3' in names
    assert any('.icloud' in msg for msg in caplog.messages)
    assert not any(p.endswith('.icloud') for p in results)


def test_find_music_files_skips_hidden_files(tmp_path):
    (tmp_path / '.hidden.mp3').write_bytes(b'')
    (tmp_path / 'visible.mp3').write_bytes(b'')

    results = find_music_files([str(tmp_path)])
    names = {os.path.basename(p) for p in results}

    assert 'visible.mp3' in names
    assert '.hidden.mp3' not in names


def test_find_music_files_deduplicates_directories(tmp_path):
    (tmp_path / 'track.mp3').write_bytes(b'')

    results = find_music_files([str(tmp_path), str(tmp_path)])

    assert len(results) == 1


def test_find_music_files_handles_nonexistent_directory(tmp_path, caplog):
    import logging
    missing = str(tmp_path / 'does_not_exist')

    with caplog.at_level(logging.WARNING, logger='scanner'):
        results = find_music_files([missing])

    assert results == []
    assert any('Directory not found' in msg for msg in caplog.messages)


def test_find_music_files_handles_spaces_in_path(tmp_path):
    spaced = tmp_path / 'my music folder'
    spaced.mkdir()
    (spaced / 'track.mp3').write_bytes(b'')

    results = find_music_files([str(spaced)])

    assert len(results) == 1
    assert 'track.mp3' in results[0]


# ---------------------------------------------------------------------------
# read_track_metadata
# ---------------------------------------------------------------------------

def test_read_track_metadata_extracts_fields(wav_factory):
    path = wav_factory(
        filename='known.wav',
        title='Test Title',
        artist='Test Artist',
        album='Test Album',
        genre='Electronic',
        bpm=128,
        key='Am',
    )

    track = read_track_metadata(path)

    assert track['error'] is None
    assert track['title'] == 'Test Title'
    assert track['artist'] == 'Test Artist'
    assert track['album'] == 'Test Album'
    assert track['genre'] == 'Electronic'
    assert track['bpm'] == '128'
    assert track['key'] == 'Am'
    assert track['file_format'] == 'wav'
    assert track['file_name'] == 'known.wav'
    assert track['file_size_mb'] is not None
    assert track['duration_seconds'] is not None


def test_read_track_metadata_handles_missing_tags(wav_factory):
    path = wav_factory(filename='no_tags.wav')

    track = read_track_metadata(path)

    assert track['error'] is None
    assert track['title'] is None
    assert track['artist'] is None
    assert track['bpm'] is None
    assert track['file_size_mb'] is not None


def test_read_track_metadata_handles_nonexistent_file(tmp_path):
    missing = str(tmp_path / 'ghost.mp3')

    track = read_track_metadata(missing)

    assert track['error'] is not None
    assert track['file_size_mb'] is None


def test_read_track_metadata_handles_unreadable_file(tmp_path):
    bad = tmp_path / 'corrupt.mp3'
    bad.write_bytes(b'\x00' * 10)

    track = read_track_metadata(str(bad))

    # Either successfully reads (no tags) or captures the error — must not raise
    assert isinstance(track, dict)
    assert 'error' in track


def test_read_track_metadata_id_is_stable(wav_factory):
    path = wav_factory()

    track1 = read_track_metadata(path)
    track2 = read_track_metadata(path)

    assert track1['id'] == track2['id']
    assert len(track1['id']) == 32  # MD5 hex digest


def test_read_track_metadata_returns_absolute_path(tmp_path, wav_factory):
    path = wav_factory()

    track = read_track_metadata(path)

    assert os.path.isabs(track['file_path'])


# ---------------------------------------------------------------------------
# scan_library
# ---------------------------------------------------------------------------

def test_scan_library_returns_one_dict_per_file(wav_factory, tmp_path):
    wav_factory(filename='a.wav')
    wav_factory(filename='b.wav')

    results = scan_library([str(tmp_path)])

    assert len(results) == 2
    assert all(isinstance(t, dict) for t in results)
    assert all('id' in t for t in results)


def test_scan_library_deduplicates_directories(wav_factory, tmp_path):
    wav_factory(filename='track.wav')

    results = scan_library([str(tmp_path), str(tmp_path)])

    assert len(results) == 1
