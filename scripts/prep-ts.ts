
import { tsDb } from "@/server/ts/schema"
import { readFileSync } from 'fs';
import { tableFromIPC } from 'apache-arrow';
const prep = async () => {
  await tsDb`DROP TABLE IF EXISTS ecg`
  const res = await tsDb`CREATE TABLE IF NOT EXISTS ecg (
    id SERIAL PRIMARY KEY,
    patientId UUID,
    timestamp TIMESTAMP,
    value NUMERIC
);`
  console.log(res)

  const arrow = readFileSync("data/data-00000-of-00010.arrow")
  const table = tableFromIPC(arrow)

  // get the first 5 rows
  const rows = table.slice(0, 5)
  console.log(rows)
}

void prep().then(() => {
  console.log("done")
})  