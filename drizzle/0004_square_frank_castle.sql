CREATE TABLE IF NOT EXISTS "htr-2024_resp" (
	"id" serial PRIMARY KEY NOT NULL,
	"patientId" uuid NOT NULL,
	"timestamp" timestamp with time zone NOT NULL,
	"value" double precision NOT NULL
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "htr-2024_resp" ADD CONSTRAINT "htr-2024_resp_patientId_htr-2024_patients_id_fk" FOREIGN KEY ("patientId") REFERENCES "public"."htr-2024_patients"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "idx_patient_id_timestamp_resp" ON "htr-2024_resp" USING btree ("patientId","timestamp");