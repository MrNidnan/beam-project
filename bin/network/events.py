from datetime import datetime, timezone

PROTOCOL_VERSION = 1
SCHEMA_VERSION = '2026-04-24'


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def build_event(event_type, sequence, snapshot):
    return {
        'type': event_type,
        'protocolVersion': PROTOCOL_VERSION,
        'schemaVersion': SCHEMA_VERSION,
        'sequence': sequence,
        'timestamp': utc_now_iso(),
        'snapshot': snapshot,
    }