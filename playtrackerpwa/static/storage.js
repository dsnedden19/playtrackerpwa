const DB_NAME = "playtracker.db";
const DB_VERSION = 5;
const GAME_STORE = "games";
const EVENT_STORE = "events";

const defaultConfiguration = [
    { name: "Offense", type: "offense", plays: ["5 Out", "Transition", "Pick and Roll"], stats: ["Made Shot", "Missed Shot", "Turnover", "Foul"] },
    { name: "Defense", type: "defense", plays: ["Man", "2-3 Zone", "Transition Defense"], stats: ["Stop", "Defensive Rebound", "Steal", "Foul"] }
];

let dbInstance = null;

function openDB() {
    if (dbInstance) return Promise.resolve(dbInstance);
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = event => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(GAME_STORE)) db.createObjectStore(GAME_STORE, { keyPath: "id" });
            if (!db.objectStoreNames.contains(EVENT_STORE)) {
                const store = db.createObjectStore(EVENT_STORE, { keyPath: "id" });
                store.createIndex("gameId", "gameId", { unique: false });
            }
        };
        request.onsuccess = event => { dbInstance = event.target.result; resolve(dbInstance); };
        request.onerror = event => reject(event.target.error);
    });
}

async function saveGame(gameData) {
    const db = await openDB();
    const record = { id: gameData.id || crypto.randomUUID(), ...gameData, updatedAt: Date.now() };
    return new Promise((resolve, reject) => {
        const request = db.transaction(GAME_STORE, "readwrite").objectStore(GAME_STORE).put(record);
        request.onsuccess = () => resolve(record);
        request.onerror = event => reject(event.target.error);
    });
}

async function loadGame(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const request = db.transaction(GAME_STORE, "readonly").objectStore(GAME_STORE).get(id);
        request.onsuccess = () => resolve(request.result || null);
        request.onerror = event => reject(event.target.error);
    });
}

async function loadAllGames() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const request = db.transaction(GAME_STORE, "readonly").objectStore(GAME_STORE).getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = event => reject(event.target.error);
    });
}

async function loadGameEvents(gameId) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const request = db.transaction(EVENT_STORE, "readonly").objectStore(EVENT_STORE).index("gameId").getAll(gameId);
        request.onsuccess = () => resolve(request.result.sort((a, b) => a.eventNumber - b.eventNumber));
        request.onerror = event => reject(event.target.error);
    });
}

async function addGameEvent(gameId, eventData) {
    const events = await loadGameEvents(gameId);
    const record = { id: crypto.randomUUID(), gameId, eventNumber: events.length + 1, recordedAt: new Date().toISOString(), ...eventData };
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const request = db.transaction(EVENT_STORE, "readwrite").objectStore(EVENT_STORE).add(record);
        request.onsuccess = () => resolve(record);
        request.onerror = event => reject(event.target.error);
    });
}

async function buildGameUploadPayload(gameId) {
    const game = await loadGame(gameId);
    if (!game) throw new Error("Game not found: " + gameId);
    return { game, events: await loadGameEvents(gameId), uploadedAt: new Date().toISOString() };
}
