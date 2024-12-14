"use server";

import { auth } from "@/server/auth";
import { db } from "@/server/db";
import { ecg } from "@/server/db/schema";
import { windowSamples, minDate, windowSize } from "@/server/ts/values";
import { and, eq, gte, lte, asc } from "drizzle-orm";

export const getEcgData = async (id: string, step: number) => {
  // Calculate window start and end times
  const startDate = new Date(minDate.getTime() + (step * 1000)); // Convert step to milliseconds
  const endDate = new Date(startDate.getTime() + (windowSize * 1000)); // Add window size (15 seconds)

  const data = await db.query.ecg.findMany({
    where: (table) => and(
      eq(table.patientId, id),
      gte(table.timestamp, startDate),
      lte(table.timestamp, endDate)
    ),
    orderBy: (table) => asc(table.timestamp)
  });

  const resp = await db.query.resp.findMany({
    where: (table) => and(
      eq(table.patientId, id),
      gte(table.timestamp, startDate),
      lte(table.timestamp, endDate)
    ),
    orderBy: (table) => asc(table.timestamp)
  });

  return {
    ecg: data.map((x) => x.value),
    resp: resp.map((x) => x.value)
  };
}