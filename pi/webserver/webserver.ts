import { serve } from "https://deno.land/std@0.214.0/http/server.ts";
import { Client } from "https://deno.land/x/postgres@v0.17.0/mod.ts";
import { format } from "https://deno.land/std@0.210.0/datetime/mod.ts";

// PostgreSQL Database Configuration
const DB_CONFIG = {
  database: "data",
  user: "postgres",
  password: "postgres",
  hostname: "localhost",
  port: 5432,
};

// Create PostgreSQL client
const client = new Client(DB_CONFIG);
await client.connect();

// Initialize database and create table if it doesn't exist
async function initDb() {
  await client.queryObject(`
    CREATE TABLE IF NOT EXISTS data (
      id SERIAL PRIMARY KEY,
      Sound_Engine REAL,
      Sound_Operator REAL,
      Emissions_Engine REAL,
      Emissions_Operator REAL,
      Temp_Engine REAL,
      Temp_Exhaust REAL,
      RPM INTEGER
    )
  `);
}

await initDb();

let recordingEndIndex: number | null = null;
const clients = new Set<WebSocket>();

async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);

  if (url.pathname === "/") {
    return new Response(await Deno.readFile("index.html"), {
      headers: { "Content-Type": "text/html" },
    });
  } else if (url.pathname === "/scripts.js") {
    return new Response(await Deno.readFile("scripts.js"), {
      headers: { "Content-Type": "application/javascript" },
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

async function handleWebSocketMessage(socket: WebSocket, message: string) {
  try {
    const data = JSON.parse(message);
    if (data.type === "record") {
      await handleRecording(socket, data.action, data.duration);
    }
  } catch (error) {
    console.error("Invalid WebSocket message:", error);
  }
}

async function broadcastDataUpdate() {
  try {
    const result = await client.queryObject("SELECT * FROM data ORDER BY id DESC LIMIT 60");

    // Transform rows to an array of arrays, excluding `id`
    const latestData = result.rows.map((row) => [
      parseFloat(row.sound_engine),
      parseFloat(row.sound_operator),
      parseFloat(row.emissions_engine),
      parseFloat(row.emissions_operator),
      parseFloat(row.temp_engine),
      parseFloat(row.temp_exhaust),
      parseInt(row.rpm, 10),
    ]).reverse(); // Reverse to maintain chronological order

    broadcast({
      type: "data_update",
      data: latestData,
      last_index: latestData.length ? latestData[0][0] : null, // Keep tracking index if needed
    });
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

function broadcast(json: object) {
  for (const client of clients) {
    client.send(JSON.stringify(json));
  }
}

async function handleRecording(socket: WebSocket, action: string, duration: number) {
  if (action === "start") {
    if (recordingEndIndex !== null) {
      socket.send(JSON.stringify({ type: "record_status", message: "Already recording." }));
      return;
    }

    const result = await client.queryObject("SELECT MAX(id) FROM data");
    const latestIndex = result.rows[0]?.max || 0;
    recordingEndIndex = latestIndex + duration;
    console.log(`Recording started. Will stop at id = ${recordingEndIndex}`);

    setTimeout(() => stopRecording(socket, latestIndex), duration * 1000);
    broadcast({ type: "record_start" });
  } else if (action === "stop") {
    await stopRecording(socket, recordingEndIndex);
  }
}

async function stopRecording(socket: WebSocket, startIndex: number | null) {
  if (recordingEndIndex === null || startIndex === null) {
    socket.send(JSON.stringify({ type: "record_status", message: "No active recording." }));
    return;
  }

  try {
    const result = await client.queryObject(
      "SELECT * FROM data WHERE id >= $1 AND id <= $2",
      startIndex,
      recordingEndIndex
    );

    const csvContent = [
      "Sound_Engine,Sound_Operator,Emissions_Engine,Emissions_Operator,Temp_Engine,Temp_Exhaust,RPM",
      ...result.rows.map((row) => Object.values(row).join(",")),
    ].join("\n");

    const timestamp = format(new Date(), "yyyy-MM-dd_HH-mm-ss");
    const filename = `Recording-${timestamp}.csv`;
    await Deno.writeTextFile(filename, csvContent);
    console.log(`Recording saved to ${filename}`);

    recordingEndIndex = null;
    broadcast({ type: "record_stop" });
  } catch (error) {
    console.error("Error saving recording:", error);
  }
}

setInterval(broadcastDataUpdate, 1000);

serve(handler, { port: 8080 });
