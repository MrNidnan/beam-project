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


class VirtualDJHandler(http.server.BaseHTTPRequestHandler):
    RESPONSES = {
        "deck master is_audible ? deck master get_artist_title : get_text ''": 'Osvaldo Pugliese - La Yumba',
        "deck master get_loaded_song 'artist'": 'Osvaldo Pugliese',
        "deck master get_loaded_song 'title'": 'La Yumba',
        "deck master get_loaded_song 'album'": '1944',
        "deck master get_loaded_song 'genre'": 'Tango',
        "deck master get_loaded_song 'year'": '1944',
        "deck master get_loaded_song 'filepath'": r'C:\Music\Osvaldo Pugliese\La Yumba.flac',
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

        if bearer != 'secret-token' or auth_header != 'Bearer secret-token':
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

    from bin.beamsettings import beamSettings
    from bin.modules import virtualdjmodule

    server = socketserver.TCPServer(('127.0.0.1', 0), VirtualDJHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        beamSettings.loadConfig()
        beamSettings.setSelectedModuleName('VirtualDJ')
        beamSettings.setVirtualDJHost('127.0.0.1')
        beamSettings.setVirtualDJPort(server.server_address[1])
        beamSettings.setVirtualDJBearerToken('secret-token')
        beamSettings.setVirtualDJQueryMode('Master')

        playlist, status = virtualdjmodule.run(beamSettings.getMaxTandaLength(), [])

        assert status == 'Playing'
        assert len(playlist) == 1

        song = playlist[0]
        assert song.Artist == 'Osvaldo Pugliese'
        assert song.Title == 'La Yumba'
        assert song.Album == '1944'
        assert song.Genre == 'Tango'
        assert song.Year == '1944'
        assert song.FilePath == r'C:\Music\Osvaldo Pugliese\La Yumba.flac'

        requested_scripts = [entry[0] for entry in REQUEST_LOG]
        assert "deck master is_audible ? deck master get_artist_title : get_text ''" in requested_scripts
        assert "deck master get_loaded_song 'artist'" in requested_scripts
        assert "deck master get_loaded_song 'filepath'" in requested_scripts

        print('VirtualDJ smoke test passed')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()