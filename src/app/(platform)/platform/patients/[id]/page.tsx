import { EcgGraph } from "@/app/(platform)/platform/patients/[id]/graph";
import { db } from "@/server/db";
import { notFound } from "next/navigation";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patient = await db.query.patients.findFirst({
    where: (table, { eq }) => eq(table.id, id)
  })
  if (!patient) {
    return notFound();
  }
  return (
    <div>
      <h1>{patient.firstName} {patient.lastName}</h1>
      <div className="flex flex-row gap-4 w-full">
        <EcgGraph id={id} />
        <EcgGraph id={id} />
      </div>
    </div>
  )
}