CREATE TABLE IF NOT EXISTS "htr-2024_ecg" (
	"id" serial PRIMARY KEY NOT NULL,
	"patientId" uuid NOT NULL,
	"timestamp" timestamp NOT NULL,
	"value" numeric NOT NULL
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "htr-2024_ecg" ADD CONSTRAINT "htr-2024_ecg_patientId_htr-2024_patients_id_fk" FOREIGN KEY ("patientId") REFERENCES "public"."htr-2024_patients"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS "idx_patient_id_timestamp" ON "htr-2024_ecg" USING btree ("patientId","timestamp");