#!/usr/bin/env python

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def install_dbus_stub():
    dbus_module = types.ModuleType("dbus")

    class FakeDbusObject:
        def Get(self, *args, **kwargs):
            return None

    class FakeSessionBus:
        def name_has_owner(self, *args, **kwargs):
            return True

        def get_object(self, *args, **kwargs):
            return FakeDbusObject()

    def interface(obj, interface_name):
        return obj

    dbus_module.SessionBus = FakeSessionBus
    dbus_module.Interface = interface
    sys.modules["dbus"] = dbus_module


def install_ola_stub():
    ola_module = types.ModuleType("ola")
    client_wrapper_module = types.ModuleType("ola.ClientWrapper")

    class FakeStatus:
        message = "stubbed"

        def Succeeded(self):
            return True

    class FakeClient:
        REGISTER = 0

        def SendDmx(self, universe, data, callback):
            callback(FakeStatus())

        def RegisterUniverse(self, universe, register_mode, callback):
            callback([])

    class FakeClientWrapper:
        def __init__(self):
            self._client = FakeClient()

        def Client(self):
            return self._client

        def Run(self):
            return None

        def Stop(self):
            return None

    client_wrapper_module.ClientWrapper = FakeClientWrapper
    ola_module.ClientWrapper = client_wrapper_module
    sys.modules["ola"] = ola_module
    sys.modules["ola.ClientWrapper"] = client_wrapper_module


def import_module_fresh(module_name):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def clear_modules(prefixes):
    for module_name in list(sys.modules):
        for prefix in prefixes:
            if module_name == prefix or module_name.startswith(prefix + "."):
                del sys.modules[module_name]
                break


def import_platform_module_group(package_name):
    package_path = ROOT / package_name.replace(".", "/")
    imported = []
    for file_path in sorted(package_path.glob("*.py")):
        if file_path.name == "__init__.py":
            continue
        module_name = package_name + "." + file_path.stem
        import_module_fresh(module_name)
        imported.append(module_name)
    return imported


def import_nowplayingdata_for_platform(platform_name):
    clear_modules(["bin.nowplayingdata"])
    with patch("platform.system", return_value=platform_name):
        importlib.import_module("bin.nowplayingdata")


def main():
    install_dbus_stub()
    install_ola_stub()

    imported_modules = []
    imported_modules.extend(import_platform_module_group("bin.modules.lin"))
    imported_modules.extend(import_platform_module_group("bin.modules.mac"))
    imported_modules.append(import_module_fresh("bin.DMX.olamodule").__name__)

    import_nowplayingdata_for_platform("Linux")
    import_nowplayingdata_for_platform("Darwin")

    print("Imported platform-gated modules:")
    for module_name in imported_modules:
        print(module_name)
    print("Imported bin.nowplayingdata for Linux and Darwin with mocked dependencies")


if __name__ == "__main__":
    main()