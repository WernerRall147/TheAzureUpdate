"use strict";

const { app } = require("@azure/functions");
const { TableClient } = require("@azure/data-tables");

// --- Configuration -------------------------------------------------------
// Connection string for the Azure Storage account that holds the view
// counts. Set VIEWS_TABLES_CONNECTION in the Static Web App configuration
// (falls back to AzureWebJobsStorage, which SWA also provides).
const CONNECTION =
  process.env.VIEWS_TABLES_CONNECTION || process.env.AzureWebJobsStorage;
const TABLE_NAME = process.env.VIEWS_TABLE_NAME || "postViews";
const PARTITION = "post";

// Post ids are used as Table row keys. Keep them to a safe character set so
// a bad id can never break a Table Storage request.
function safeId(raw) {
  return String(raw == null ? "" : raw)
    .trim()
    .slice(0, 256)
    .replace(/[\\/#?\t\n\r]/g, "-");
}

let tablePromise = null;
async function getTable() {
  if (!CONNECTION) {
    throw new Error("No storage connection string configured (VIEWS_TABLES_CONNECTION).");
  }
  if (!tablePromise) {
    const client = TableClient.fromConnectionString(CONNECTION, TABLE_NAME, {
      allowInsecureConnection: /devstoreaccount1|127\.0\.0\.1|UseDevelopmentStorage/i.test(CONNECTION)
    });
    tablePromise = client.createTable().then(() => client).catch(() => client);
  }
  return tablePromise;
}

async function readCount(table, id) {
  try {
    const entity = await table.getEntity(PARTITION, id);
    return Number(entity.count) || 0;
  } catch (err) {
    if (err.statusCode === 404) return 0;
    throw err;
  }
}

// Increment with optimistic concurrency: retry a few times if another
// request updated the same row between our read and write.
async function incrementCount(table, id) {
  for (let attempt = 0; attempt < 5; attempt++) {
    let entity;
    try {
      entity = await table.getEntity(PARTITION, id);
    } catch (err) {
      if (err.statusCode !== 404) throw err;
      entity = null;
    }

    if (!entity) {
      try {
        await table.createEntity({ partitionKey: PARTITION, rowKey: id, count: 1 });
        return 1;
      } catch (err) {
        if (err.statusCode === 409) continue; // created concurrently, retry as update
        throw err;
      }
    }

    const next = (Number(entity.count) || 0) + 1;
    try {
      await table.updateEntity(
        { partitionKey: PARTITION, rowKey: id, count: next },
        "Replace",
        { etag: entity.etag }
      );
      return next;
    } catch (err) {
      if (err.statusCode === 412) continue; // etag mismatch, retry
      throw err;
    }
  }
  // Fallback: return best-effort current value without another write.
  return readCount(table, id);
}

async function readAll(table) {
  const counts = {};
  const entities = table.listEntities({
    queryOptions: { filter: `PartitionKey eq '${PARTITION}'` }
  });
  for await (const entity of entities) {
    counts[entity.rowKey] = Number(entity.count) || 0;
  }
  return counts;
}

// GET  /api/views            -> { counts: { <id>: <n>, ... } }
// GET  /api/views?post=<id>  -> { id, count }
// POST /api/views { post }   -> { id, count }  (increments)
app.http("views", {
  methods: ["GET", "POST"],
  authLevel: "anonymous",
  route: "views",
  handler: async (request, context) => {
    let table;
    try {
      table = await getTable();
    } catch (err) {
      context.error("Storage not configured:", err.message);
      return { status: 503, jsonBody: { error: "View tracking is not configured." } };
    }

    try {
      if (request.method === "POST") {
        let body = {};
        try {
          body = await request.json();
        } catch {
          body = {};
        }
        const id = safeId(body.post || request.query.get("post"));
        if (!id) return { status: 400, jsonBody: { error: "Missing 'post' id." } };
        const count = await incrementCount(table, id);
        return { status: 200, jsonBody: { id, count } };
      }

      const postParam = request.query.get("post");
      if (postParam) {
        const id = safeId(postParam);
        const count = await readCount(table, id);
        return { status: 200, jsonBody: { id, count } };
      }

      const counts = await readAll(table);
      return { status: 200, jsonBody: { counts } };
    } catch (err) {
      context.error("views handler failed:", err);
      return { status: 500, jsonBody: { error: "Failed to process view request." } };
    }
  }
});
