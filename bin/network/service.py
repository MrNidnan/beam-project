import asyncio
import json
import logging
import os
import threading
from copy import deepcopy

from bin.beamsettings import beamSettings
from bin.beamutils import getBeamHomePath
from bin.mutagenutils import readCoverArtData
from bin.network.events import build_event
from bin.network.schema import empty_snapshot, snapshot_from_display_data

try:
    from aiohttp import web
except ImportError:
    web = None


class BeamNetworkService(object):

    def __init__(self):
        self._lock = threading.RLock()
        self._clients = set()
        self._loop = None
        self._thread = None
        self._runner = None
        self._site = None
        self._started = False
        self._available = web is not None
        self._sequence = 0
        self._latest_snapshot = empty_snapshot(beamSettings)
        self._latest_serialized = json.dumps(self._latest_snapshot, sort_keys=True)

    def _reset_runtime_state(self):
        self._clients = set()
        self._runner = None
        self._site = None
        self._thread = None
        self._loop = None
        self._started = False

    def start(self):
        if not beamSettings.getNetworkServiceEnabled():
            return

        if not self._available:
            logging.warning('Beam network service disabled: aiohttp is not installed.')
            return

        if self._started:
            return

        try:
            self._started = True
            self._thread = threading.Thread(target=self._run_server, name='BeamNetworkService', daemon=True)
            self._thread.start()
        except Exception as e:
            self._reset_runtime_state()
            logging.error('Beam network service failed to start.', exc_info=True)

    def stop(self):
        if not self._started:
            return

        self._started = False

        if self._loop is not None and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                logging.error(e, exc_info=True)

        if self._thread is not None:
            self._thread.join(timeout=5)

        self._thread = None
        self._loop = None

    def publish_display_state(self, display_data):
        if not self._started:
            return False

        snapshot = snapshot_from_display_data(display_data, beamSettings)
        serialized = json.dumps(snapshot, sort_keys=True)

        with self._lock:
            if serialized == self._latest_serialized:
                return False

            self._latest_snapshot = snapshot
            self._latest_serialized = serialized
            self._sequence += 1
            event = build_event('state.updated', self._sequence, deepcopy(snapshot))

        if self._loop is not None and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast(event), self._loop)

        return True

    def get_state_document(self):
        with self._lock:
            return {
                'protocolVersion': self._latest_snapshot['protocolVersion'],
                'schemaVersion': self._latest_snapshot['schemaVersion'],
                'sequence': self._sequence,
                'snapshot': deepcopy(self._latest_snapshot),
            }

    def _run_server(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        app = web.Application()
        app.router.add_get('/', self._handle_index)
        app.router.add_get('/now-playing', self._handle_now_playing)
        app.router.add_get('/events', self._handle_events)
        app.router.add_get('/media/background/current', self._handle_background)
        app.router.add_get('/media/background/{layer}', self._handle_background)
        app.router.add_get('/media/cover-art/current', self._handle_cover_art)
        app.router.add_static('/static/', self._get_static_directory())

        self._runner = web.AppRunner(app)

        try:
            self._loop.run_until_complete(self._runner.setup())
            self._site = web.TCPSite(
                self._runner,
                beamSettings.getNetworkServiceHost(),
                beamSettings.getNetworkServicePort(),
            )
            self._loop.run_until_complete(self._site.start())
            logging.info(
                'Beam network service listening on http://{0}:{1}'.format(
                    beamSettings.getNetworkServiceHost(),
                    beamSettings.getNetworkServicePort(),
                )
            )
            self._loop.run_forever()
        except Exception as e:
            logging.error('Beam network service failed during setup or runtime.', exc_info=True)
        finally:
            try:
                if self._runner is not None:
                    self._loop.run_until_complete(self._runner.cleanup())
            except Exception as e:
                logging.error(e, exc_info=True)
            try:
                self._loop.close()
            finally:
                self._reset_runtime_state()

    async def _shutdown(self):
        clients = list(self._clients)
        for client in clients:
            try:
                await client.close()
            except Exception as e:
                logging.error(e, exc_info=True)

        if self._runner is not None:
            await self._runner.cleanup()

        self._loop.stop()

    async def _broadcast(self, event_document):
        clients = list(self._clients)

        for client in clients:
            if client.closed:
                self._clients.discard(client)
                continue

            try:
                await client.send_json(event_document)
            except Exception as e:
                logging.error(e, exc_info=True)
                self._clients.discard(client)

    async def _handle_index(self, request):
        return web.FileResponse(os.path.join(self._get_static_directory(), 'index.html'))

    async def _handle_now_playing(self, request):
        return web.json_response(self.get_state_document())

    async def _handle_events(self, request):
        websocket = web.WebSocketResponse(heartbeat=30)
        await websocket.prepare(request)

        self._clients.add(websocket)
        await websocket.send_json(build_event('session.hello', self._sequence, self.get_state_document()['snapshot']))

        try:
            async for message in websocket:
                if message.type == web.WSMsgType.ERROR:
                    logging.error(websocket.exception(), exc_info=True)
        finally:
            self._clients.discard(websocket)

        return websocket

    def _get_snapshot_background_path(self, layer_name):
        background_data = self._latest_snapshot.get('background', {})
        if layer_name == 'base':
            layer_data = background_data.get('base', {})
            return layer_data.get('currentPath', '') or layer_data.get('sourcePath', '')
        if layer_name == 'overlay':
            layer_data = background_data.get('overlay', {})
            return layer_data.get('currentPath', '') or layer_data.get('sourcePath', '')
        return background_data.get('sourcePath', '')

    async def _handle_background(self, request):
        layer_name = request.match_info.get('layer', 'current')
        with self._lock:
            background_path = self._get_snapshot_background_path(layer_name)

        if background_path and os.path.isfile(background_path):
            return web.FileResponse(background_path)

        raise web.HTTPNotFound()

    async def _handle_cover_art(self, request):
        with self._lock:
            cover_art_path = self._latest_snapshot.get('coverArt', {}).get('sourcePath', '')

        if not cover_art_path:
            raise web.HTTPNotFound()

        image_bytes, mime_type = readCoverArtData(cover_art_path)
        if not image_bytes:
            raise web.HTTPNotFound()

        return web.Response(
            body=image_bytes,
            content_type=mime_type or 'application/octet-stream',
            headers={'Cache-Control': 'no-store'},
        )

    def _get_static_directory(self):
        return os.path.join(getBeamHomePath(), beamSettings.getNetworkServiceWebRoot())