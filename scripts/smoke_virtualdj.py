#!/usr/bin/env python

import http.server
import os
import socketserver
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUEST_LOG = []
PRIMARY_HISTORY_PATH = 'music/Ricardo Tanturi/Una Emocion.flac'
PRIMARY_NETWORK_PATH = 'music/Osvaldo Pugliese/La Yumba.flac'


class VirtualDJHandler(http.server.BaseHTTPRequestHandler):
    RESPONSES = {
        "deck master is_audible ? deck master get_artist_title : get_text ''": 'Osvaldo Pugliese - La Yumba',
        "deck master get_text \"artist=`deck master get_loaded_song 'artist'`\\ntitle=`deck master get_loaded_song 'title'`\\nalbum=`deck master get_loaded_song 'album'`\\ngenre=`deck master get_loaded_song 'genre'`\\nyear=`deck master get_loaded_song 'year'`\\nfilepath=`deck master get_loaded_song 'filepath'`\"": (
            'artist=Osvaldo Pugliese\n'
            'title=La Yumba\n'
            'album=1944\n'
            'genre=Tango\n'
            'year=1944\n'
            'filepath=' + PRIMARY_NETWORK_PATH
        ),
    }

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path != '/query':
            self.send_response(404)
            self.end_headers()
            return

        script = params.get('script', [''])[0]
        bearer = params.get('bearer', [''])[0]
        auth_header = self.headers.get('Authorization', '')
        REQUEST_LOG.append((script, bearer, auth_header))

        if bearer != '' or auth_header != 'Bearer secret-token':
            self.send_response(401)
            self.end_headers()
            return

        body = self.RESPONSES.get(script, '').encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args, **kwargs):
        # Silence the test server's request logging to keep CI output stable.
        pass


def main():
    temp_home = tempfile.mkdtemp(prefix='beam-virtualdj-smoke-')
    os.environ['HOME'] = temp_home
    os.environ['USERPROFILE'] = temp_home
    os.environ['LOCALAPPDATA'] = temp_home

    from bin.beamsettings import beamSettings
    from bin.modules import virtualdjmodule

    history_dir = Path(temp_home) / 'VirtualDJ' / 'History'
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / 'tracklist.txt').write_text(
        '22:44 : Juan D\'Arienzo - Paciencia\n'
        '22:45 : deck=1 Oscar Larroca - Tango - Remolino\n'
        '22:46 : deck=1 artist=Ricardo Tanturi genre=Tango title=Una Emocion year=1942 filepath=' + PRIMARY_HISTORY_PATH + '\n'
        '22:47 : deck=2 artist=Preview Artist genre=Preview title=Should Be Ignored year=1942\n',
        encoding='utf-8',
    )

    beamSettings.loadConfig()
    beamSettings.setSelectedModuleName('VirtualDJ')
    beamSettings.setVirtualDJIntegrationMode('History File')
    beamSettings.setVirtualDJHistoryPath('')
    beamSettings.setVirtualDJRecentTrackWindowSec(300)
    beamSettings.setVirtualDJHistoryDeck('Deck 1')

    playlist, status, details = virtualdjmodule.run_with_details(beamSettings.getMaxTandaLength(), [], emit_debug_log=False)

    assert status == 'Playing'
    assert len(playlist) == 1
    assert details['route'] == 'history'
    assert playlist[0].Artist == 'Ricardo Tanturi'
    assert playlist[0].Genre == 'Tango'
    assert playlist[0].Title == 'Una Emocion'
    assert playlist[0].Year == '1942'
    assert playlist[0].FilePath == PRIMARY_HISTORY_PATH

    legacy_song = virtualdjmodule.get_song_from_text('22:45 : deck=1 Oscar Larroca - Tango - Remolino')
    assert legacy_song.Artist == 'Oscar Larroca'
    assert legacy_song.Genre == 'Tango'
    assert legacy_song.Title == 'Remolino'

    oldest_legacy_song = virtualdjmodule.get_song_from_text('22:44 : Juan D\'Arienzo - Paciencia')
    assert oldest_legacy_song.Artist == 'Juan D\'Arienzo'
    assert oldest_legacy_song.Title == 'Paciencia'

    beamSettings.setVirtualDJHistoryDeck('Deck 2')
    playlist, status, details = virtualdjmodule.run_with_details(beamSettings.getMaxTandaLength(), [], emit_debug_log=False)

    assert status == 'Playing'
    assert len(playlist) == 1
    assert details['historyDeck'] == '2'
    assert playlist[0].Artist == 'Preview Artist'
    assert playlist[0].Genre == 'Preview'
    assert playlist[0].Title == 'Should Be Ignored'

    beamSettings.setVirtualDJHistoryDeck('-1')
    playlist, status, details = virtualdjmodule.run_with_details(beamSettings.getMaxTandaLength(), [], emit_debug_log=False)

    assert status == 'Playing'
    assert len(playlist) == 1
    assert details['historyDeck'] == '-1'
    assert playlist[0].Artist == 'Preview Artist'

    beamSettings.setVirtualDJHistoryDeck('Deck 1')

    server = socketserver.TCPServer(('127.0.0.1', 0), VirtualDJHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        beamSettings.setVirtualDJIntegrationMode('Network Control')
        beamSettings.setVirtualDJHost('127.0.0.1')
        beamSettings.setVirtualDJPort(server.server_address[1])
        beamSettings.setVirtualDJBearerToken('secret-token')
        beamSettings.setVirtualDJQueryMode('Master')

        playlist, status, details = virtualdjmodule.run_with_details(beamSettings.getMaxTandaLength(), [], emit_debug_log=False)

        assert status == 'Playing'
        assert len(playlist) == 1
        assert details['route'] == 'network'

        song = playlist[0]
        assert song.Artist == 'Osvaldo Pugliese'
        assert song.Title == 'La Yumba'
        assert song.Album == '1944'
        assert song.Genre == 'Tango'
        assert song.Year == '1944'
        assert song.FilePath == PRIMARY_NETWORK_PATH

        requested_scripts = [entry[0] for entry in REQUEST_LOG]
        assert "deck master is_audible ? deck master get_artist_title : get_text ''" in requested_scripts
        assert "deck master get_text \"artist=`deck master get_loaded_song 'artist'`\\ntitle=`deck master get_loaded_song 'title'`\\nalbum=`deck master get_loaded_song 'album'`\\ngenre=`deck master get_loaded_song 'genre'`\\nyear=`deck master get_loaded_song 'year'`\\nfilepath=`deck master get_loaded_song 'filepath'`\"" in requested_scripts
        assert all(entry[1] == '' for entry in REQUEST_LOG)
        assert all(entry[2] == 'Bearer secret-token' for entry in REQUEST_LOG)

        beamSettings.setVirtualDJIntegrationMode('Auto (Network -> History)')
        beamSettings.setVirtualDJPort(server.server_address[1] + 1)

        playlist, status, details = virtualdjmodule.run_with_details(beamSettings.getMaxTandaLength(), [], emit_debug_log=False)

        assert status == 'Playing'
        assert len(playlist) == 1
        assert details['route'] == 'fallback-history'
        assert playlist[0].Artist == 'Ricardo Tanturi'
        assert playlist[0].Title == 'Una Emocion'
        assert playlist[0].FilePath == PRIMARY_HISTORY_PATH

        print('VirtualDJ smoke test passed')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()