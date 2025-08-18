"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { FaSearch } from "react-icons/fa";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination";

interface Audiencia {
  fecha_audiencia: string;
  hora: string;
  rol: string;
  caratula: string;
  tipo_audiencia: string;
  estado: string;
  fecha_fallo?: string;
  doc_resolucion?: string;
}

export default function AudienciasProximas() {
  const [audiencias, setAudiencias] = useState<Audiencia[]>([]);
  const [loading, setLoading] = useState(true);

  const [busqueda, setBusqueda] = useState("");
  const [tipoSeleccionado, setTipoSeleccionado] = useState<string | undefined>("__ALL__");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [soloFuturas, setSoloFuturas] = useState(false); // <- desactivado por defecto
  const [pagina, setPagina] = useState(1);

  const porPagina = 20;

  // Parser robusto: DD-MM-YYYY (CSV) y YYYY-MM-DD (inputs date)
  const parseFecha = (fechaStr: string): Date => {
    if (!fechaStr) return new Date("Invalid");
    const partes = fechaStr.trim().split("-");
    if (partes.length !== 3) return new Date("Invalid");

    if (partes[0].length === 2) {
      // DD-MM-YYYY
      const [d, m, y] = partes.map(Number);
      return new Date(y, m - 1, d);
    }
    if (partes[0].length === 4) {
      // YYYY-MM-DD
      const [y, m, d] = partes.map(Number);
      return new Date(y, m - 1, d);
    }
    return new Date("Invalid");
  };

  const hoy = useMemo(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }, []);

  const getDiasRestantes = (fechaStr: string) => {
    const fecha = parseFecha(fechaStr);
    const diffTime = fecha.getTime() - hoy.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const getClasificacion = (dias: number) => {
    if (dias <= 14) return "muy_proxima";
    if (dias <= 28) return "proxima";
    return "aun_queda";
  };

  const getColorPildora = (clasificacion: string) => {
    if (clasificacion === "muy_proxima") return "bg-red-500 text-white";
    if (clasificacion === "proxima") return "bg-yellow-400 text-black";
    return "bg-gray-300 text-black";
  };

  const getTextoPildora = (clasificacion: string) => {
    if (clasificacion === "muy_proxima") return "Muy próxima";
    if (clasificacion === "proxima") return "Próxima";
    return "Con tiempo";
  };

  const getPageItems = (total: number, current: number, delta = 2) => {
    const range: (number | "...")[] = [];
    const left = Math.max(2, current - delta);
    const right = Math.min(total - 1, current + delta);

    range.push(1); // siempre la primera

    if (left > 2) range.push("...");
    for (let i = left; i <= right; i++) range.push(i);
    if (right < total - 1) range.push("...");

    if (total > 1) range.push(total); // siempre la última
    return range;
  };

  // Carga de datos
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        setLoading(true);
        const res = await fetch("/api/audiencias", { cache: "no-store" });
        if (!res.ok) throw new Error(`/api/audiencias ${res.status}`);
        const json = await res.json();
        const data: Audiencia[] = Array.isArray(json) ? json : [];
        if (!active) return;

        const ordenadas = [...data].sort(
          (a, b) =>
            parseFecha(a.fecha_audiencia).getTime() -
            parseFecha(b.fecha_audiencia).getTime()
        );
        setAudiencias(ordenadas);
      } catch (e) {
        console.error("Error cargando /api/audiencias:", e);
        if (active) setAudiencias([]);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const limpiarFiltros = () => {
    setBusqueda("");
    setTipoSeleccionado("__ALL__");
    setFechaDesde("");
    setFechaHasta("");
    setSoloFuturas(false);
    setPagina(1);
  };

  // Opciones de tipo (limpia y sin vacíos)
  const tiposAudiencia = useMemo(() => {
    const setTipos = new Set<string>();
    for (const a of audiencias) {
      const t = (a?.tipo_audiencia ?? "").toString().trim();
      if (t.length > 0) setTipos.add(t);
    }
    return Array.from(setTipos).sort((x, y) => x.localeCompare(y));
  }, [audiencias]);

  // Base (aplica 'solo futuras' si corresponde)
  const base = useMemo(() => {
    const validas = audiencias.filter(
      (a) => !isNaN(parseFecha(a.fecha_audiencia).getTime())
    );
    if (!soloFuturas) return validas;
    return validas.filter((a) => parseFecha(a.fecha_audiencia) >= hoy);
  }, [audiencias, soloFuturas, hoy]);

  // Filtros + orden
  const audienciasFiltradas = useMemo(() => {
    const b = busqueda.trim().toLowerCase();
    const desde = fechaDesde ? parseFecha(fechaDesde) : null;
    const hasta = fechaHasta ? parseFecha(fechaHasta) : null;

    return base
      .filter((a) => !b || a.rol.toLowerCase().includes(b) || a.caratula.toLowerCase().includes(b))
      .filter((a) => !tipoSeleccionado || tipoSeleccionado === "__ALL__" || a.tipo_audiencia === tipoSeleccionado)
      .filter((a) => {
        const f = parseFecha(a.fecha_audiencia);
        return (!desde || f >= desde) && (!hasta || f <= hasta);
      })
      .sort(
        (a, b) =>
          parseFecha(a.fecha_audiencia).getTime() -
          parseFecha(b.fecha_audiencia).getTime()
      );
  }, [base, busqueda, tipoSeleccionado, fechaDesde, fechaHasta]);

  const totalPaginas = Math.ceil(audienciasFiltradas.length / porPagina) || 1;
  const paginaSegura = Math.min(pagina, totalPaginas);
  const paginadas = useMemo(
    () =>
      audienciasFiltradas.slice(
        (paginaSegura - 1) * porPagina,
        paginaSegura * porPagina
      ),
    [audienciasFiltradas, paginaSegura]
  );

  useEffect(() => {
    if (pagina > totalPaginas) setPagina(totalPaginas);
  }, [pagina, totalPaginas]);

  return (
    <div className="space-y-6 max-w-full px-4">
      <h1 className="text-2xl font-bold">Audiencias</h1>

      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <FaSearch />
          <Input
            type="text"
            placeholder="Buscar por rol o carátula"
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPagina(1);
            }}
            className="w-[260px]"
          />
        </div>

        <Select
          value={tipoSeleccionado}
          onValueChange={(val) => {
            setTipoSeleccionado(val);
            setPagina(1);
          }}
        >
          <SelectTrigger className="w-[260px]">
            <SelectValue placeholder="Audiencia pública" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__ALL__">Todos los tipos</SelectItem>
            {tiposAudiencia.map((tipo) => (
              <SelectItem key={tipo} value={tipo}>
                {tipo}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={fechaDesde}
          onChange={(e) => {
            setFechaDesde(e.target.value);
            setPagina(1);
          }}
          className="w-[160px]"
        />
        <Input
          type="date"
          value={fechaHasta}
          onChange={(e) => {
            setFechaHasta(e.target.value);
            setPagina(1);
          }}
          className="w-[160px]"
        />

        <div className="flex items-center gap-2 pl-1">
          <Checkbox
            id="solo-futuras"
            checked={soloFuturas}
            onCheckedChange={(v) => {
              setSoloFuturas(Boolean(v));
              setPagina(1);
            }}
          />
          <label
            htmlFor="solo-futuras"
            className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Solo futuras
          </label>
        </div>

        <Button variant="outline" onClick={limpiarFiltros}>
          Limpiar filtros
        </Button>
      </div>

      <div className="overflow-x-auto border rounded-lg">
        {loading ? (
          <div className="p-6 text-sm text-muted-foreground">Cargando…</div>
        ) : paginadas.length === 0 ? (
          <div className="p-6 text-sm text-muted-foreground">
            No hay audiencias que coincidan con los filtros.
          </div>
        ) : (
          <Table className="min-w-full table-fixed">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Fecha</TableHead>
                <TableHead className="w-[80px]">Hora</TableHead>
                <TableHead className="w-[120px]">Rol</TableHead>
                <TableHead className="w-[320px]">Carátula</TableHead>
                <TableHead className="w-[220px]">Tipo</TableHead>
                <TableHead className="w-[140px]">Estado</TableHead>
                <TableHead className="w-[120px]">Días</TableHead>
                <TableHead className="w-[160px]">Clasificación</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginadas.map((a) => {
                const dias = getDiasRestantes(a.fecha_audiencia);
                const clasificacion = getClasificacion(dias);
                const rowKey = `${a.fecha_audiencia}_${a.hora}_${a.rol}`;
                return (
                  <TableRow key={rowKey}>
                    <TableCell>{a.fecha_audiencia}</TableCell>
                    <TableCell>{a.hora}</TableCell>
                    <TableCell className="whitespace-nowrap">{a.rol}</TableCell>
                    <TableCell className="break-words whitespace-normal">{a.caratula}</TableCell>
                    <TableCell>{a.tipo_audiencia}</TableCell>
                    <TableCell>{a.estado}</TableCell>
                    <TableCell>{dias}</TableCell>
                    <TableCell>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${getColorPildora(
                          clasificacion
                        )}`}
                      >
                        {getTextoPildora(clasificacion)}
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      {!loading && audienciasFiltradas.length > 0 && totalPaginas > 1 && (
        <Pagination className="justify-center pt-4">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                aria-label="Anterior"
                onClick={() => setPagina((p) => Math.max(1, p - 1))}
                // desactivar si estás en la primera
                className={pagina === 1 ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>

            {getPageItems(totalPaginas, pagina, 2).map((item, idx) =>
              item === "..." ? (
                <PaginationItem key={`e-${idx}`}>
                  <PaginationEllipsis />
                </PaginationItem>
              ) : (
                <PaginationItem key={item}>
                  <PaginationLink
                    isActive={item === pagina}
                    aria-current={item === pagina ? "page" : undefined}
                    onClick={() => setPagina(item as number)}
                  >
                    {item}
                  </PaginationLink>
                </PaginationItem>
              )
            )}

            <PaginationItem>
              <PaginationNext
                aria-label="Siguiente"
                onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
                className={pagina === totalPaginas ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
