# Network Display (Browser & Tablet)

Beam can publish the live display over your local network, so a phone, tablet,
laptop, or any browser can show the same song information as your projector.

![Beam browser display on a tablet](images/user-manual/beam_web_tablet.jpeg)

## What it does

The network display shows the current mood layout — song info, cover art, and
backgrounds — in a browser, and updates live when the track changes. Several
devices can connect at the same time, with low latency.

## When to use it

- A tablet at the DJ table
- A small side display somewhere in the venue
- Checking the output from another device
- When the DJ laptop and the display device are not the same machine

## How to enable it

1. Open Beam `Settings`.
2. Go to `Network Display`.
3. Enable the network display service.
4. Beam shows the local address you can open in a browser.

![Network display settings with host, port, and the local URL](images/user-manual/beam_network_settings.png)

The status bar shows **Network: ON** when the service is running, and
**Network: OFF** when it is not.

## How to open it from another device

1. Make sure the other device is on the **same Wi-Fi / network** as the Beam
   laptop.
2. Open the address Beam shows (something like `http://192.168.1.50:8765`) in any
   browser.
3. The current song and background should appear, updating as tracks change.

The browser can go full screen and keep the screen awake when you tap it.

## Host, port, and local address — what they mean

- **Host** — which network interface Beam listens on. `0.0.0.0` means "all
  interfaces", so other devices on the network can reach it. Beam shows a detected
  local IP address as a hint for the URL to open.
- **Port** — the door number on the laptop. The default is **8765**. You can
  change it in `Settings > Network Display` if that port is busy.
- **Local address** — the full `http://<ip>:<port>` URL to type on the other
  device.

## Troubleshooting

**Another device cannot connect — check, in order:**

- **Same network** — both devices must be on the same Wi-Fi/LAN. Guest networks
  often block device-to-device traffic.
- **Service enabled** — confirm the status bar shows **Network: ON**.
- **Right IP** — use the address Beam shows. The laptop's IP can change between
  sessions or networks.
- **Firewall** — your firewall may block Beam. On Linux especially, you may need
  to open the port. Allow Beam (or the port) through the firewall.
- **Port already in use** — if another program uses the port, change Beam's
  **Port** to a free one and reopen the new address.
- **Browser refresh** — if a device shows a stale screen, refresh the page; it
  reconnects automatically.

## More technical detail

For the HTTP/WebSocket API and internals, see
[NETWORK_DISPLAY.md](../NETWORK_DISPLAY).

---

[Home](../) ·
[Download](../download) ·
[Getting Started](../getting-started) ·
[Features](../features) ·
[Player Support](../player-support) ·
[Network Display](../network-display) ·
[Live Display Controls](../live-display-controls) ·
[Moods & Backgrounds](../moods-and-backgrounds) ·
[Troubleshooting](../troubleshooting) ·
[Changelog](../changelog)
