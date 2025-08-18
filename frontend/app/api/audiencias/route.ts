// app/api/audiencias/route.ts
import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type AudienciaCSV = {
  fecha?: string; hora?: string; rol?: string; caratula?: string;
  tipo_audiencia?: string; estado?: string; doc_resolucion?: string;
};

async function findCsvPath(): Promise<string | null> {
  const candidates = [
    path.resolve(process.cwd(), "backend/data/calendar/calendario_audiencias.csv"),
    path.resolve(process.cwd(), "../backend/data/calendar/calendario_audiencias.csv"),
  ];
  for (const p of candidates) {
    try { await fs.access(p); return p; } catch {}
  }
  return null;
}

export async function GET() {
  try {
    const csvPath = await findCsvPath();
    if (!csvPath) {
      console.error("CSV no encontrado en rutas candidatas.");
      return NextResponse.json([]); // <- siempre array
    }

    const csvRaw = await fs.readFile(csvPath, "utf-8");
    const rows = parse(csvRaw, {
      columns: true, skip_empty_lines: true, trim: true,
    }) as AudienciaCSV[];

    const data = rows.map((r) => ({
      fecha_audiencia: (r.fecha ?? "").trim(),
      hora: (r.hora ?? "").trim(),
      rol: (r.rol ?? "").trim(),
      caratula: (r.caratula ?? "").trim(),
      tipo_audiencia: (r.tipo_audiencia ?? "").trim(),
      estado: (r.estado ?? "").trim(),
      doc_resolucion: (r.doc_resolucion ?? "").trim(),
    }));

    return NextResponse.json(data);
  } catch (err) {
    console.error("Error leyendo CSV:", err);
    // Importante: devolvemos [] para que el front no rompa
    return NextResponse.json([]);
  }
}
