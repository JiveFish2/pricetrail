import postgres from "postgres";

// One connection pool per server instance. Local Postgres has no TLS; hosted
// databases (Neon) require it.
const url = process.env.DATABASE_URL;
if (!url) throw new Error("DATABASE_URL is not set");

export const sql = postgres(url, {
  ssl: /localhost|127\.0\.0\.1/.test(url) ? false : "require",
  max: 5,
  idle_timeout: 20,
  // Keep numeric columns as strings; prices are formatted, never summed, in the UI.
});
