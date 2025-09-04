"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
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
  link: string;
}

export default function AudienciasProximas() {
  const [audiencias, setAudiencias] = useState<Audiencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [tipoSeleccionado, setTipoSeleccionado] = useState<string | undefined>("__ALL__");
  const [estadoSeleccionado, setEstadoSeleccionado] = useState<string | undefined>("__ALL__");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [soloFuturas, setSoloFuturas] = useState(true);
  const [pagina, setPagina] = useState(1);
  const porPagina = 20;

  const parseFecha = (fechaStr: string): Date => {
    if (!fechaStr) return new Date("Invalid");
    const partes = fechaStr.trim().split("-");
    if (partes.length !== 3) return new Date("Invalid");
    if (partes[0].length === 2) {
      const [d, m, y] = partes.map(Number);
      return new Date(y, m - 1, d);
    }
    if (partes[0].length === 4) {
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
    if (dias < 0) return "ya_fue";
    if (dias <= 7) return "proxima_semana";
    if (dias > 7 && dias <= 14) return "mas_de_una_semana";
    if (dias > 14 && dias <= 31) return "dentro_del_mes";
    return "mas_de_un_mes";
  };

  const getColorPildora = (clasificacion: string) => {
    if (clasificacion === "ya_fue") return "bg-gray-300 text-black";
    if (clasificacion === "proxima_semana") return "bg-red-500 text-white";
    if (clasificacion === "mas_de_una_semana") return "bg-yellow-400 text-black";
    if (clasificacion === "dentro_del_mes") return "bg-blue-400 text-white";
    return "bg-gray-300 text-black";
  };

  const getTextoPildora = (clasificacion: string) => { 
    if (clasificacion === "ya_fue") return "Audiencia pasada"
    if (clasificacion === "proxima_semana") return "Próxima semana";
    if (clasificacion === "mas_de_una_semana") return "Más de una semana";
    if (clasificacion === "dentro_del_mes") return "Dentro de un mes";
    return "Más de un mes";
  };

  const getPageItems = (total: number, current: number, delta = 2) => {
    const range: (number | "...")[] = [];
    const left = Math.max(2, current - delta);
    const right = Math.min(total - 1, current + delta);
    range.push(1);
    if (left > 2) range.push("...");
    for (let i = left; i <= right; i++) range.push(i);
    if (right < total - 1) range.push("...");
    if (total > 1) range.push(total);
    return range;
  };

  useEffect(() => {
    const fetchAudiencias = async () => {
      try {
        setLoading(true);
        const queryParams = new URLSearchParams();
        if (fechaDesde) {
          const [y, m, d] = fechaDesde.split("-");
          queryParams.append("fecha_desde", `${d}-${m}-${y}`);
        }
        if (fechaHasta) {
          const [y, m, d] = fechaHasta.split("-");
          queryParams.append("fecha_hasta", `${d}-${m}-${y}`);
        }
        if (tipoSeleccionado && tipoSeleccionado !== "__ALL__") {
          queryParams.append("tipos", tipoSeleccionado);
        }
        if (estadoSeleccionado && estadoSeleccionado !== "__ALL__") {
          queryParams.append("estados", estadoSeleccionado);
        }
        if (busqueda.trim()) {
          queryParams.append("busqueda", busqueda.trim());
        }
        queryParams.append("solo_futuras", String(soloFuturas));

        const res = await fetch(`http://localhost:8000/calendario/calendario?${queryParams.toString()}`);
        if (!res.ok) throw new Error(`/calendario/calendario ${res.status}`);
        const json = await res.json();
        const data: Audiencia[] = Array.isArray(json) ? json : [];

        const ordenadas = [...data].sort(
          (a, b) => parseFecha(a.fecha_audiencia).getTime() - parseFecha(b.fecha_audiencia).getTime()
        );

        setAudiencias(ordenadas);
      } catch (e) {
        console.error("Error cargando /calendario/calendario:", e);
        setAudiencias([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAudiencias();
  }, [fechaDesde, fechaHasta, tipoSeleccionado, estadoSeleccionado, busqueda, soloFuturas]);

  const limpiarFiltros = () => {
    setBusqueda("");
    setTipoSeleccionado("__ALL__");
    setEstadoSeleccionado("__ALL__");
    setFechaDesde("");
    setFechaHasta("");
    setSoloFuturas(true);
    setPagina(1);
  };

  const tiposAudiencia = useMemo(() => {
    const setTipos = new Set<string>();
    for (const a of audiencias) {
      const t = a.tipo_audiencia?.trim();
      if (t) setTipos.add(t);
    }
    return Array.from(setTipos).sort();
  }, [audiencias]);

  const estadosAudiencia = useMemo(() => {
    const setEstados = new Set<string>();
    for (const a of audiencias) {
      const e = a.estado?.trim();
      if (e) setEstados.add(e);
    }
    return Array.from(setEstados).sort();
  }, [audiencias]);

  const totalPaginas = Math.ceil(audiencias.length / porPagina) || 1;
  const paginaSegura = Math.min(pagina, totalPaginas);

  const paginadas = useMemo(
    () => audiencias.slice((paginaSegura - 1) * porPagina, paginaSegura * porPagina),
    [audiencias, paginaSegura]
  );

  useEffect(() => {
    if (pagina > totalPaginas) setPagina(totalPaginas);
  }, [pagina, totalPaginas]);

  return (
    <div className="space-y-6 max-w-full px-4">
      <h1 className="text-2xl font-bold">Calendario de Audiencias</h1>

      <h2 className="text-lg font-semibold">Filtros</h2>
      <div className="flex flex-wrap gap-4 items-center">
        
        <div className="flex flex-col w-[260px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Filtrar por rol o carátula</div>
          <div className="flex items-center gap-2">
            <FaSearch />
            <Input
              type="text"
              placeholder="Buscar por rol o carátula"
              value={busqueda}
              onChange={(e) => { setBusqueda(e.target.value); setPagina(1); }}
              className="w-[260px]"
            />
          </div>
        </div>

        <div className="flex flex-col w-[260px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Filtrar por tipo de causa</div>
          <Select value={tipoSeleccionado} onValueChange={(val) => { setTipoSeleccionado(val); setPagina(1); }}>
            <SelectTrigger className="w-[260px]">
              <SelectValue placeholder="Tipo de audiencia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__ALL__">Todos los tipos</SelectItem>
              {tiposAudiencia.map((tipo) => (
                <SelectItem key={tipo} value={tipo}>{tipo}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col w-[260px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Filtrar por estado</div>
          <Select value={estadoSeleccionado} onValueChange={(val) => { setEstadoSeleccionado(val); setPagina(1); }}>
            <SelectTrigger className="w-[260px]">
              <SelectValue placeholder="Estado de audiencia" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__ALL__">Todos los estados</SelectItem>
              {estadosAudiencia.map((estado) => (
                <SelectItem key={estado} value={estado}>{estado}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        
        <div className="flex flex-col w-[160px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Desde</div>
          <Input
            type="date"
            value={fechaDesde}
            onChange={(e) => {
              setFechaDesde(e.target.value);
              setPagina(1);
            }}
          />
        </div>

        <div className="flex flex-col w-[160px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Hasta</div>
          <Input
            type="date"
            value={fechaHasta}
            onChange={(e) => {
              setFechaHasta(e.target.value);
              setPagina(1);
            }}
          />
        </div>  

        <div className="flex flex-col w-[160px]">
          <div className="text-sm font-medium text-gray-600 mb-2">Opciones</div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="solo-futuras"
              checked={soloFuturas}
              onCheckedChange={(v) => {
                setSoloFuturas(Boolean(v));
                setPagina(1);
              }}
            />
            <span className="text-sm">Solo futuras</span>
          </div>
        </div>

        <div className="flex flex-col items-start justify-end w-[160px] pb-[4px]">
          <div className="text-sm font-medium text-gray-600 mb-2 invisible">Botón</div>
          <Button variant="outline" onClick={limpiarFiltros}>
            Limpiar filtros
          </Button>
        </div>
      </div>

      <h2 className="text-lg font-semibold">Resultados</h2>
      <div className="overflow-x-auto border rounded-lg">
        {loading ? (
          <div className="p-6 text-sm text-muted-foreground">Cargando…</div>
        ) : paginadas.length === 0 ? (
          <div className="p-6 text-sm text-muted-foreground">No hay audiencias que coincidan con los filtros.</div>
        ) : (
          <Table className="min-w-full table-fixed">
            <TableHeader className="bg-gray-50">
              <TableRow>
                <TableHead className="w-[120px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Fecha
                </TableHead>
                <TableHead className="w-[80px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Hora
                </TableHead>
                <TableHead className="w-[160px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Rol
                </TableHead>
                <TableHead className="w-[320px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Carátula
                </TableHead>
                <TableHead className="w-[220px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Tipo
                </TableHead>
                <TableHead className="w-[140px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Estado
                </TableHead>
                <TableHead className="w-[120px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Días
                </TableHead>
                <TableHead className="w-[160px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Clasificación
                </TableHead>
                <TableHead className="w-[120px] px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Enlace
                </TableHead>
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
                      <TableCell>
                        {dias >= 0 ? dias : ""}
                      </TableCell>
                      <TableCell>
                        <span className={`text-xs px-2 py-1 rounded-full ${getColorPildora(clasificacion)}`}>
                          {getTextoPildora(clasificacion)}
                        </span>
                      </TableCell>
                      <TableCell className="text-left">
                        {a.link ? (
                          <a
                            href={a.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline text-sm"
                          >
                            Ver causa
                          </a>
                        ) : (
                          <span className="text-gray-400 text-sm italic">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
          </Table>
        )}
      </div>

      {!loading && audiencias.length > 0 && totalPaginas > 1 && (
        <Pagination className="justify-center pt-4">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious aria-label="Anterior" onClick={() => setPagina((p) => Math.max(1, p - 1))} className={pagina === 1 ? "pointer-events-none opacity-50" : ""} />
            </PaginationItem>
            {getPageItems(totalPaginas, pagina, 2).map((item, idx) => item === "..." ? (
              <PaginationItem key={`e-${idx}`}><PaginationEllipsis /></PaginationItem>
            ) : (
              <PaginationItem key={item}>
                <PaginationLink isActive={item === pagina} aria-current={item === pagina ? "page" : undefined} onClick={() => setPagina(item as number)}>
                  {item}
                </PaginationLink>
              </PaginationItem>
            ))}
            <PaginationItem>
              <PaginationNext aria-label="Siguiente" onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))} className={pagina === totalPaginas ? "pointer-events-none opacity-50" : ""} />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
