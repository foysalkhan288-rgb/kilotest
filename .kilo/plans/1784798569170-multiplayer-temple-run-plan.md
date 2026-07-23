# Multiplayer Temple Run — Offline Local-Host 3D Game

## Goal
Mobile-first 3D temple-run racing game hosted on a local hotspot. 1 host, multiple clients join over LAN. First to reach the finish line wins. Includes bomb/punch/push/slide/trap/throw power-ups, per-device accounts with a store, and local real-time leaderboard.

---

## Tech Stack & Constraints
- **App format**: Single Android APK.
- **Host runtime**: Native Kotlin Android app.
- **Server**: Lightweight embedded HTTP + WebSocket server (e.g., `NanoHTTPD` or `KoHttp`) running inside the host app. Serves static game files and authoritative state.
- **Game client**: Three.js (ES modules) running inside an in-app `WebView` (host) and standalone browser (clients) over `http(s)://<host-ip>:8080`.
- **Network**: **Plain WebSocket** over local hotspot. No external broker, fully offline.
- **Local Database**: IndexedDB via `idb` wrapper in the WebView client (accounts, inventory, currencies, leaderboard).
- **Build**: Vite for build tooling; APK packaging done separately by an implementation agent.

---

## Asset Plan
Implementation agent must source free/open-source assets before building:
- **Models/Tiles**: Kenney `low-poly-temple-pack` (CC0) or equivalent temple geometry.
- **Textures**: ambientCG CC0 pack (e.g., `Rock_04`).
- **Animations**: Mixamo Free, retargeted to simple rig; baked to glTF/FBX.

---

## Game Mechanics
- **Course**: Linear 3–8 lane temple corridor, ~90s run. Random obstacle seeds but deterministic per room.
- **Win condition**: First runner whose `z` crosses `finishZ`.
- **Power-ups** (equipped pre-run from store):
  - Bomb: AoE stun (2-lane radius, 1.5s)
  - Push: 1-lane knockback
  - Punch: Melee stun, 1-lane range
  - Slide: Immune to low obstacles for 2s
  - Trap: Place behind, 2s slow+stun trigger
  - Throw: Projectile stun (3-lane range, 0.5s)

---

## Host / Client Architecture
1. **Host app**:
   - Starts hotspot.
   - Starts embedded `http + ws` server on `0.0.0.0:8080`.
   - Logs local IP + port + Room Code.
   - Runs authoritative game tick at **50Hz** (`setInterval` inside Kotlin coroutine/`ScheduledExecutorService`).
   - Broadcasts JSON state snapshots at **20Hz**.
   - Game UI: in-app `WebView` pointing to `localhost:8080`.
2. **Client app/browser**:
   - Opens `http://<host-ip>:8080`.
   - Connects via `new WebSocket(hostUrl)`.
   - Sends input vector each rendered frame.
   - Renders received `state` payload with interpolation.

---

## Network Protocol
- **Client → Host**: `{type:"input", seq, x, jump, action, timestamp}`
- **Host → Client**: `{type:"state", players:[{id,x,z,lane,stunUntil,alive}], obstacles:[], effects:[]}`
- **Host → Client**: `{type:"start", seed, spawnLanes:[...]}`
- **Host → Client**: `{type:"result", finishOrder:[{id, username, time}]}`
- **Host → Client**: `{type:"error", message}`

---

## Account & Store (Per-Device / IndexedDB)
- **Stores**:
  - `players`: `{id, username, deviceIdHash, totalCoins, createdAt}`
  - `inventory`: `{id, deviceIdHash, itemId, quantity, equipped}`
  - `leaderboard`: `{raceId, finishOrder:[{deviceIdHash, username, time}], createdAt}`
  - `versions`: schema version.
- **Store prices**: Bomb=100, Push=80, Punch=120, Slide=60, Trap=90, Throw=110 (in-game coins).
- **Earning**: 1st place +50c, 2nd +30c, 3rd +15c. Daily bonus +20c (24h gate).

---

## Mobile Controls
- **Left 35%**: Touch joystick (lane movement).
- **Right 65%**: Action buttons (Bomb, Push, Punch, Slide, Trap, Throw).
- **Swipe up**: Jump. **Swipe down**: Slide.

---

## UI Layout
- Three.js canvas full-screen inside WebView.
- HTML/CSS overlay (absolute divs) for:
  - HUD: rank, timer, minimap.
  - Lobby: host/join inputs.
  - Store: item grid, purchase/equip.
  - Results: finish order, coins earned.

---

## Directory Structure (Source)
```
temple-run-multiplayer/
├── android/
│   └── src/main/
│       ├── java/.../HostServer.kt        # Embedded HTTP + WS server
│       └── res/...                        # Android resources
├── public/
│   ├── assets/                            # Pre-downloaded models, textures
│   └── sw.js                              # PWA service worker
├── server/
│   └── host-server.js                     # Authoritative tick logic (shared with WebView eval)
├── src/
│   ├── main.js                            # WebView client entry
│   ├── game.js                            # Game state machine
│   ├── scene.js
│   ├── controls.js                        # Touch input binding
│   ├── network/
│   │   ├── client.js                      # WebSocket client
│   │   └── protocol.js
│   ├── entities/
│   │   ├── runner.js
│   │   ├── obstacle.js
│   │   └── projectile.js
│   ├── store/
│   │   ├── db.js
│   │   ├── account.js
│   │   └── shop.js
│   └── style.css
├── index.html
├── vite.config.js
└── package.json
```

---

## Data Flow
1. **Lobby**: Host starts app, hotspot + server begin, prints `ws://<host-ip>:8080`. Clients enter same URL.
2. **Countdown**: Host sends `start` with seed + spawn lanes.
3. **Race**: Clients input → Host authoritative tick → state broadcast → client interpolation.
4. **Finish**: Host emits `result` event. Client shows results, awards coins, writes to IndexedDB.

---

## Failure Modes
- **Host disconnect**: Race ends immediately; partial results written.
- **Client lag**: Host drops packets with `seq` > 2 ticks behind. Clients interpolate.
- **Lobby cap**: 8 players max to keep bandwidth < 64kbps/client.
- **Hotspot DHCP churn**: Host UI shows current IP; clients may need manual refresh.

---

## Milestones
1. **M1**: Host Kotlin app with embedded `ws` server; serves static site. Host/join UI.
2. **M2**: Three.js temple corridor, one runner, touch joystick, camera follow.
3. **M3**: Authoritative host tick, state broadcast, 2+ clients rendering positions.
4. **M4**: Obstacles + all 6 power-ups with collision resolution.
5. **M5**: IndexedDB account, shop, leaderboard, results screen.
6. **M6**: Proc-gen corridor, PWA, performance polish, APK final pack.
