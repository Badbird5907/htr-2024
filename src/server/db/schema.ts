import { relations, sql } from "drizzle-orm";
import {
  date,
  doublePrecision,
  index,
  integer,
  numeric,
  pgEnum,
  pgTableCreator,
  primaryKey,
  serial,
  text,
  timestamp,
  uuid,
  varchar,
} from "drizzle-orm/pg-core";
import { type AdapterAccount } from "next-auth/adapters";

/**
 * This is an example of how to use the multi-project schema feature of Drizzle ORM. Use the same
 * database instance for multiple projects.
 *
 * @see https://orm.drizzle.team/docs/goodies#multi-project-schema
 */
export const createTable = pgTableCreator((name) => `htr-2024_${name}`);

export const users = createTable("user", {
  id: varchar("id", { length: 255 })
    .notNull()
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 255 }).notNull(),
  emailVerified: timestamp("email_verified", {
    mode: "date",
    withTimezone: true,
  }).default(sql`CURRENT_TIMESTAMP`),
  image: varchar("image", { length: 255 }),
});

export const usersRelations = relations(users, ({ many }) => ({
  accounts: many(accounts),
}));

export const accounts = createTable(
  "account",
  {
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => users.id),
    type: varchar("type", { length: 255 })
      .$type<AdapterAccount["type"]>()
      .notNull(),
    provider: varchar("provider", { length: 255 }).notNull(),
    providerAccountId: varchar("provider_account_id", {
      length: 255,
    }).notNull(),
    refresh_token: text("refresh_token"),
    access_token: text("access_token"),
    expires_at: integer("expires_at"),
    token_type: varchar("token_type", { length: 255 }),
    scope: varchar("scope", { length: 255 }),
    id_token: text("id_token"),
    session_state: varchar("session_state", { length: 255 }),
  },
  (account) => ({
    compoundKey: primaryKey({
      columns: [account.provider, account.providerAccountId],
    }),
    userIdIdx: index("account_user_id_idx").on(account.userId),
  })
);

export const accountsRelations = relations(accounts, ({ one }) => ({
  user: one(users, { fields: [accounts.userId], references: [users.id] }),
}));

export const sessions = createTable(
  "session",
  {
    sessionToken: varchar("session_token", { length: 255 })
      .notNull()
      .primaryKey(),
    userId: varchar("user_id", { length: 255 })
      .notNull()
      .references(() => users.id),
    expires: timestamp("expires", {
      mode: "date",
      withTimezone: true,
    }).notNull(),
  },
  (session) => ({
    userIdIdx: index("session_user_id_idx").on(session.userId),
  })
);

export const sessionsRelations = relations(sessions, ({ one }) => ({
  user: one(users, { fields: [sessions.userId], references: [users.id] }),
}));

export const verificationTokens = createTable(
  "verification_token",
  {
    identifier: varchar("identifier", { length: 255 }).notNull(),
    token: varchar("token", { length: 255 }).notNull(),
    expires: timestamp("expires", {
      mode: "date",
      withTimezone: true,
    }).notNull(),
  },
  (vt) => ({
    compoundKey: primaryKey({ columns: [vt.identifier, vt.token] }),
  })
);

// ------------------------------

export const pgGender = pgEnum("gender", ["male", "female", "other"]);
export const patients = createTable("patients", {
  id: uuid("id").primaryKey().defaultRandom().unique(),
  firstName: text("first_name").notNull(),
  lastName: text("last_name").notNull(),
  birthDate: date("birth_date").notNull(),
  gender: pgGender("gender").notNull(),
  notes: text("notes").default("").notNull(),

  createdAt: timestamp("created_at", { withTimezone: true })
    .defaultNow()
    .notNull(),
});
export const detections = createTable("detections", {
  id: uuid("id").primaryKey().defaultRandom().unique(),
  patientId: uuid("patient_id")
    .notNull()
    .references(() => patients.id),
  createdAt: timestamp("created_at", { withTimezone: true })
    .defaultNow()
    .notNull(),
});


export const detectionsRelations = relations(detections, ({ one }) => ({
  patient: one(patients, { fields: [detections.patientId], references: [patients.id] }),
}));

export const ecg = createTable("ecg", {
  id: serial("id").primaryKey(),
  patientId: uuid("patientId").notNull().references(() => patients.id),
  timestamp: timestamp("timestamp", { withTimezone: true }).notNull(),
  value: doublePrecision("value").notNull(),
}, (t) => ({
  idx: index("idx_patient_id_timestamp").on(t.patientId, t.timestamp),
}));

export const ecgRelations = relations(ecg, ({ one }) => ({
  patient: one(patients, { fields: [ecg.patientId], references: [patients.id] }),
}));

export const resp = createTable("resp", {
  id: serial("id").primaryKey(),
  patientId: uuid("patientId").notNull().references(() => patients.id),
  timestamp: timestamp("timestamp", { withTimezone: true }).notNull(),
  value: doublePrecision("value").notNull(),
}, (t) => ({
  idx: index("idx_patient_id_timestamp_resp").on(t.patientId, t.timestamp),
}));

export const respRelations = relations(resp, ({ one }) => ({
  patient: one(patients, { fields: [resp.patientId], references: [patients.id] }),
}));
