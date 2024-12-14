import { z } from "zod";

export const newPatientSchema = z.object({
  firstName: z.string().min(1),
  lastName: z.string().min(1),
  birthDate: z.string().min(1),
  gender: z.enum(["male", "female", "other"]),
  notes: z.string().optional(),
})