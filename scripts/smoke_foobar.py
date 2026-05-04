#!/usr/bin/env python

import base64
import http.server
import json
import socketserver
import sys
import threading
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUEST_LOG = []
PRIMARY_ARTIST = 'Carlos Di Sarli'
PRIMARY_TITLE = 'Bahia Blanca'
PRIMARY_PATH = r'C:\Music\Carlos Di Sarli\Bahia Blanca.flac'


class FoobarHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        auth_header = self.headers.get('Authorization', '')
        REQUEST_LOG.append((parsed.path, query, auth_header))

        if auth_header != 'Basic ' + base64.b64encode(b'beam:secret').decode('ascii'):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Beefweb"')
            self.end_headers()
            return

        if parsed.path == '/api/player':
            body = {
                'player': {
                    'playbackState': 'playing',
                    'activeItem': {
                        'playlistId': 'main',
                        'index': 3,
                        'columns': [
                            PRIMARY_ARTIST,
                            'Instrumentales',
                            PRIMARY_TITLE,
                            'Tango',
                            '',
                            '',
                            '1957',
                            PRIMARY_ARTIST,
                            '',
                            PRIMARY_PATH,
                        ],
                    },
                },
            }
        elif parsed.path == '/api/playlists/main/items/3:4':
            body = {
                'playlistItems': {
                    'items': [
                        {
                            'columns': [
                                PRIMARY_ARTIST,
                                'Instrumentales',
                                PRIMARY_TITLE,
                                'Tango',
                                '',
                                '',
                                '1957',
                                PRIMARY_ARTIST,
                                '',
                                PRIMARY_PATH,
                            ],
                        },
                        {
                            'columns': [
                                'Osvaldo Pugliese',
                                'En Vivo',
                                'La Yumba',
                                'Tango',
                                '',
                                '',
                                '1946',
                                'Osvaldo Pugliese',
                                '',
                                r'C:\Music\Osvaldo Pugliese\La Yumba.flac',
                            ],
                        },
                    ],
                },
            }
        else:
            self.send_response(404)
            self.end_headers()
            return

        payload = json.dumps(body).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args, **kwargs):
        # Keep the smoke test output stable and focused on assertion failures.
        pass


def main():
    from bin.beamsettings import beamSettings
    from bin.modules.win import foobar2kmodule

    server = socketserver.TCPServer(('127.0.0.1', 0), FoobarHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        config_data = beamSettings.loadConfigData(beamSettings.getDefaultConfigFilePath())
        config_data['Module'] = 'Foobar2000'
        Path(beamSettings.getBeamConfigFilePath()).parent.mkdir(parents=True, exist_ok=True)
        beamSettings.dumpConfigData(beamSettings.getBeamConfigFilePath(), config_data)
        beamSettings.loadConfig()
        beamSettings.setSelectedModuleName('Foobar2000')
        beamSettings.setFoobarBeefwebUrl('http://127.0.0.1:{0}/api/'.format(server.server_address[1]))
        beamSettings.setFoobarBeefwebUser('beam')
        beamSettings.setFoobarBeefwebPassword('secret')

        playlist, status, details = foobar2kmodule.run_with_details(4, emit_debug_log=False)

        assert status == 'Playing'
        assert details['route'] == 'beefweb'
        assert details['baseUrl'] == 'http://127.0.0.1:{0}/api'.format(server.server_address[1])
        assert details['authMode'] == 'basic-auth'
        assert details['activePlaylistId'] == 'main'
        assert details['activeIndex'] == '3'
        assert len(playlist) == 2
        assert playlist[0].Artist == PRIMARY_ARTIST
        assert playlist[0].Title == PRIMARY_TITLE
        assert playlist[0].FilePath == PRIMARY_PATH

        request_paths = [entry[0] for entry in REQUEST_LOG]
        assert '/api/player' in request_paths
        assert '/api/playlists/main/items/3:4' in request_paths
        assert any(entry[2].startswith('Basic ') for entry in REQUEST_LOG)

        print('Foobar2000 smoke test passed')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()