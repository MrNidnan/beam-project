# Profile Configuration Implementation Plan

## Goal

Add named Beam configuration profiles that let the user:

- open a Profile configuration page from the preferences icon list, below `Tags`
- see all available profiles with the current profile selected
- create, update, and delete profiles
- always keep a non-deletable `Default` profile
- switch the active profile from the UI
- save the current in-memory settings back into the selected profile
- have each profile contain the full Beam configuration, including settings, layout, rules, moods, and display-tag-related layout configuration
- replace the current in-memory configuration when a different profile is selected

## Current State

Beam currently persists one configuration file at `~/.beam/beamconfig.json`.

The main owner is `bin/beamsettings.py`:

- `loadConfig()` loads one config file plus the default resource config
- `dumpConfig()` writes the current `_beamConfigData` back to one file
- `_beamConfigData` already contains the full persisted configuration tree

The current preferences shell is built in `bin/mainframe.py` by `ListBookMenu`, which currently shows:

- `Preview`
- `Settings`
- `Layout`
- `Rules`
- `Tags`
- `DMX` on Linux and macOS

Relevant editing surfaces already mutate the in-memory `BeamSettings` object directly:

- `bin/dialogs/preferencespanels/basicsettingspanel.py`
- `bin/dialogs/preferencespanels/moodspanel.py`
- `bin/dialogs/preferencespanels/defaultlayoutpanel.py`
- `bin/dialogs/editmooddialog.py`
- `bin/dialogs/editlayoutitemdialog.py`

That means profile support should be centered on `BeamSettings`, not implemented separately in each panel.

## Scope Definition

Each profile should store a full copy of the persisted Beam configuration, not a partial overlay.

That includes at least:

- media player and refresh settings
- mood transition settings
- logging settings
- network display settings
- Foobar2000 Beefweb settings
- DMX settings
- `Rules`
- `Moods`
- the default layout and mood layouts inside `Moods[*].Display`

The `Tags` page itself is a preview/reference surface and does not currently persist independent state. In practice, the profile requirement for tag configuration maps to the layout items and rules that reference Beam tags.

## Proposed Storage Model

Use a profile manifest plus one config JSON file per profile.

Suggested files under `~/.beam`:

- `beamprofiles.json`
- `profiles/default.json`
- `profiles/<slug>.json`

Suggested manifest shape:

```json
{
  "ActiveProfile": "default",
  "Profiles": [
    {
      "Id": "default",
      "Name": "Default",
      "File": "profiles/default.json",
      "Locked": true
    }
  ]
}
```

Suggested rules:

- `Id` is a stable internal key used for filenames and selection
- `Name` is the user-facing label shown in the UI
- `Locked` is `true` for the built-in `Default` profile so it cannot be deleted
- each profile JSON file stores the same schema currently used by `beamconfig.json`

## Backward Compatibility and Migration

Migration should preserve existing installs without user intervention.

Startup migration flow:

1. If `beamprofiles.json` exists, load the manifest and active profile.
2. If it does not exist, create a profile store from the current single-file setup.
3. Use the current `~/.beam/beamconfig.json` as the initial contents for `Default`.
4. If `~/.beam/beamconfig.json` does not exist, fall back to `resources/json/beamconfig.json`.
5. Write `beamprofiles.json` and `profiles/default.json`.

Compatibility recommendation:

- continue writing the active profile back to `~/.beam/beamconfig.json` after save and profile switch

That shadow copy keeps older code paths, user expectations, and manual troubleshooting workflows intact while the new profile store becomes the source of truth.

## BeamSettings Changes

Extend `bin/beamsettings.py` into the profile owner.

Add new responsibilities:

- load and persist the profile manifest
- resolve the active profile path
- load a full config snapshot for a chosen profile
- save the current `_beamConfigData` into the active profile
- create a new profile from the current config or from the default config
- update profile metadata such as display name
- delete non-default profiles
- switch the active profile and reapply `_beamConfigData`

Suggested API additions on `BeamSettings`:

- `getProfiles()`
- `getActiveProfileId()`
- `getActiveProfileName()`
- `loadProfiles()`
- `saveProfiles()`
- `switchProfile(profileId)`
- `createProfile(name, source='current')`
- `renameProfile(profileId, newName)`
- `deleteProfile(profileId)`
- `saveActiveProfile()`
- `saveActiveProfileAs(profileId)` if a separate update action is useful

Suggested internal helpers:

- `_getProfilesManifestPath()`
- `_getProfilesDirectoryPath()`
- `_getProfileFilePath(profileId)`
- `_slugifyProfileName(name)`
- `_loadProfileManifest()`
- `_dumpProfileManifest()`
- `_ensureDefaultProfileExists()`
- `_mirrorActiveProfileToLegacyConfig()`

Important behavioral rule:

- `switchProfile(profileId)` must fully replace the current `_beamConfigData`, rerun the existing normalization path in `__setConfigData()`, and refresh any derived members such as `_moduleNames`, `_Universe1`, `_Universe2`, and OS-specific preference sizes

## UI Design

Add a new preferences page below `Tags` in `bin/mainframe.py`.

Implementation pieces:

- new panel file: `bin/dialogs/preferencespanels/profilespanel.py`
- new icon asset in `resources/icons/preferences/`, for example `6-Profiles32.png` or the next available index after the current set
- update `ListBookMenu.urllist`
- add the new panel to `ListBookMenu.pages`

Recommended page behavior:

- list all profiles in a `wx.ListBox` or `wx.ListCtrl`
- highlight the active profile
- show `Default` as non-deletable
- provide buttons:
  - `Switch`
  - `Save`
  - `Create`
  - `Rename`
  - `Delete`
- optionally provide a short status label such as `Active profile: Milonga Hall`

Recommended interactions:

- selecting a profile and clicking `Switch` applies that profile immediately
- clicking `Save` writes the current in-memory settings into the selected active profile
- clicking `Create` asks for a profile name and copies the current config snapshot into a new profile
- clicking `Rename` changes the display name but not the locked default profile
- clicking `Delete` removes the selected non-default profile after confirmation

## Replace Current State on Profile Switch

Switching profiles must do more than just change a filename pointer.

Required flow:

1. Prompt to save the current profile if there are unsaved changes.
2. Load the selected profile JSON.
3. Load the resource default config.
4. Re-run `__setConfigData()` to merge defaults and rebuild derived state.
5. Update the main frame through the existing refresh path.
6. Refresh any open preferences pages so controls show the newly selected profile data.

The current refresh anchor is `MainFrame.updateSettings()` in `bin/mainframe.py`. That method already restarts the network service and republishes display state, so it should be reused after profile switches and profile saves.

## Unsaved Changes Strategy

Profile switching and profile deletion become risky if in-memory edits are not tracked.

Recommended minimal approach:

- add a dirty flag to `BeamSettings`, set by mutating setters and by panels that directly edit nested lists or dicts
- clear the dirty flag after `saveActiveProfile()` and after loading a profile
- before switching profiles, prompt:
  - `Save current profile`
  - `Discard changes`
  - `Cancel`

Short-term fallback if full dirty tracking is too invasive:

- always prompt before switching profiles when the preferences window is open

The dirty-flag approach is preferable because many panels mutate `getMoods()` and `getRules()` directly.

## Panel Refresh Strategy

Several existing panels populate controls only once in `__init__`.

To support profile switching without closing the preferences window, add a lightweight refresh contract to affected panels:

- `BasicSettingsPanel.reloadFromSettings()`
- `MoodsPanel.reloadFromSettings()`
- `RulesPanel.reloadFromSettings()`
- `DisplayPanel.reloadFromSettings()` if needed
- `ProfilesPanel.reloadFromSettings()`

Each method should repopulate widgets from the current `BeamSettings` values without rebuilding the entire frame.

## Default Profile Rules

The `Default` profile should always exist.

Rules:

- cannot be deleted
- may be selected like any other profile
- may be updated with current settings
- may optionally be kept non-renamable to simplify migration and support logic

Recommendation:

- keep `Default` non-deletable and non-renamable in the first version

## Create and Update Semantics

The user request distinguishes between creating a profile and saving the selected profile with current settings.

Recommended semantics:

- `Create`: copy the current in-memory configuration into a new named profile and make it active
- `Save`: overwrite the currently active profile file with the current in-memory configuration
- `Delete`: remove the selected profile, then switch to `Default` if the deleted profile was active

This keeps the model simple and matches the current single-config mental model.

## Proposed Delivery Steps

### Phase 1: Core profile persistence

- add manifest and profile file helpers in `bin/beamsettings.py`
- migrate existing single-file config into `Default`
- load and save the active profile
- mirror active profile to legacy `beamconfig.json`

### Phase 2: Profile UI

- add `ProfilesPanel`
- add preferences icon and page registration in `bin/mainframe.py`
- implement create, save, delete, and switch actions

### Phase 3: Runtime refresh

- refresh display and network state after profile switch
- add panel reload methods so the preferences UI updates in place

### Phase 4: Safety and polish

- add dirty tracking and unsaved-change prompt
- add rename support if still desired after the first usable version
- document profile storage in README or wiki

## Validation Plan

Manual checks:

1. Existing users with only `~/.beam/beamconfig.json` are migrated automatically into `Default`.
2. A new profile created from current settings preserves rules, moods, and default layout.
3. Switching profiles changes the display output immediately.
4. Saving the active profile persists changes across app restart.
5. Deleting a non-default profile removes it from the list and disk.
6. `Default` cannot be deleted.
7. Legacy `~/.beam/beamconfig.json` still reflects the active profile after save.
8. Linux, macOS, and Windows still rebuild OS-specific module and DMX choices correctly after profile switch.

## Risks

- many panels mutate nested configuration structures directly, which makes dirty tracking easy to miss
- profile switching while dialogs are open may leave stale widget state unless reload hooks are added
- changing `beamconfig.json` ownership too aggressively could break old assumptions in docs and support guidance
- default config merging in `__setConfigData()` must continue to run for every profile load to avoid schema drift

## Recommended First Milestone

Deliver a first version with:

- `Default` plus additional named profiles
- create, switch, save, and delete
- active profile shown in a dedicated Preferences page below `Tags`
- full config snapshot per profile
- runtime refresh after switching

Defer until a second pass:

- rename support
- import/export
- duplicate profile action
- per-profile dirty diff view
