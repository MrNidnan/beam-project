#!/usr/bin/env python

import platform
import socket
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _free_port():
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def _is_port_open(port):
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(0.2)
    try:
        return probe.connect_ex(('127.0.0.1', port)) == 0
    finally:
        probe.close()


def _wait_for_port_state(port, expected_open, timeout_seconds=8):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _is_port_open(port) == expected_open:
            return True
        time.sleep(0.05)
    return _is_port_open(port) == expected_open


def _assert_port_can_bind(port):
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(('127.0.0.1', port))
    finally:
        probe.close()


def main():
    if platform.system() not in ('Windows', 'Linux'):
        print('Network display port smoke test skipped: target is Windows/Linux')
        return

    try:
        from bin.beamsettings import beamSettings
    except ModuleNotFoundError as exc:
        if str(exc) == "No module named 'wx'":
            print('Network display port smoke test skipped: wxPython is not installed in this environment')
            return
        raise

    from bin.network import BeamNetworkService

    beamSettings.loadConfig()

    original_enabled = beamSettings.getNetworkServiceEnabled()
    original_host = beamSettings.getNetworkServiceHost()
    original_port = beamSettings.getNetworkServicePort()

    service = BeamNetworkService()
    test_port = _free_port()
    next_port = _free_port()
    while next_port == test_port:
        next_port = _free_port()

    try:
        beamSettings.setNetworkServiceEnabled(True)
        beamSettings.setNetworkServiceHost('127.0.0.1')
        beamSettings.setNetworkServicePort(test_port)

        service.start()
        assert _wait_for_port_state(test_port, True), 'service did not open first test port'

        service.stop()
        assert _wait_for_port_state(test_port, False), 'service did not release first test port'
        _assert_port_can_bind(test_port)

        beamSettings.setNetworkServicePort(next_port)
        service.start()
        assert _wait_for_port_state(next_port, True), 'service did not open second test port'

        service.stop()
        assert _wait_for_port_state(next_port, False), 'service did not release second test port'
        _assert_port_can_bind(next_port)
    finally:
        try:
            service.stop()
        except Exception:
            pass
        beamSettings.setNetworkServiceEnabled(original_enabled)
        beamSettings.setNetworkServiceHost(original_host)
        beamSettings.setNetworkServicePort(original_port)

    print('Network display port smoke test passed')


if __name__ == '__main__':
    main()
