#!/usr/bin/env python

import gc
import os
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n'
    b'\x00\x00\x00\rIHDR'
    b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    b'\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x04\x00\x01\xf6\x178U'
    b'\x00\x00\x00\x00IEND\xaeB`\x82'
)


def write_png(path):
    Path(path).write_bytes(PNG_BYTES)


def get_memory_usage_bytes():
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == 'darwin':
            return int(rss)
        return int(rss) * 1024
    except ImportError:
        if sys.platform == 'win32':
            import ctypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ('cb', ctypes.c_ulong),
                    ('PageFaultCount', ctypes.c_ulong),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(ProcessMemoryCounters)
            ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(counters),
                counters.cb,
            )
            return int(counters.WorkingSetSize)
        return 0


def main():
    import wx

    from bin.dialogs.preferencespanels.displaypanel import DisplayPanel

    temp_root = Path(tempfile.mkdtemp(prefix='beam-layered-repaint-soak-'))
    image_paths = []
    for idx in range(12):
        path = temp_root / ('image-%02d.png' % idx)
        write_png(path)
        image_paths.append(str(path))

    class FakeLogNull:
        pass

    class FakeImage:
        def __init__(self, source):
            self.source = source

        def IsOk(self):
            return True

        def GetWidth(self):
            return 1920

        def GetHeight(self):
            return 1080

        def Scale(self, width, height, quality):
            self.size = (width, height, quality)
            return self

        def AdjustChannels(self, red, green, blue, alpha):
            self.channels = (red, green, blue, alpha)
            return self

    class FakeBitmap:
        def __init__(self, image):
            self.image = image

        def GetSize(self):
            return (1280, 720)

    fake_display = SimpleNamespace(
        red=1.0,
        green=1.0,
        blue=1.0,
        alpha=1.0,
    )
    fake_panel = SimpleNamespace(
        _background_bitmap_cache=OrderedDict(),
        _background_bitmap_cache_limit=8,
        displayData=fake_display,
    )

    baseline_memory = get_memory_usage_bytes()

    with patch.object(wx, 'LogNull', FakeLogNull), \
         patch.object(wx, 'Image', FakeImage), \
         patch.object(wx, 'Bitmap', FakeBitmap):
        for iteration in range(200):
            base_path = image_paths[iteration % len(image_paths)]
            overlay_path = image_paths[(iteration + 5) % len(image_paths)]

            DisplayPanel._get_scaled_background_bitmap(fake_panel, base_path, 1280, 720, 1.0)
            DisplayPanel._get_scaled_background_bitmap(fake_panel, overlay_path, 1280, 720, 0.35)
            if iteration % 20 == 0:
                gc.collect()

    final_memory = get_memory_usage_bytes()
    cache_size = len(fake_panel._background_bitmap_cache)
    growth_mb = (final_memory - baseline_memory) / float(1024 * 1024) if final_memory and baseline_memory else 0.0

    assert cache_size <= fake_panel._background_bitmap_cache_limit

    print('Layered repaint soak completed')
    print('Cache size:', cache_size)
    print('Working set delta MB: %.2f' % growth_mb)


if __name__ == '__main__':
    main()