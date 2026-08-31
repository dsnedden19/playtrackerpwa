const DB_NAME = "playtracker_.db";
const DB_VERSION = 4;
const STORE_NAME = "games";
const PLAY_STATS_STORE_NAME = "play_stats";

let dbInstance = null;

function openDB() {
    if (dbInstance) return Promise.resolve(dbInstance);

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
request.onupgradeneeded = (event) => {
    const db = event.target.result;
    const upgradeTransaction = event.target.transaction;

    if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: "id" });
        store.createIndex("synced", "synced", { unique: false });
    }

    let playStatsStore;

    if (!db.objectStoreNames.contains(PLAY_STATS_STORE_NAME)) {
        playStatsStore = db.createObjectStore(
            PLAY_STATS_STORE_NAME,
            { keyPath: "id" }
        );
    } else {
        playStatsStore = upgradeTransaction.objectStore(
            PLAY_STATS_STORE_NAME
        );
    }

    if (!playStatsStore.indexNames.contains("gameId")) {
        playStatsStore.createIndex(
            "gameId",
            "gameId",
            { unique: false }
        );
    }

    if (!playStatsStore.indexNames.contains("gameCategoryPlay")) {
        playStatsStore.createIndex(
            "gameCategoryPlay",
            ["gameId", "category", "play"],
            { unique: true }
        );
    }

    if (!playStatsStore.indexNames.contains("synced")) {
        playStatsStore.createIndex(
            "synced",
            "synced",
            { unique: false }
        );
    }
};
        request.onsuccess = (event) => {
            dbInstance = event.target.result;
            resolve(dbInstance);
        };


        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}

async function saveGame(gameData) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, "readwrite");
        const store = tx.objectStore(STORE_NAME);

        const record = {
            id: gameData.id || crypto.randomUUID(),
            ...gameData,
            synced: false,
            updatedAt: Date.now()
        };

        const request = store.put(record);
        request.onsuccess = () => resolve(record);
        request.onerror = (event) => reject(event.target.error);
    });
}

async function loadGame(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, "readonly");
        const store = tx.objectStore(STORE_NAME);
        const request = store.get(id);

        request.onsuccess = () => resolve(request.result || null);
        request.onerror = (event) => reject(event.target.error);
    });
}

async function loadAllGames() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, "readonly");
        const store = tx.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = (event) => reject(event.target.error);
    });
}

async function clearGame(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, "readwrite");
        const store = tx.objectStore(STORE_NAME);
        const request = store.delete(id);

        request.onsuccess = () => resolve();
        request.onerror = (event) => reject(event.target.error);
    });
}
function createPlayStatsId(gameId, category, play) {
    return `${gameId}|${category}|${play}`;
}
async function incrementPlayStat(gameId, category, play, counter) {
    const db = await openDB();
    const id = createPlayStatsId(gameId, category, play);

    return new Promise((resolve, reject) => {
        const tx = db.transaction(PLAY_STATS_STORE_NAME, "readwrite");
        const store = tx.objectStore(PLAY_STATS_STORE_NAME);
        const request = store.get(id);

        request.onsuccess = () => {
            const record = request.result || {
                id: id,
                gameId: gameId,
                category: category,
                play: play,
                counters: {},
                synced: false,
                updatedAt: Date.now()
            };

            record.counters[counter] =
                (record.counters[counter] || 0) + 1;

            record.synced = false;
            record.updatedAt = Date.now();

            const saveRequest = store.put(record);

            saveRequest.onsuccess = () => resolve(record);
            saveRequest.onerror = event => reject(event.target.error);
        };

        request.onerror = event => reject(event.target.error);
    });
}
async function loadPlayStats(gameId, category, play) {
    const db = await openDB();
    const id = createPlayStatsId(gameId, category, play);

    return new Promise((resolve, reject) => {
        const tx = db.transaction(PLAY_STATS_STORE_NAME, "readonly");
        const store = tx.objectStore(PLAY_STATS_STORE_NAME);
        const request = store.get(id);

        request.onsuccess = () => {
            resolve(request.result || null);
        };

        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}
async function loadGamePlayStats(gameId) {
    const db = await openDB();

    return new Promise((resolve, reject) => {
        const tx = db.transaction(PLAY_STATS_STORE_NAME, "readonly");
        const store = tx.objectStore(PLAY_STATS_STORE_NAME);
        const index = store.index("gameId");
        const request = index.getAll(gameId);

        request.onsuccess = () => resolve(request.result);
        request.onerror = event => reject(event.target.error);
    });
}
async function buildGameUploadPayload(gameId) {
    const game = await loadGame(gameId);

    if (!game) {
        throw new Error("Game not found: " + gameId);
    }

    const playStats = await loadGamePlayStats(gameId);

    return {
        game: game,
        playStats: playStats,
        uploadedAt: new Date().toISOString()
    };
}
