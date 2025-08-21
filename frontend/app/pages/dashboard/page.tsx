"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bar, Line, Pie } from "react-chartjs-2";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Bell, FileText, CheckCircle } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
} from "chart.js";
import { set } from "date-fns";

interface CausaDelDia {
  fecha_estado_diario: string;
  rol: string;
  descripcion: string;
  tramites: number;
  link: string;
}

interface TramiteDelDia {
  idCausa: string;
  rol: string;
  TipoTramite: string;
  Fecha: string;
  Referencia: string;
  Foja: string;
  Link_Descarga: string;
  Tiene_Detalles: string;
  Tiene_Firmantes: string;
}

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend);

export default function DashboardPage() {
  const [promedioAudiencia, setPromedioAudiencia] = useState<number | null>(null);
  const [promedioInicio, setPromedioInicio] = useState<number | null>(null);
  const [diasDesdeAudiencia, setDiasDesdeAudiencia] = useState<number | null>(null);
  const [causasDesdeAudiencia, setCausasDesdeAudiencia] = useState<number | null>(null);
  const [diasDesdeInicio, setDiasDesdeInicio] = useState<number | null>(null);
  const [causasDesdeInicio, setCausasDesdeInicio] = useState<number | null>(null);
  const [esperandoFallo, setEsperandoFallo] = useState<any[]>([]);
  const [evolucionAudienciaData, setEvolucionAudienciaData] = useState<any>({ labels: [], datasets: [] });
  const [evolucionInicioData, setEvolucionInicioData] = useState<any>({ labels: [], datasets: [] });
  const [totalCausas, setTotalCausas] = useState<number | null>(null);
  const [causasDelDia, setCausasDelDia] = useState<CausaDelDia[]>([]);
  const [tramitesDelDia, setTramitesDelDia] = useState<TramiteDelDia[]>([]);
  const [expandedCausa, setExpandedCausa] = useState<string | null>(null);

  const [fechaInicio, setFechaInicio] = useState("2022-01-01");
  const [fechaFin, setFechaFin] = useState("2025-12-31");
  const [tipo, setTipo] = useState("todos");

  const formatDateToDDMMYYYY = (dateString: string) => {
    const [year, month, day] = dateString.split("-");
    return `${day}-${month}-${year}`;
  };

  const toggleExpanded = (rol: string) => {
    setExpandedCausa(expandedCausa === rol ? null : rol);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = `fecha_inicio=${formatDateToDDMMYYYY(fechaInicio)}&fecha_fin=${formatDateToDDMMYYYY(fechaFin)}&tipo=${tipo}`;

        const [audienciageneralRes, tramitegeneralRes, audienciaRes, tramiteRes, esperandoRes, evolucionAudienciaRes, evolucionInicioRes, totalCausasRes, causasDelDiaRes, tramitesDelDiaRes,] = await Promise.all([
          fetch(`http://localhost:8000/causas/promedio-dias-audiencia-general`),
          fetch(`http://localhost:8000/causas/promedio-dias-inicio-general`),
          fetch(`http://localhost:8000/causas/promedio-dias-fallo?${params}`),
          fetch(`http://localhost:8000/causas/promedio-dias-desde-primer-tramite?${params}`),
          fetch(`http://localhost:8000/causas/causas-esperando-fallo`),
          fetch(`http://localhost:8000/causas/evolucion-diaria-audiencia?${params}`),
          fetch(`http://localhost:8000/causas/evolucion-diaria-inicio?${params}`),
          fetch(`http://localhost:8000/causas/total-causas`),
          // --- Estado diario ---
          fetch(`http://localhost:8000/estado-diario/causas-del-dia`),
          fetch(`http://localhost:8000/estado-diario/tramites-del-dia`)
        ]);

        const promedioAudiencia = await audienciageneralRes.json();
        const promedioInicio = await tramitegeneralRes.json();
        const audienciaData = await audienciaRes.json();
        const tramiteData = await tramiteRes.json();
        const esperandoData = await esperandoRes.json();
        const evolucionAudiencia = await evolucionAudienciaRes.json();
        const evolucionInicio = await evolucionInicioRes.json();
        const totalCausasData = await totalCausasRes.json();
        // --- Estado diario ---
        const causasDelDiaData = await causasDelDiaRes.json();
        const tramitesDelDiaData = await tramitesDelDiaRes.json();

        setPromedioAudiencia(promedioAudiencia.promedio_dias);
        setPromedioInicio(promedioInicio.promedio_dias);
        setDiasDesdeAudiencia(audienciaData.promedio_dias);
        setCausasDesdeAudiencia(audienciaData.n_causas);
        setDiasDesdeInicio(tramiteData.promedio_dias);
        setCausasDesdeInicio(tramiteData.n_causas);
        setTotalCausas(totalCausasData.total_causas);
        setEsperandoFallo(Array.isArray(esperandoData) ? esperandoData : []);
        // --- Estado diario ---
        setCausasDelDia(causasDelDiaData.causas_del_dia);
        setTramitesDelDia(tramitesDelDiaData.tramites_del_dia);

        const formatDataByRol = (data: any, label: string) => {
          if (!Array.isArray(data)) return { labels: [], datasets: [] };

          const sorted = [...data].sort(
            (a, b) => new Date(a.fecha_primer_tramite).getTime() - new Date(b.fecha_primer_tramite).getTime()
          );

          return {
            labels: sorted.map((item) => item.rol),
            datasets: [
              {
                label,
                data: sorted.map((item) => item.dias),
                borderColor: "rgb(75, 192, 192)",
                backgroundColor: "rgba(75, 192, 192, 0.3)",
                tension: 0.1,
              },
            ],
          };
        };


        setEvolucionAudienciaData(formatDataByRol(evolucionAudiencia, "Desde audiencia"));
        setEvolucionInicioData(formatDataByRol(evolucionInicio, "Desde inicio"));

      } catch (error) {
        console.error("Error al obtener métricas del dashboard:", error);
      }
    };

    fetchData();
  }, [fechaInicio, fechaFin, tipo]);

  const getTramitesForCausa = (rol: string) => {
    return tramitesDelDia.filter(tramite => tramite.rol === rol);
  };

  return (
    <div className="p-2 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Métricas del TDLC</h1>

      <Tabs defaultValue="resumen" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
          <TabsTrigger value="analitica">Analítica</TabsTrigger>
          <TabsTrigger value="estado diario">Estado Diario</TabsTrigger>
        </TabsList>

        <TabsContent value="resumen" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Días promedio desde audiencia</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-semibold">
                  {promedioAudiencia !== null ? `${promedioAudiencia} días` : "Cargando..."}
                </p>
                <p className="text-muted-foreground mt-2 text-sm">
                  Basado en todas las causas con audiencia vista o pública y fallo en expediente.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Días promedio desde primer trámite</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-semibold">
                  {promedioInicio !== null ? `${promedioInicio} días` : "Cargando..."}
                </p>
                <p className="text-muted-foreground mt-2 text-sm">
                  Basado en todas las causas con primer trámite y fallo.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Total de Causas</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-semibold">
                  {totalCausas !== null ? `${totalCausas} causas` : "Cargando..."}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Reclamaciones post fallo</CardTitle>
              </CardHeader>
              <CardContent>
                <Pie data={{ labels: [], datasets: [] }} options={{ responsive: true }} />
              </CardContent>
            </Card>

            <Card className="relative">
              <CardHeader>
                <CardTitle>Causas con audiencia esperando fallo</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="max-h-[580px] overflow-y-auto px-4 pb-4">
                  <div className="space-y-3 py-2">
                    {Array.isArray(esperandoFallo) && esperandoFallo.length > 0 ? (
                      esperandoFallo
                        .sort((a, b) => b.dias_desde_audiencia - a.dias_desde_audiencia)
                        .map((causa, index) => (
                          <a
                            key={index}
                            href={causa.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 rounded-lg border border-border hover:bg-muted transition-all duration-200 ease-in-out"
                          >
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                              <div className="w-full overflow-hidden">
                                <h3 className="text-md font-semibold">{causa.rol}</h3>
                                <p className="text-sm">{causa.caratula}</p>
                                <p className="text-xs text-muted-foreground mb-2">
                                  Audiencia: {new Date(causa.fecha_audiencia).toLocaleDateString("es-CL")}
                                </p>
                              </div>
                              <div className="flex gap-2 flex-wrap shrink-0">
                                <div className="bg-blue-600 hover:bg-blue-700 text-white text-sm text-primary px-2 py-1 rounded-full min-w-[70px] text-center">
                                  {causa.dias_desde_audiencia} días
                                </div>
                                <div className="bg-sky-500 hover:bg-sky-600 text-white text-sm bg-secondary px-2 py-1 rounded-full text-secondary-foreground min-w-[70px] text-center">
                                  Estimado: {causa.dias_estimados_restantes} días
                                </div>
                              </div>
                            </div>
                          </a>
                        ))
                    ) : (
                      <p className="text-muted-foreground text-sm px-4 py-2">No hay causas esperando fallo.</p>
                    )}
                  </div>
                </ScrollArea>

                {/* Sombra inferior como indicación de scroll */}
                <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-background to-transparent" />
              </CardContent>
            </Card>

          </div>

          <Separator />
        </TabsContent>

        <TabsContent value="analitica" className="space-y-6">
          <div className="space-y-3">
            <br/>
            <h2 className="text-2xl font-semibold">Análisis de causas</h2>
            <br/>
            <p className="text-muted-foreground">
              Esta sección permite monitorear la evolución de los tiempos de resolución de causas en el TDLC. Utiliza la fecha de la sentencia (`fecha_fallo`) como punto de referencia para calcular el promedio de días que toma una causa en resolverse, ya sea desde la fecha de su última audiencia pública (`vista`) o desde la fecha de su primer trámite. Los resultados se presentan tanto en un promedio general como en un gráfico de evolución mensual, y pueden ser filtrados por un rango de fechas o por tipo de causa para un análisis más específico.
            </p>
            <br/>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium">Fecha inicio</label>
                <input
                  type="date"
                  className="w-full border rounded px-2 py-1"
                  value={fechaInicio}
                  onChange={(e) => setFechaInicio(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Fecha fin</label>
                <input
                  type="date"
                  className="w-full border rounded px-2 py-1"
                  value={fechaFin}
                  onChange={(e) => setFechaFin(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Tipo de causa</label>
                <select
                  className="w-full border rounded px-2 py-1"
                  value={tipo}
                  onChange={(e) => setTipo(e.target.value)}
                >
                  <option value="todos">Todos</option>
                  <option value="contencioso">Contencioso</option>
                  <option value="no contencioso">No contencioso</option>
                </select>
              </div>
            </div>
          
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Días promedio desde audiencia</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-semibold">
                  {diasDesdeAudiencia !== null ? `${diasDesdeAudiencia} días` : "Cargando..."}
                </p>
                <p className="text-muted-foreground mt-2 text-sm">
                  Basado en {causasDesdeAudiencia ?? "…"} causas con audiencia vista o pública y fallo.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Días promedio desde primer trámite</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-semibold">
                  {diasDesdeInicio !== null ? `${diasDesdeInicio} días` : "Cargando..."}
                </p>
                <p className="text-muted-foreground mt-2 text-sm">
                  Basado en {causasDesdeInicio ?? "…"} causas.
                </p>
              </CardContent>
            </Card>
          </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>
                    Evolución mensual: días promedio desde audiencia hasta fallo
                  </CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  <Line data={evolucionAudienciaData} options={{ responsive: true, maintainAspectRatio: false }} />
                </CardContent>
              </Card>

              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>
                    Evolución mensual: días promedio desde inicio hasta fallo
                  </CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  <Line data={evolucionInicioData} options={{ responsive: true, maintainAspectRatio: false }} />
                </CardContent>
              </Card>
            </div>
          </div>
          <Separator />
        </TabsContent>

        <TabsContent value="estado diario" className="space-y-2">
          <br/>
          <p className="text-muted-foreground">
            Esta sección permite monitorear y acceder rápidamente a los trámites realizados durante el día.
          </p>

          <div className="mt-8">
            <h2 className="text-xl font-bold mb-4">Listado completo de trámites del día</h2>
            {tramitesDelDia.length > 0 ? (
              <div className="border rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Carátula</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Referencia</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Link</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {/* Unimos los datos de las causas y los trámites justo antes de renderizar */}
                    {tramitesDelDia.map((tramite, index) => {
                      const causaAsociada = causasDelDia.find(causa => causa.rol === tramite.rol);
                      
                      if (!causaAsociada) return null;

                      return (
                        <tr key={index}>
                          <td className="px-4 py-2 whitespace-nowrap text-xs font-medium text-gray-900">{causaAsociada.rol}</td>
                          {/* AÑADIDO: Clases para truncar y limitar el ancho de la carátula */}
                          <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 max-w-xs truncate">{causaAsociada.descripcion}</td>
                          <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">{tramite.TipoTramite}</td>
                          <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">{tramite.Fecha}</td>
                          <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">{tramite.Referencia}</td>
                          <td className="px-4 py-2 whitespace-nowrap text-xs text-blue-500 hover:underline">
                            {tramite.Link_Descarga && <a href={tramite.Link_Descarga} target="_blank" rel="noopener noreferrer">Descargar</a>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No se encontraron trámites para el día de hoy.</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
