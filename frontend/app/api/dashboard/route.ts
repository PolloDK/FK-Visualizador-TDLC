import fs from "fs/promises";
import path from "path";
import { parse } from "csv-parse/sync";
import {
  differenceInCalendarDays,
  parse as parseDate,
  format,
  isValid,
} from "date-fns";
import { CausaDetalle, Audiencia, CausaResumen } from "@/types/dashboard";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Rutas a los archivos
    const detallePath = path.join(process.cwd(), "data/rol_idcausa_detalle.csv");
    const audienciasPath = path.join(process.cwd(), "data/calendario_audiencias.csv");
    const rolInfoPath = path.join(process.cwd(), "data/rol_idcausa.csv");

    // Lectura y parseo de los archivos CSV
    const [detalleRaw, audienciasRaw, rolInfoRaw] = await Promise.all([
      fs.readFile(detallePath, "utf-8"),
      fs.readFile(audienciasPath, "utf-8"),
      fs.readFile(rolInfoPath, "utf-8"),
    ]);

    const detalleParsed = parse(detalleRaw, {
      columns: true,
      skip_empty_lines: true,
      delimiter: ",",
    }) as CausaDetalle[];

    const audienciasParsed = parse(audienciasRaw, {
      columns: true,
      skip_empty_lines: true,
      delimiter: ",",
    }) as Audiencia[];

    const rolInfoParsed = parse(rolInfoRaw, {
      columns: true,
      skip_empty_lines: true,
      delimiter: ",",
    }) as CausaResumen[];

    // Filtrar causas con fallo registrado
    const causasConFallo = detalleParsed.filter(
      (c) => c.fallo_detectado === "True" && c.fecha_fallo
    );

    const diferenciasDias: number[] = [];
    const diferenciasPorTipo: Record<string, number[]> = {};
    const diferenciasPorMes: Record<string, number[]> = {};

    for (const causa of causasConFallo) {
      // Buscar audiencias relevantes (vista o pública)
      const audienciasDeCausa = audienciasParsed.filter(
        (a) =>
          a.rol === causa.rol &&
          (a.tipo_audiencia?.toLowerCase().includes("vista") ||
            a.tipo_audiencia?.toLowerCase().includes("pública"))
      );

      if (!audienciasDeCausa.length) continue;

      // Parsear fechas de audiencias en formato correcto
      const fechasAudiencias = audienciasDeCausa
        .map((a) => parseDate(a.fecha, "dd-MM-yyyy", new Date()))
        .filter(isValid);

      if (!fechasAudiencias.length) continue;

      // Tomar la audiencia más reciente
      const fechaAudiencia = fechasAudiencias.sort((a, b) => b.getTime() - a.getTime())[0];
      const fechaFallo = parseDate(causa.fecha_fallo, "yyyy-MM-dd", new Date());

      if (!isValid(fechaFallo)) continue;

      const dias = differenceInCalendarDays(fechaFallo, fechaAudiencia);
      if (dias < 0) continue;

      diferenciasDias.push(dias);

      // Obtener tipo de procedimiento
      const info = rolInfoParsed.find((r) => r.rol === causa.rol);
      const tipo = info?.procedimiento || "Desconocido";

      if (!diferenciasPorTipo[tipo]) diferenciasPorTipo[tipo] = [];
      diferenciasPorTipo[tipo].push(dias);

      const mes = format(fechaFallo, "yyyy-MM");
      if (!diferenciasPorMes[mes]) diferenciasPorMes[mes] = [];
      diferenciasPorMes[mes].push(dias);
    }

    // Cálculos de promedios
    const promedioGlobal =
      diferenciasDias.reduce((sum, dias) => sum + dias, 0) / (diferenciasDias.length || 1);

    const promedioPorTipo = Object.fromEntries(
      Object.entries(diferenciasPorTipo).map(([tipo, dias]) => [
        tipo,
        Math.round(dias.reduce((sum, d) => sum + d, 0) / dias.length),
      ])
    );

    const promedioPorMes = Object.fromEntries(
      Object.entries(diferenciasPorMes)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([mes, dias]) => [
          mes,
          Math.round(dias.reduce((sum, d) => sum + d, 0) / dias.length),
        ])
    );

    return NextResponse.json({
      promedio_dias_entre_audiencia_y_fallo: Math.round(promedioGlobal),
      total_causas: diferenciasDias.length,
      promedio_por_tipo: promedioPorTipo,
      promedio_por_mes: promedioPorMes,
      distribucion_dias: diferenciasDias,
    });
  } catch (err) {
    console.error("❌ Error en API dashboard:", err);
    return NextResponse.json({ error: "Error procesando datos" }, { status: 500 });
  }
}
