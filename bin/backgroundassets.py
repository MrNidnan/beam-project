#!/usr/bin/env python
# -*- coding: utf-8 -*-

import filecmp
import logging
import os
import shutil

from bin.beamutils import getBeamConfigPath, getBeamHomePath, getBeamResourcesPath


BACKGROUND_EXTENSIONS = ('.jpg', '.jpeg', '.png')
ASSET_PREFIX = 'asset:'
ASSET_SCOPE_BUILTIN = 'builtin'
ASSET_SCOPE_USER = 'user'
ASSET_SCOPE_EXTERNAL = 'external'


def _normalize_slashes(path_value):
    return str(path_value).replace('\\', '/')


def _is_supported_background_file(path_value):
    return os.path.isfile(path_value) and os.path.splitext(path_value)[1].lower() in BACKGROUND_EXTENSIONS


def _clean_relative_path(relative_path):
    normalized = _normalize_slashes(relative_path).strip()
    while normalized.startswith('./'):
        normalized = normalized[2:]
    normalized = normalized.lstrip('/')
    raw_parts = normalized.split('/')
    for part in raw_parts:
        if part == '..':
            raise ValueError("Background asset paths cannot contain '..'")

    normalized = os.path.normpath(normalized.replace('/', os.sep))

    parts = []
    for part in normalized.split(os.sep):
        if part in ('', '.'):
            continue
        if part == '..':
            raise ValueError("Background asset paths cannot contain '..'")
        parts.append(part)

    return '/'.join(parts)


def _make_reference(scope, relative_path):
    return '%s%s/%s' % (ASSET_PREFIX, scope, _clean_relative_path(relative_path))


def _is_path_under_root(path_value, root_path):
    try:
        absolute_path = os.path.normcase(os.path.abspath(path_value))
        absolute_root = os.path.normcase(os.path.abspath(root_path))
        return os.path.commonpath([absolute_path, absolute_root]) == absolute_root
    except ValueError:
        return False


def _resolve_root_for_scope(scope):
    if scope == ASSET_SCOPE_BUILTIN:
        return getBeamResourcesPath()
    if scope == ASSET_SCOPE_USER:
        return getBeamConfigPath()
    return None


def _normalize_asset_type(asset_type):
    normalized_type = _normalize_slashes(asset_type or 'moods').strip().lower()
    if normalized_type in ('mood', 'moods', 'backgrounds/moods'):
        return 'backgrounds/moods'
    if normalized_type in ('artist', 'artists', 'orchestra', 'orchestras', 'backgrounds/orchestras'):
        return 'backgrounds/orchestras'
    raise ValueError("Unknown background asset type '%s'" % asset_type)


def _list_supported_backgrounds(directory_path):
    if not os.path.isdir(directory_path):
        return []

    return sorted(
        [
            entry for entry in os.listdir(directory_path)
            if _is_supported_background_file(os.path.join(directory_path, entry))
        ]
    )


def _files_are_identical(source_path, target_path):
    try:
        return filecmp.cmp(source_path, target_path, shallow=False)
    except OSError:
        return False


def _directories_are_identical(source_directory, target_directory):
    source_files = _list_supported_backgrounds(source_directory)
    target_files = _list_supported_backgrounds(target_directory)
    if source_files != target_files:
        return False

    for filename in source_files:
        if not _files_are_identical(
            os.path.join(source_directory, filename),
            os.path.join(target_directory, filename),
        ):
            return False

    return True


def _build_result(kind, scope, raw_value, reference, relative_path, normalized_reference):
    return {
        'kind': kind,
        'scope': scope,
        'rawValue': raw_value,
        'reference': reference,
        'relativePath': relative_path,
        'normalizedReference': normalized_reference,
    }


def get_user_background_root(asset_type):
    return os.path.join(getBeamConfigPath(), *_normalize_asset_type(asset_type).split('/'))


def get_background_asset_roots():
    return {
        ASSET_SCOPE_BUILTIN: getBeamResourcesPath(),
        ASSET_SCOPE_USER: getBeamConfigPath(),
    }


def parse_background_reference(value):
    raw_value = '' if value is None else str(value).strip()
    if raw_value == '':
        return _build_result('empty', None, raw_value, '', '', '')

    if raw_value.startswith(ASSET_PREFIX):
        asset_value = _normalize_slashes(raw_value[len(ASSET_PREFIX):]).strip()
        if '/' not in asset_value:
            return _build_result('invalid', None, raw_value, raw_value, '', '')

        scope, relative_path = asset_value.split('/', 1)
        if scope not in (ASSET_SCOPE_BUILTIN, ASSET_SCOPE_USER):
            return _build_result('invalid', None, raw_value, raw_value, '', '')

        try:
            cleaned_relative_path = _clean_relative_path(relative_path)
        except ValueError:
            return _build_result('invalid', None, raw_value, raw_value, '', '')

        normalized_reference = _make_reference(scope, cleaned_relative_path)
        return _build_result('asset', scope, raw_value, normalized_reference, cleaned_relative_path, normalized_reference)

    normalized_value = _normalize_slashes(raw_value)
    if normalized_value.lower().startswith('resources/'):
        try:
            cleaned_relative_path = _clean_relative_path(normalized_value[len('resources/'):])
        except ValueError:
            return _build_result('invalid', None, raw_value, raw_value, '', '')

        normalized_reference = _make_reference(ASSET_SCOPE_BUILTIN, cleaned_relative_path)
        return _build_result('legacy-resource', ASSET_SCOPE_BUILTIN, raw_value, raw_value, cleaned_relative_path, normalized_reference)

    if os.path.isabs(raw_value):
        absolute_path = os.path.normpath(raw_value)
        return _build_result('absolute', ASSET_SCOPE_EXTERNAL, raw_value, absolute_path, '', absolute_path)

    return _build_result('relative', None, raw_value, raw_value, '', raw_value)


def normalize_background_reference(value):
    parsed_value = parse_background_reference(value)
    if parsed_value['kind'] == 'empty':
        return ''
    if parsed_value['kind'] in ('asset', 'legacy-resource'):
        return parsed_value['normalizedReference']
    if parsed_value['kind'] in ('absolute', 'relative'):
        return parsed_value['reference']
    raise ValueError("Invalid background reference '%s'" % value)


def resolve_background_reference(value):
    parsed_value = parse_background_reference(value)
    absolute_path = ''
    canonical_reference = ''

    if parsed_value['kind'] == 'asset':
        root_path = _resolve_root_for_scope(parsed_value['scope'])
        absolute_path = os.path.normpath(os.path.join(root_path, *parsed_value['relativePath'].split('/')))
        canonical_reference = parsed_value['normalizedReference']
    elif parsed_value['kind'] == 'legacy-resource':
        absolute_path = os.path.normpath(os.path.join(getBeamResourcesPath(), *parsed_value['relativePath'].split('/')))
        canonical_reference = parsed_value['normalizedReference']
    elif parsed_value['kind'] == 'absolute':
        absolute_path = parsed_value['reference']
    elif parsed_value['kind'] == 'relative':
        absolute_path = os.path.normpath(os.path.join(getBeamHomePath(), parsed_value['rawValue']))
    elif parsed_value['kind'] == 'invalid':
        logging.warning("Invalid background reference '%s'", value)

    return {
        'kind': parsed_value['kind'],
        'scope': parsed_value['scope'],
        'reference': parsed_value['reference'],
        'rawValue': parsed_value['rawValue'],
        'relativePath': parsed_value['relativePath'],
        'absolutePath': absolute_path,
        'exists': bool(absolute_path) and (os.path.isfile(absolute_path) or os.path.isdir(absolute_path)),
        'canonicalReference': canonical_reference,
    }


def to_persisted_background_reference(absolute_path, asset_type=None):
    if absolute_path is None:
        return ''

    normalized_path = os.path.normpath(os.path.abspath(str(absolute_path)))
    roots = get_background_asset_roots()
    if _is_path_under_root(normalized_path, roots[ASSET_SCOPE_BUILTIN]):
        relative_path = os.path.relpath(normalized_path, roots[ASSET_SCOPE_BUILTIN])
        return _make_reference(ASSET_SCOPE_BUILTIN, relative_path)

    if _is_path_under_root(normalized_path, roots[ASSET_SCOPE_USER]):
        relative_path = os.path.relpath(normalized_path, roots[ASSET_SCOPE_USER])
        return _make_reference(ASSET_SCOPE_USER, relative_path)

    return None


def _copy_file_into_directory(source_path, destination_directory):
    filename = os.path.basename(source_path)
    stem, extension = os.path.splitext(filename)
    candidate_path = os.path.join(destination_directory, filename)
    suffix = 1

    while os.path.exists(candidate_path):
        if _files_are_identical(source_path, candidate_path):
            return candidate_path, False
        candidate_path = os.path.join(destination_directory, '%s-%s%s' % (stem, suffix, extension))
        suffix += 1

    shutil.copy2(source_path, candidate_path)
    return candidate_path, True


def _copy_directory_contents(source_directory, destination_root):
    source_name = os.path.basename(os.path.normpath(source_directory)) or 'backgrounds'
    candidate_directory = os.path.join(destination_root, source_name)
    suffix = 1

    while os.path.exists(candidate_directory):
        if os.path.isdir(candidate_directory) and _directories_are_identical(source_directory, candidate_directory):
            return candidate_directory, 0, False
        candidate_directory = os.path.join(destination_root, '%s-%s' % (source_name, suffix))
        suffix += 1

    os.makedirs(candidate_directory)
    copied_files = 0
    for filename in _list_supported_backgrounds(source_directory):
        shutil.copy2(os.path.join(source_directory, filename), os.path.join(candidate_directory, filename))
        copied_files += 1

    return candidate_directory, copied_files, True


def import_background_asset(source_path, asset_type, copy_mode='copy'):
    del copy_mode

    source_absolute_path = os.path.normpath(os.path.abspath(str(source_path)))
    existing_reference = to_persisted_background_reference(source_absolute_path, asset_type)
    if existing_reference:
        resolved_asset = resolve_background_reference(existing_reference)
        return {
            'status': 'reused',
            'reference': existing_reference,
            'absolutePath': resolved_asset['absolutePath'],
            'copiedFiles': 0,
            'message': '',
        }

    destination_root = get_user_background_root(asset_type)
    os.makedirs(destination_root, exist_ok=True)

    if os.path.isfile(source_absolute_path):
        if not _is_supported_background_file(source_absolute_path):
            return {
                'status': 'failed',
                'reference': '',
                'absolutePath': '',
                'copiedFiles': 0,
                'message': 'Unsupported background file type.',
            }

        target_path, copied = _copy_file_into_directory(source_absolute_path, destination_root)
        reference = to_persisted_background_reference(target_path, asset_type)
        return {
            'status': 'imported' if copied else 'reused',
            'reference': reference,
            'absolutePath': target_path,
            'copiedFiles': 1 if copied else 0,
            'message': '',
        }

    if os.path.isdir(source_absolute_path):
        supported_files = _list_supported_backgrounds(source_absolute_path)
        if not supported_files:
            return {
                'status': 'failed',
                'reference': '',
                'absolutePath': '',
                'copiedFiles': 0,
                'message': 'The selected folder does not contain supported background images.',
            }

        target_path, copied_files, copied = _copy_directory_contents(source_absolute_path, destination_root)
        reference = to_persisted_background_reference(target_path, asset_type)
        return {
            'status': 'imported' if copied else 'reused',
            'reference': reference,
            'absolutePath': target_path,
            'copiedFiles': copied_files,
            'message': '',
        }

    return {
        'status': 'failed',
        'reference': '',
        'absolutePath': '',
        'copiedFiles': 0,
        'message': 'Selected background path does not exist.',
    }