#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
from copy import deepcopy

from bin.beamutils import getBeamConfigPath, getUserHomePath


class ProfileSettingsStore:
    def __init__(self, config_filename, get_default_config_path, get_legacy_config_path, load_config_data, dump_config_data):
        self._config_filename = config_filename
        self._get_default_config_path = get_default_config_path
        self._get_legacy_config_path = get_legacy_config_path
        self._load_config_data = load_config_data
        self._dump_config_data = dump_config_data
        self._profiles_manifest = None
        self._active_profile_id = 'default'
        self._active_profile_name = 'Default'

    def _get_profiles_manifest_path(self):
        return os.path.join(getBeamConfigPath(), 'beamprofiles.json')

    def _get_profiles_directory_path(self):
        return os.path.join(getBeamConfigPath(), 'profiles')

    def _get_profile_file_path(self, profile_id):
        return os.path.join(self._get_profiles_directory_path(), profile_id + '.json')

    def _get_default_profile_entry(self):
        return {
            'Id': 'default',
            'Name': 'Default',
            'File': os.path.join('profiles', 'default.json'),
            'Locked': True,
            'Persisted': True,
        }

    def _ensure_config_directory(self):
        config_path = getBeamConfigPath()
        if not os.path.isdir(config_path):
            logging.warning("BeamSettings: '%s' does not exist, creating it.", config_path)
            os.makedirs(config_path)

    def _ensure_profiles_directory(self):
        self._ensure_config_directory()
        profiles_path = self._get_profiles_directory_path()
        if not os.path.isdir(profiles_path):
            logging.info("BeamSettings: creating profiles directory '%s'", profiles_path)
            os.makedirs(profiles_path)

    def _load_default_config_data(self):
        return self._load_config_data(self._get_default_config_path())

    def _load_legacy_config_data(self):
        legacy_config_path = self._get_legacy_config_path()
        if os.path.isfile(legacy_config_path):
            return self._load_config_data(legacy_config_path)

        old_config_file = os.path.join(getUserHomePath(), 'BeamConfig.json')
        if os.path.isfile(old_config_file):
            logging.warning("BeamSettings.loadConfig(): using configfile in old directory: '%s'", old_config_file)
            return self._load_config_data(old_config_file)

        logging.warning("BeamSettings.loadConfig(): loading default configfile '%s'", self._get_default_config_path())
        return self._load_default_config_data()

    def _load_profile_manifest(self):
        manifest_path = self._get_profiles_manifest_path()
        if not os.path.isfile(manifest_path):
            return None

        manifest = self._load_config_data(manifest_path)
        if not isinstance(manifest, dict):
            raise ValueError('Profile manifest must be a JSON object')

        profiles = manifest.get('Profiles', [])
        if not isinstance(profiles, list):
            raise ValueError('Profile manifest Profiles must be a list')

        active_profile = manifest.get('ActiveProfile', 'default')
        if not isinstance(active_profile, str) or active_profile == '':
            active_profile = 'default'

        return {
            'ActiveProfile': active_profile,
            'Profiles': profiles,
        }

    def _dump_profile_manifest(self):
        self._ensure_profiles_directory()
        self._dump_config_data(self._get_profiles_manifest_path(), self._profiles_manifest)

    def _get_profile_by_id(self, profile_id):
        if self._profiles_manifest is None:
            return None

        for profile in self._profiles_manifest.get('Profiles', []):
            if profile.get('Id') == profile_id:
                return profile

        return None

    def _get_active_profile_entry(self):
        return self._get_profile_by_id(self._active_profile_id)

    def _ensure_profile_metadata_defaults(self):
        if self._profiles_manifest is None:
            return

        for profile in self._profiles_manifest.get('Profiles', []):
            if 'Persisted' not in profile:
                profile['Persisted'] = True

    def _get_profile_path(self, profile):
        profile_file = profile.get('File', '')
        if profile_file == '':
            return self._get_profile_file_path(profile.get('Id', 'default'))

        if os.path.isabs(profile_file):
            return profile_file

        return os.path.join(getBeamConfigPath(), profile_file)

    def _ensure_default_profile_exists(self, default_config_data):
        default_profile = self._get_profile_by_id('default')
        if default_profile is None:
            self._profiles_manifest['Profiles'].insert(0, self._get_default_profile_entry())
            default_profile = self._get_profile_by_id('default')
        else:
            default_profile['Locked'] = True
            default_profile['Name'] = 'Default'
            default_profile['File'] = os.path.join('profiles', 'default.json')
            default_profile['Persisted'] = True

        default_profile_path = self._get_profile_path(default_profile)
        if not os.path.isfile(default_profile_path):
            self._dump_config_data(default_profile_path, default_config_data)

    def _build_manifest_from_legacy(self):
        legacy_config_data = self._load_legacy_config_data()
        self._profiles_manifest = {
            'ActiveProfile': 'default',
            'Profiles': [self._get_default_profile_entry()],
        }
        self._ensure_profiles_directory()
        self._dump_config_data(self._get_profile_file_path('default'), legacy_config_data)
        self._dump_profile_manifest()
        self._dump_config_data(self._get_legacy_config_path(), legacy_config_data)
        return legacy_config_data

    def _load_profile_config_data(self, profile_id):
        profile = self._get_profile_by_id(profile_id)
        if profile is None:
            raise KeyError("Unknown profile id '%s'" % profile_id)

        profile_path = self._get_profile_path(profile)
        if not os.path.isfile(profile_path):
            raise FileNotFoundError(profile_path)

        return self._load_config_data(profile_path)

    def _sync_active_profile_name(self):
        active_profile = self._get_active_profile_entry()
        if active_profile is None:
            self._active_profile_id = 'default'
            self._active_profile_name = 'Default'
            return

        self._active_profile_name = active_profile.get('Name', active_profile.get('Id', 'Default'))

    def _slugify_profile_name(self, name):
        slug = re.sub(r'[^a-z0-9]+', '-', str(name).strip().lower())
        slug = slug.strip('-')
        if slug == '':
            slug = 'profile'

        existing_ids = set()
        if self._profiles_manifest is not None:
            existing_ids = {profile.get('Id') for profile in self._profiles_manifest.get('Profiles', [])}

        base = slug
        suffix = 2
        while slug in existing_ids:
            slug = '%s-%s' % (base, suffix)
            suffix += 1

        return slug

    def _mirror_active_profile_to_legacy_config(self, config_data):
        self._dump_config_data(self._get_legacy_config_path(), config_data)

    def getProfiles(self):
        if self._profiles_manifest is None:
            return []

        return deepcopy(self._profiles_manifest.get('Profiles', []))

    def getActiveProfileId(self):
        return self._active_profile_id

    def getActiveProfileName(self):
        return self._active_profile_name

    def hasActiveProfileBeenPersisted(self):
        active_profile = self._get_active_profile_entry()
        if active_profile is None:
            return True

        return bool(active_profile.get('Persisted', True))

    def loadProfiles(self):
        default_config_data = self._load_default_config_data()
        manifest = self._load_profile_manifest()

        if manifest is None:
            beam_config_data = self._build_manifest_from_legacy()
        else:
            self._profiles_manifest = manifest
            self._ensure_profiles_directory()
            self._ensure_profile_metadata_defaults()
            self._ensure_default_profile_exists(default_config_data)

            active_profile = self._profiles_manifest.get('ActiveProfile', 'default')
            if self._get_profile_by_id(active_profile) is None:
                active_profile = 'default'
                self._profiles_manifest['ActiveProfile'] = active_profile

            try:
                beam_config_data = self._load_profile_config_data(active_profile)
            except FileNotFoundError:
                logging.warning("BeamSettings: active profile file missing for '%s', recreating from defaults", active_profile)
                if active_profile == 'default':
                    beam_config_data = deepcopy(default_config_data)
                    self._dump_config_data(self._get_profile_file_path('default'), beam_config_data)
                else:
                    self._profiles_manifest['ActiveProfile'] = 'default'
                    active_profile = 'default'
                    beam_config_data = self._load_profile_config_data(active_profile)

            self._dump_profile_manifest()

        self._active_profile_id = self._profiles_manifest.get('ActiveProfile', 'default')
        self._sync_active_profile_name()
        return beam_config_data, default_config_data

    def saveProfiles(self):
        if self._profiles_manifest is None:
            return

        self._dump_profile_manifest()

    def saveActiveProfile(self, config_data):
        active_profile = self._get_active_profile_entry()
        if active_profile is None:
            raise KeyError('No active profile is loaded')

        self._dump_config_data(self._get_profile_path(active_profile), config_data)
        active_profile['Persisted'] = True
        self._mirror_active_profile_to_legacy_config(config_data)
        self.saveProfiles()

    def saveActiveProfileAs(self, profile_id, config_data):
        profile = self._get_profile_by_id(profile_id)
        if profile is None:
            raise KeyError("Unknown profile id '%s'" % profile_id)

        self._dump_config_data(self._get_profile_path(profile), config_data)
        profile['Persisted'] = True
        if profile_id == self._active_profile_id:
            self._mirror_active_profile_to_legacy_config(config_data)

        self.saveProfiles()

    def switchProfile(self, profile_id):
        if profile_id == self._active_profile_id:
            return None, None

        default_config_data = self._load_default_config_data()
        beam_config_data = self._load_profile_config_data(profile_id)
        self._profiles_manifest['ActiveProfile'] = profile_id
        self._active_profile_id = profile_id
        self._sync_active_profile_name()
        self._mirror_active_profile_to_legacy_config(beam_config_data)
        self.saveProfiles()
        return beam_config_data, default_config_data

    def createProfile(self, name, config_data, source='current'):
        profile_name = str(name).strip()
        if profile_name == '':
            raise ValueError('Profile name cannot be empty')

        profile_id = self._slugify_profile_name(profile_name)
        default_config_data = self._load_default_config_data()
        if source == 'default':
            profile_config_data = deepcopy(default_config_data)
        else:
            profile_config_data = deepcopy(config_data)

        profile = {
            'Id': profile_id,
            'Name': profile_name,
            'File': os.path.join('profiles', profile_id + '.json'),
            'Locked': False,
            'Persisted': False,
        }
        self._profiles_manifest['Profiles'].append(profile)
        self._profiles_manifest['ActiveProfile'] = profile_id
        self._active_profile_id = profile_id
        self._sync_active_profile_name()
        self._dump_config_data(self._get_profile_path(profile), profile_config_data)
        self._mirror_active_profile_to_legacy_config(profile_config_data)
        self.saveProfiles()
        return deepcopy(profile), profile_config_data, default_config_data

    def renameProfile(self, profile_id, new_name):
        profile = self._get_profile_by_id(profile_id)
        if profile is None:
            raise KeyError("Unknown profile id '%s'" % profile_id)
        if profile.get('Locked'):
            raise ValueError("Profile '%s' cannot be renamed" % profile_id)

        profile_name = str(new_name).strip()
        if profile_name == '':
            raise ValueError('Profile name cannot be empty')

        profile['Name'] = profile_name
        self._sync_active_profile_name()
        self.saveProfiles()

    def deleteProfile(self, profile_id):
        profile = self._get_profile_by_id(profile_id)
        if profile is None:
            raise KeyError("Unknown profile id '%s'" % profile_id)
        if profile.get('Locked'):
            raise ValueError("Profile '%s' cannot be deleted" % profile_id)

        was_active = profile_id == self._active_profile_id
        profile_path = self._get_profile_path(profile)
        self._profiles_manifest['Profiles'] = [
            idx_profile for idx_profile in self._profiles_manifest.get('Profiles', [])
            if idx_profile.get('Id') != profile_id
        ]

        if os.path.isfile(profile_path):
            os.remove(profile_path)

        if was_active:
            self._profiles_manifest['ActiveProfile'] = 'default'
            self._active_profile_id = 'default'
            self._sync_active_profile_name()
            default_config_data = self._load_default_config_data()
            beam_config_data = self._load_profile_config_data('default')
            self._mirror_active_profile_to_legacy_config(beam_config_data)
            self.saveProfiles()
            return beam_config_data, default_config_data

        self.saveProfiles()
        return None, None