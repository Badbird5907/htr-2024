"use client";

import { NewPatient } from "@/app/(platform)/platform/patients/new";
import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/trpc/react";
import { type Patient } from "@/types";
import { type ColumnDef } from "@tanstack/react-table";
import { Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const columns: ColumnDef<Patient>[] = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "firstName", header: "First Name" },
  { accessorKey: "lastName", header: "Last Name" },
  { accessorKey: "birthDate", header: "Birth Date" },
  { accessorKey: "gender", header: "Gender" },
  { accessorKey: "notes", header: "Notes" },
  {
    accessorKey: "__actions",
    header: "Actions",
    cell: ({ row }) => {
      return (
        <Link href={`/platform/patients/${row.original.id}`}>
          <Button>View</Button>
        </Link>
      )
    }
  }
];

export default function Page() {
  const { data, isLoading } = api.patients.getPatients.useQuery();
  const [filter, setFilter] = useState<string>("");

  return (
    <div className="flex flex-col gap-4 px-2">
      <h1 className="text-2xl font-bold">Patients</h1>
      <div className="w-full flex flex-col gap-4">
        <DataTable columns={columns} data={data ?? []} globalFilter={filter} actionsBar={(
          <div className="flex flex-col md:flex-row w-full items-center gap-2">
            {/* <NewPatient /> */}
            <Input
              className="w-full md:w-1/3 mx-2"
              type="text"
              placeholder="Search"
              startContent={<Search />}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
        )} />
      </div>
    </div>
  )
}