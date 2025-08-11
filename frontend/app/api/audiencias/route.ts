import { NextResponse } from "next/server";
import { readFileSync } from "fs";
import { parse } from "csv-parse/sync";
import path from "path";

export async function GET() {
  const filePath = path.join(process.cwd(), "../backend/data/calendario_audiencias.csv");

  try {
    const fileContent = readFileSync(filePath, "utf-8");

    const rawRecords = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
    }) as Record<string, string>[];

    // Limpieza manual adicional por si acaso
    const records = rawRecords.map((r: Record<string, string>) => ({
      fecha_audiencia: r["fecha"]?.trim(),
      hora: r["hora"]?.trim(),
      rol: r["rol"]?.trim(),
      caratula: r["caratula"]?.trim(),
      tipo_audiencia: r["tipo_audiencia"]?.trim(),
      estado: r["estado"]?.trim(),
    }));

    return NextResponse.json(records);
  } catch (error) {
    return NextResponse.json({ error: "No se pudo leer el CSV" }, { status: 500 });
  }
}
