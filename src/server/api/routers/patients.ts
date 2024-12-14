import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { patients } from "@/server/db/schema";
import { newPatientSchema } from "@/types/patient";

export const patientsRouter = createTRPCRouter({
  getPatients: protectedProcedure.query(async ({ ctx }) => {
    return await ctx.db.query.patients.findMany();
  }),
  createPatient: protectedProcedure.input(newPatientSchema).mutation(async ({ ctx, input }) => {
    const { firstName, lastName, birthDate, gender, notes } = input;
    const patient = await ctx.db.insert(patients).values({
      firstName,
      lastName,
      birthDate,
      gender,
      notes,
    }).returning();

    return patient;
  })
})