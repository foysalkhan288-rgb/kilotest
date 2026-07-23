# Multiplayer Temple Run — Offline Local IP 3D Game

## Goal
Mobile-first 3D temple-run racing game hosted on a local hotspot. 1 host, multiple clients join over LAN. First to reach the finish line wins. Includes bomb/punch/push/slide/trap/throw power-ups, per-device accounts with a store, and local real-time leaderboard.

---

## Fixed Stack Decisions
- **Rendering**: Three.js (ES modules), flat shading, instanced meshes, ≤300 draw calls, baked lighting where possible. 30fps floor on mid-range mobile.
- **Runtimes**: Host = browser-only Node.js + `ws` server; Clients = browser-only, no server install needed for joiners.
- **Network**: Native `ws` server (host) + browser `WebSocket` (clients) over local hotspot IP. No signaling broker, fully offline.
- **Local Database**: IndexedDB via `idb` wrapper for accounts, inventory, currencies, and leaderboard (all per-device).
- **Build**: Vite; bundled as a PWA with Service Worker for offline asset caching.
- **Controls**: Left touch joystick (lane/jump input), right action buttons (Bomb/Push/Punch/Slide/Trap/Throw), swipe up jump, swipe down slide.

---

## Host Server (Node.js + ws)
- Spins up `http` (serves static PWA files) + `ws` on a configurable port (default `8080`).
- Prints local IP + port + short Room Code on startup.
- **Game loop**: `setInterval` at 50Hz (20ms). Authoritative physics + collision + power-up resolution.
- **State broadcast**: JSON delta snapshots at 20Hz to all connected clients.
- **Protocol**:
  - Client → Host: `{type:"input", seq, x, jump, action, timestamp}`
  - Host → Client: `{type:"state", players:[{id,x,z,lane,stunUntil,alive}], obstacles:[], effects:[]}`
  - Host → Client: `{type:"result", finishOrder:[id,id,id]}` on race end.

---

## Client (Browser)
- Connects via `new WebSocket(hostUrl)`.
- Sends input vector each tick.
- Renders received `state` payload with interpolation (render at 30fps, network 50Hz).
- Handles touch joystick and action buttons.

---

## Game Mechanics
- **Course**: Linear 3–8 lane temple corridor, ~90s run. Random obstacle seeds but same per room.
- **Win**: First `z >= finishZ`.
- **Power-ups** (equipped pre-run from store):
  - Bomb: AoE stun (2 lane radius, 1.5s)
  - Push: 1-lane knockback to target
  - Punch: Melee stun, 1 lane range
  - Slide: Immune to low obstacles for 2s
  - Trap: Place behind, 2s slow+stun trigger
  - Throw: Projectile stun (travel 3 lanes, 0.5s)

---

## Account & Store (Per-Device / IndexedDB)
- `players` store: `{id, username, deviceIdHash, totalCoins, createdAt}`
- `inventory` store: `{id, deviceIdHash, itemId, quantity, equipped}`
- `leaderboard` store: `{raceId, finishOrder:[{deviceIdHash,username,time}], createdAt}`
- `versions` store: `dbVersion`.
- **Store prices**: Bomb=100, Push=80, Punch=120, Slide=60, Trap=90, Throw=110 (in-game coins).
- **Earning**: 1st place +50c, 2nd +30c, 3rd +15c. Daily bonus = +20c (24h gate).

---

## UI Layout
- Three.js canvas full-screen.
- CSS overlay (absolute divs, plain CSS, no CDN): HUD (lap, rank, timer), lobby (host/join inputs), store (grid of items), results.
- Mobile touch zones: left 35% = joystick, right 65% = action buttons. Tap on action icons triggers power-up with debounce / cooldown.

---

## Asset Sources (Pre-downloaded by impl agent)
- Temple geometry/tiles: Kenney `low-poly-temple-pack` (CC0).
- Textures: ambientCG `Rock_04_1K-JPG` or similar CC0.
- Animations: Mixamo Free (Idle/Run/Jump/Slide) — retargeted to simple rig; baked into FBX or glTF.

---

## Directory Structure
```
temple-run-multiplayer/
├── server.js              # ws + http host
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.js            # entry
│   ├── game.js            # Game state machine (lobby, countdown, race, result)
│   ├── scene.js
│   ├── controls.js        # touch input
│   ├── network/
│   │   ├── client.js      # WebSocket client
│   │   └── protocol.js    # message types
│   ├── entities/
│   │   ├── runner.js
│   │   ├── obstacle.js
│   │   └── projectile.js
│   ├── store/
│   │   ├── db.js
│   │   ├── account.js
│   │   └── shop.js
│   └── style.css
└── public/
    ├── assets/            # pre-downloaded models + textures
    └── sw.js              # PWA service worker
```

---

## Data Flow
1. **Lobby**: Host starts `server.js`, opens `localhost:8080`. Clients enter `http://<host-ip>:8080`. Enter name → join room.
2. **Countdown**: Host sends `start` with obstacle seed + player spawn lanes.
3. **In-race**:
   - Client sends input at each rendered frame.
   - Host processes 50Hz tick → broadcasts state at 20Hz.
   - Clients render interpolated state.
4. **Finish**: Host emits `finish` event with ordered finish array. Client shows results, awards coins, writes to IndexedDB.

---

## Milestones
1. **M1**: `server.js`, static asset serving, client `wss://` connect + host/join UI.
2. **M2**: Three.js temple corridor, one runner, touch joystick, movement, camera follow.
3. **M3**: Authoritative host tick, state broadcast, 2+ clients showing positions.
4. **M4**: Obstacles + all 6 power-ups with collision resolution.
5. **M5**: IndexedDB account, shop, leaderboard, results screen.
6. **M6**: Proc-gen corridor, polish, PWA packaging, input dead-zone tuning.

---

## Failure Modes
- **Host disconnects**: Race ends immediately, partial results written.
- **Client lag**: Host drops packet if `seq` falls behind 2 ticks; client smooths via interpolation.
- **Large lobby**: Cap at 8 players to keep bandwidth < 64kbps/client.
- **Hotspot DHCP churn**: Host shows current IP; clients refresh if connection drops.
