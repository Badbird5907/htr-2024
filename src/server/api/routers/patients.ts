import { createTRPCRouter, protectedProcedure, publicProcedure } from "@/server/api/trpc";
import { patients } from "@/server/db/schema";
import { newPatientSchema } from "@/types/patient";

export const patientsRouter = createTRPCRouter({
  getPatients: publicProcedure.query(async ({ ctx }) => {
    return await ctx.db.query.patients.findMany();
  }),
  createPatient: publicProcedure.input(newPatientSchema).mutation(async ({ ctx, input }) => {
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