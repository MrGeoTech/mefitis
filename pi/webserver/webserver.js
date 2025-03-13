import { serve } from "https://deno.land/std@0.214.0/http/server.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";
import { format } from "https://deno.land/std@0.210.0/datetime/mod.ts";

const db = new DB("../data.db");
db.execute(`CREATE TABLE IF NOT EXISTS data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Sound_Engine REAL,
    Sound_Operator REAL,
    Emissions_Engine REAL,
    Emissions_Operator REAL,
    Temp_Engine REAL,
    Temp_Exhaust REAL,
    RPM INTEGER
)`);
let recordingEndIndex = null;

const clients = new Set();

async function handler(req) {
    const url = new URL(req.url);
    
    if (url.pathname === "/") {
        return new Response(await Deno.readFile("index.html"), {
            headers: { "Content-Type": "text/html" }
        });
    } else if (url.pathname === "/scripts.js") {
        return new Response(await Deno.readFile("scripts.js"), {
            headers: { "Content-Type": "application/javascript" }
        });
    } else if (url.pathname === "/ws") {
        const { socket, response } = Deno.upgradeWebSocket(req);
        socket.onopen = () => clients.add(socket);
        socket.onmessage = (event) => handleWebSocketMessage(socket, event.data);
        socket.onclose = () => clients.delete(socket);
        socket.onerror = (err) => console.error("WebSocket error:", err);
        return response;
    }
    
    return new Response("Not Found", { status: 404 });
}

function handleWebSocketMessage(socket, message) {
    try {
        const data = JSON.parse(message);
        if (data.type === "record") {
            handleRecording(socket, data.action, data.duration);
        }
    } catch (error) {
        console.error("Invalid WebSocket message:", error);
    }
}

function broadcastDataUpdate() {
    const latestData = db.query("SELECT * FROM data ORDER BY id DESC LIMIT 60").reverse();
    broadcast({ type: "data_update", data: latestData, last_index: latestData.length ? latestData[0][0] : null });
}

function broadcast(json) {
    for (const client of clients) {
        client.send(JSON.stringify(json));
    }
}

function handleRecording(socket, action, duration) {
    if (action === "start") {
        if (recordingEndIndex !== null) {
            socket.send(JSON.stringify({ type: "record_status", message: "Already recording." }));
            return;
        }
        const latestIndex = db.query("SELECT MAX(id) FROM data")[0][0] || 0;
        recordingEndIndex = latestIndex + duration;
        console.log(`Recording started. Will stop at id = ${recordingEndIndex}`);
        setTimeout(() => stopRecording(socket, latestIndex), duration * 1000);
        broadcast({ type: "record_start" });
    } else if (action === "stop") {
        stopRecording(socket, recordingEndIndex);
    }
}

async function stopRecording(socket, startIndex) {
    if (recordingEndIndex === null) {
        socket.send(JSON.stringify({ type: "record_status", message: "No active recording." }));
        return;
    }
    const data = db.query("SELECT * FROM data WHERE id >= ? AND id <= ?", [startIndex, recordingEndIndex]);
    const csvContent = [
        "Sound_Engine,Sound_Operator,Emissions_Engine,Emissions_Operator,Temp_Engine,Temp_Exhaust,RPM",
        ...data.map(row => row.join(","))
    ].join("\n");
    
    const timestamp = format(new Date(), "yyyy-MM-dd_HH-mm-ss");
    const filename = `Recording-${timestamp}.csv`;
    await Deno.writeTextFile(filename, csvContent);
    console.log(`Recording saved to ${filename}`);
    recordingEndIndex = null;
    broadcast({ type: "record_stop" });
}

setInterval(broadcastDataUpdate, 1000);

serve(handler, { port: 8080 });
