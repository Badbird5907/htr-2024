import postgres from "postgres";

import { env } from "@/env";
import { drizzle } from "drizzle-orm/postgres-js";
import { numeric, pgTable, serial, timestamp, uuid } from "drizzle-orm/pg-core";

/**
 * Cache the database connection in development. This avoids creating a new connection on every HMR
 * update.
 */
const globalForDb = globalThis as unknown as {
  conn2: postgres.Sql | undefined;
};

const tsConn = globalForDb.conn2 ?? postgres(env.TIMESCALE_URL);
if (env.NODE_ENV !== "production") globalForDb.conn2 = tsConn;


export const tsDb = tsConn;
