import { readFileSync } from 'fs';
import { Float, tableFromIPC, Vector } from 'apache-arrow';
import { tsDb } from '@/server/ts/schema';
import { db } from '@/server/db';
import { ecg as dbEcg } from '@/server/db/schema';
import { asc, desc } from 'drizzle-orm';
import { sampleRate } from '@/server/ts/values';
const arrow = readFileSync("data/data-00000-of-00010.arrow")
const table = tableFromIPC(arrow)

// get the first 10 rows
const arr = table.toArray()
type Row = {
  infant_id: number,
  segment_id: number,
  input: { toArray: () => { toArray: () => [number, number] }[] }
  label: number
}

let end = new Date()
const interval = (1 / sampleRate) * 1000
// delete all data
// eslint-disable-next-line drizzle/enforce-delete-with-where
await db.delete(dbEcg);
// process first 10 rows
for (let i = 0; i < 10; i++) {
  const row = arr[i] as Row
  const points = row.input.toArray().map(x => x.toArray());
  
  console.log(`Row ${i}: ${points.length} data points`)
  
  const ecg = points.map((x, j) => {
    const value = x[0]
    const timestamp = end.getTime() - j * interval
    return { value, timestamp }
  });

  end = new Date(ecg[ecg.length - 1]!.timestamp)

  const pid = "0da28d88-932c-4e16-bb3d-82aad9de4e51";

  // await tsDb`
  //   INSERT INTO ecg (patientId, timestamp, value) 
  //   VALUES ${tsDb(ecg.map(x => [pid, x.timestamp, x.value]))}
  // `
  await db.insert(dbEcg).values(ecg.map(x => {
    return {
      patientId: pid,
      timestamp: new Date(x.timestamp),
      value: x.value
    }
  }))
}

const min = await db.select().from(dbEcg).orderBy(desc(dbEcg.id)).limit(1)
console.log("min", min[0]?.timestamp)
const max = await db.select().from(dbEcg).orderBy(asc(dbEcg.id)).limit(1)
console.log("max", max[0]?.timestamp)
process.exit(0)