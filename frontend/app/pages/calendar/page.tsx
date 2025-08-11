"use client";

import { useEffect, useState } from "react";
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
import { FaSearch } from "react-icons/fa";

interface Audiencia {
  fecha_audiencia: string;
  hora: string;
  rol: string;
  caratula: string;
  tipo_audiencia: string;
  estado: string;
  fecha_fallo?: string;
}

export default function AudienciasProximas() {
  const [audiencias, setAudiencias] = useState<Audiencia[]>([]);
  const [busqueda, setBusqueda] = useState("");
  const [tipoSeleccionado, setTipoSeleccionado] = useState("");
  const [pagina, setPagina] = useState(1);
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const porPagina = 20;

  const parseFecha = (fechaStr: string): Date => {
    const partes = fechaStr?.trim().split("-");
    if (partes?.length !== 3) return new Date("Invalid");
    const [dia, mes, anio] = partes.map(Number);
    return new Date(anio, mes - 1, dia);
  };

  const hoy = new Date();

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

  useEffect(() => {
    fetch("/api/audiencias")
      .then((res) => res.json())
      .then((data) => setAudiencias(data));
  }, []);

  const limpiarFiltros = () => {
    setBusqueda("");
    setTipoSeleccionado("");
    setFechaDesde("");
    setFechaHasta("");
    setPagina(1);
  };

  const audienciasFiltradas = audiencias
    .filter((a) => {
      const fecha = parseFecha(a.fecha_audiencia);
      return !isNaN(fecha.getTime()) && fecha >= hoy;
    })
    .filter((a) => {
      const b = busqueda.toLowerCase();
      return (
        a.rol.toLowerCase().includes(b) ||
        a.caratula.toLowerCase().includes(b)
      );
    })
    .filter((a) => !tipoSeleccionado || a.tipo_audiencia === tipoSeleccionado)
    .filter((a) => {
      const fecha = parseFecha(a.fecha_audiencia);
      const desde = fechaDesde ? parseFecha(fechaDesde) : null;
      const hasta = fechaHasta ? parseFecha(fechaHasta) : null;
      return (
        (!desde || fecha >= desde) &&
        (!hasta || fecha <= hasta)
      );
    })
    .sort(
      (a, b) =>
        parseFecha(a.fecha_audiencia).getTime() -
        parseFecha(b.fecha_audiencia).getTime()
    );

  const totalPaginas = Math.ceil(audienciasFiltradas.length / porPagina);
  const paginadas = audienciasFiltradas.slice(
    (pagina - 1) * porPagina,
    pagina * porPagina
  );

  return (
    <div className="space-y-6 max-w-full px-4">
      <h1 className="text-2xl font-bold">Próximas Audiencias</h1>

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
          onValueChange={(val) => {
            setTipoSeleccionado(val);
            setPagina(1);
          }}
          value={tipoSeleccionado}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Filtrar por tipo de audiencia" />
          </SelectTrigger>
          <SelectContent>
            {[...new Set(audiencias.map((a) => a.tipo_audiencia))].map(
              (tipo) => (
                <SelectItem key={tipo} value={tipo}>
                  {tipo}
                </SelectItem>
              )
            )}
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className="w-[160px]"
        />
        <Input
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className="w-[160px]"
        />

        <Button variant="outline" onClick={limpiarFiltros}>
          Limpiar filtros
        </Button>
      </div>

      <div className="overflow-x-auto border rounded-lg">
        <Table className="min-w-full table-fixed">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px]">Fecha</TableHead>
              <TableHead className="w-[80px]">Hora</TableHead>
              <TableHead className="w-[120px]">Rol</TableHead>
              <TableHead className="w-[300px]">Carátula</TableHead>
              <TableHead className="w-[200px]">Tipo</TableHead>
              <TableHead className="w-[100px]">Estado</TableHead>
              <TableHead className="w-[120px]">Días restantes</TableHead>
              <TableHead className="w-[160px]">Clasificación</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginadas.map((a, i) => {
              const dias = getDiasRestantes(a.fecha_audiencia);
              const clasificacion = getClasificacion(dias);
              return (
                <TableRow key={i}>
                  <TableCell>{a.fecha_audiencia}</TableCell>
                  <TableCell>{a.hora}</TableCell>
                  <TableCell>{a.rol}</TableCell>
                  <TableCell className="break-words whitespace-normal">
                    {a.caratula}
                  </TableCell>
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
      </div>

      {totalPaginas > 1 && (
        <div className="flex justify-center gap-2 pt-4">
          {[...Array(totalPaginas)].map((_, idx) => (
            <Button
              key={idx}
              size="sm"
              variant={idx + 1 === pagina ? "default" : "outline"}
              onClick={() => setPagina(idx + 1)}
            >
              {idx + 1}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
