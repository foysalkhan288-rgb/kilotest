# Multiplayer Temple Run — Offline P2P 3D Game

## Goal
A mobile-first 3D temple-run style racing game where one player hosts via local hotspot and others join offline. First player to reach the end point wins. Includes trap/bomb/punch/push/slide/throw power-ups, per-device accounts with a store, and real-time local leaderboards.

---

## Tech Stack
- **Rendering**: Three.js (ES modules) with Flat shading and LOD for mobile performance.
- **Network**: PeerJS built on WebRTC (peer-to-peer, low-latency). Host is game authority. No backend.
- **Local Database**: IndexedDB via `idb` wrapper (accounts, inventory, leaderboard, currencies).
- **Controls**: Touch joystick (left side) + action buttons (right side). Swipe gestures for slide.
- **Build/Packaging**: Vite (fast HMR), PWA with Service Worker for offline caching.

---

## Asset Sources (Open Source)
- **Models/Tiles**: BlenderKit / Poly Haven / Kenney Assets (search `Kenney temple` or `low poly ruin`).
- **Animations**: Mixamo for runner idle/run/jump/slide (retarget to Three.js skeleton).
- **Textures**: `cc0textures.com` / `ambientcg.com` for PBR textures.

---

## Game Mechanics
- **Course**: Linear temple corridor (3-8 lanes) with randomized obstacles (walls, pits, traps).
- **Runners**: Third-person, automatic forward pace. User lanes left/right and jumps/pushes.
- **Items**: Equipped before run or collected mid-run:
  - Bomb: Area-of-effect stun
  - Push: Direct knockback 1 lane
  - Punch: Melee stun (close range)
  - Slide: Skip low obstacle
  - Trap: Leave behind, slows others
  - Throw: Projectile stun
- **Win condition**: First to cross finish line.

---

## Multiplayer Architecture (Offline / Hotspot)
1. **Host**:
   - Generates a Game Code (short string).
   - Hosts PeerJS server (in-browser signaling emulation required).
   - Acts as **authoritative server**: runs physics, collision, power-up logic.
   - Broadcasts state snapshots at 20Hz.
2. **Client**:
   - Sends input vector (left/right/jump/slide/action) to host.
   - Renders predicted local state; corrects on server reconciliation.
3. **Discovery in offline mode**:
   - Use the Game Code + local LAN IP for direct WebRTC connection.
   - Client scans common ports on the local subnet for a PeerJS broker or use a manual IP entry dialog.

---

## Account & Store (Per-Device)
- **Storage**: IndexedDB stores:
  - `players` (id, username, avatar, currency)
  - `inventory` (itemId, quantity, equippedSlot)
  - `leaderboard` (raceId, position, timestamp, deviceId hash)
  - `currencies` (coins, gems, sourceTransactionId)
- **Store**: Purchases with fake currency earned through races. No internet validation required.
- **Sync**: Offline-first. Optional peer-to-peer leaderboard exchange with host at session end.
- **Anti-cheat** (client-side only, accept limitation):
  - Sanity checks for impossible speeds/positions on the host authority.
  - Tamper-free assertions: host never trusts client for time/position.

---

## Controls (Mobile)
- **Left zone**: Touch-move joystick (virtual analog stick).
- **Right zone**: Tap action buttons (Bomb/Push/Punch/Slide/Trap/Throw).
- **Swipe up**: Jump. Swipe down: Slide.
- **Esc key / menu button**: Pause.

---

## UI Framework
- Pure Three.js scene + HTML/CSS overlay (HUD: health, timer, minimap, store).
- TailwindCSS via CDN for HUD styling (or plain CSS for offline resilience).

---

## Directory Structure
```
temple-run-multiplayer/
├── public/
│   ├── assets/              # 3D models, textures (downloaded)
│   └── manifest.json
├── src/
│   ├── core/
│   │   ├── game.js          # Main game loop, state machine
│   │   ├── scene.js         # Three.js setup, lighting, camera
│   │   └── loader.js        # Asset loading manager
│   ├── network/
│   │   ├── peer.js          # PeerJS host/join logic
│   │   ├── protocol.js      # Message types (input, state, event)
│   │   └── host.js          # Authoritative game tick
│   ├── player/
│   │   ├── runner.js        # Player character controller
│   │   ├── inventory.js     # Items selection
│   │   └── abbotities.js    # Power-up activation
│   ├── store/
│   │   ├── db.js            # IndexedDB wrapper
│   │   ├── account.js       # Player profile logic
│   │   └── shop.js          # Store UI and purchase
│   ├── ui/
│   │   ├── hud.js           # HUD, menus, store overlay
│   │   └── controls.js      # Touch/UI input binding
│   ├── level/
│   │   ├── generator.js     # Procedural corridor generation
│   │   ├── obstacles.js     # Walls, pits, triggers
│   │   └── effects.js       # Particles, explosions
│   ├── main.js
│   └── style.css
├── index.html
├── vite.config.js
├── package.json
└── plan.md
```

---

## Data Flow
1. **Pre-game**: Account load → Shop → Item equip → Game lobby.
2. **Lobby**: Host creates room, clients join. Host loads level, sends initial state.
3. **In-game** (20Hz tick):
   - Clients → Host: `{input: {x, jump, action}, timestamp}`.
   - Host → Clients: `{players: [...], obstacles: [...], effects: [...]}`.
4. **Post-game**: Client requests sync → Host confirms results → Leaderboard update + currency award.

---

## Risk & Limitation Mitigation
- **Offline discovery**: Require users to enter the host's local IP manually. Use zero-conf mDNS if supported.
- **Host cheating**: Game-loop is state server, can log inputs. Local play, trust friends.
- **Performance**: Keep draw calls < 300 with instancing; use baked lighting and vertex colors.
- **Cross-device sync**: Manual conflict resolution or last-write-wins for local-only leaderboard.

---

## Milestones & Validation
1. **M1**: Three.js empty temple corridor with one runner & mobile joystick.
2. **M2**: Host/join lobby and sending player positions over WebRTC.
3. **M3**: Authoritative host tick, sync, and collision.
4. **M4**: Power-ups (all 6 items) + local animation.
5. **M5**: IndexedDB account, shop, currency, leaderboard.
6. **M6**: Polish, asset replacement, touch optimizations, PWA packaging.

---

## Open Questions to Resolve Before Implementation
1. **P2P Signaling Offline**: PeerJS requires a broker for initial connection. For true offline internet-free setup, should we bundle a tiny Node.js signaling server the host runs alongside the game, or restrict to manual IP/port entry over WebRTC directly?
2. **Asset Licensing**: Which specific Kenney/Poly Haven packs to use?
3. **Frame Budget**: Target 30fps or 60fps on mid-range mobile?
