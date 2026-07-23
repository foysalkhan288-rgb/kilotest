# Multiplayer Temple Run — APK Delivery Plan

## 1. Deliverable
Single Android APK. Host and client play over a local hotspot with no internet. Persistent per-device data survives app restarts.

## 2. Architecture

| Layer | Choice | Notes |
|---|---|---|
| Host runtime | Native Kotlin `Activity` | Runs hotspot + embedded server |
| Server | NanoHTTPD + KoHTTP WS inside host app | Listen on `0.0.0.0:8080` |
| Game client | Three.js in in-app `WebView` | Host connects `localhost:8080`; clients connect `http://<host-ip>:8080` |
| Network | Plain WebSocket | 50Hz tick, 20Hz state broadcast |
| Local DB | IndexedDB (`idb` wrapper) | Accounts, inventory, leaderboard, currencies |
| Build frontend | Vite | Outputs to Android `assets/` |
| APK packaging | Android Gradle + Kotlin | Single APK |

## 3. Server Responsibilities (Kotlin)
- Serve static game files from APK `assets/`
- Accept WebSocket connections
- Run authoritative game tick at 50Hz
- Manage lobby, countdown, race, result states
- Validate inputs, resolve collisions, judge finish order
- Broadcast: `{type:"start"}`, `{type:"state", players, obstacles, effects}`, `{type:"result", finishOrder}`

## 4. Client Responsibilities (Three.js / WebView)
- Connect via `new WebSocket(hostUrl)`
- Send `{type:"input", seq, x, jump, action}` per frame
- Render three.js scene + HTML/CSS overlays
- Touch controls: left 35% joystick, right 65% action buttons
- Swipe: up = jump, down = slide

## 5. Protocol
- **Client → Host**: `{type:"input", seq, x, jump, action, timestamp}`
- **Host → Client**: `{type:"state", players:[{id,x,z,lane,stunUntil,alive}], obstacles:[], effects:[]}`
- **Host → Client**: `{type:"start", seed, spawnLanes}`
- **Host → Client**: `{type:"result", finishOrder:[{id, username, time}]}`

## 6. Accounts & Store (IndexedDB)
- `players`: `{id, username, deviceIdHash, totalCoins, createdAt}`
- `inventory`: `{id, deviceIdHash, itemId, quantity, equipped}`
- `leaderboard`: `{raceId, finishOrder, createdAt}`
- Store prices: Bomb=100, Push=80, Punch=120, Slide=60, Trap=90, Throw=110
- Race rewards: 1st=+50c, 2nd=+30c, 3rd=+15c

## 7. Game Design
- **Course**: Linear 3–8 lane temple corridor, ~90s, deterministic obstacle seed per race
- **Win condition**: First to `z >= finishZ`
- **Power-ups**: Bomb (AoE stun), Push (1-lane knockback), Punch (melee stun), Slide (2s low-obstacle immunity), Trap (placed behind, stun+slow), Throw (projectile stun)
- **Cap**: 8 players max

## 8. Assets To Download
Implementer must download before coding:
- **Models**: Kenney `low-poly-temple-pack` (CC0) or equivalent temple geometry
- **Textures**: ambientCG CC0 pack (e.g., `Rock_04`)
- **Animations**: Mixamo Free Idle/Run/Jump/Slide retargeted to simple rig, export glTF

## 9. Mobile Controls
- Left 35%: touch joystick (lane movement)
- Right 65%: action buttons (Bomb/Push/Punch/Slide/Trap/Throw)
- Swipe up: jump, Swipe down: slide

## 10. Failure Modes
- Host disconnect → race ends, partial results saved
- Client lag → host drops packets 2+ ticks behind, client interpolates
- Hotspot DHCP churn → host UI shows current IP, clients refresh if connection drops

## 11. Milestones
1. **M1**: Kotlin app with embedded HTTP+WS server, serve static site, host/join lobby
2. **M2**: Three.js temple corridor, single runner, touch joystick, camera follow
3. **M3**: Host 50Hz tick, 20Hz state broadcast, 2+ clients showing positions
4. **M4**: Obstacles + all 6 power-ups with collision
5. **M5**: IndexedDB accounts, shop, leaderboard, results screen
6. **M6**: Procedural corridor, PWA, performance polish, APK build & signing

## 12. Directory Structure
```
temple-run-multiplayer/
├── android/
│   └── src/main/
│       ├── java/.../HostServer.kt     # Embedded HTTP + WS server
│       └── res/...                    # Android resources
├── public/
│   └── assets/                        # Downloaded game assets
├── server/
│   └── host-server.js                 # Shared authoritative logic (eval'd in Kis)
├── src/
│   ├── main.js
│   ├── game.js
│   ├── scene.js
│   ├── controls.js
│   ├── network/{client.js, protocol.js}
│   ├── entities/{runner.js, obstacle.js, projectile.js}
│   ├── store/{db.js, account.js, shop.js}
│   └── style.css
├── index.html
├── vite.config.js
└── package.json
```

## 13. APK Build Notes
- Host server runs in Kotlin service/activity, not Node.js
- Vite build output zipped into `android/src/main/assets/`
- Permissions: `INTERNET`, `ACCESS_WIFI_STATE`, `ACCESS_NETWORK_STATE`, `CHANGE_WIFI_STATE`
- Target API 33+, min SDK 26
