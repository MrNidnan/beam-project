#!/usr/bin/env python

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read(path):
    return Path(path).read_text(encoding='utf-8')


def _method_source(source, method_name):
    marker = 'def {0}('.format(method_name)
    start = source.find(marker)
    assert start != -1, 'method not found: {0}'.format(method_name)
    next_start = source.find('\n    def ', start + len(marker))
    if next_start == -1:
        return source[start:]
    return source[start:next_start]


def main():
    basic_path = ROOT / 'bin' / 'dialogs' / 'preferencespanels' / 'basicsettingspanel.py'
    profiles_path = ROOT / 'bin' / 'dialogs' / 'preferencespanels' / 'profilespanel.py'
    mainframe_path = ROOT / 'bin' / 'mainframe.py'

    basic_source = _read(basic_path)
    profiles_source = _read(profiles_path)
    mainframe_source = _read(mainframe_path)

    # Explicit apply action should exist in settings UI and call the network apply path.
    assert "label='Apply'" in basic_source, 'missing compact Apply button label'
    assert 'def OnApplyNetworkChanges(' in basic_source, 'missing explicit apply handler'
    apply_button_handler = _method_source(basic_source, 'OnApplyNetworkChanges')
    assert "_applyNetworkServiceState(reason='manual apply button')" in apply_button_handler

    # Enable/disable is an allowed trigger.
    network_toggle_handler = _method_source(basic_source, 'OnNetworkEnabled')
    assert "_applyNetworkServiceState(reason='enable toggle')" in network_toggle_handler

    # Host/port field edits should only update settings, not apply immediately.
    network_host_handler = _method_source(basic_source, 'OnNetworkHostChanged')
    network_port_handler = _method_source(basic_source, 'OnNetworkPortChanged')
    assert '_applyNetworkServiceState(' not in network_host_handler
    assert '_applyNetworkServiceState(' not in network_port_handler

    # Profile switch should explicitly re-apply network settings after switching.
    refresh_after_profile_change = _method_source(profiles_source, 'refreshAfterProfileChange')
    assert "applyNetworkServiceState(reason='profile switch')" in refresh_after_profile_change

    # Generic settings updates should not restart the network service anymore.
    update_settings_handler = _method_source(mainframe_source, 'updateSettings')
    assert 'self.networkService.stop()' not in update_settings_handler
    assert 'self.networkService.start()' not in update_settings_handler

    print('Network apply wiring smoke test passed')


if __name__ == '__main__':
    main()
