"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useDashboardData } from "@/hooks/useDashboardData";
import { ScrollArea } from "@/components/ui/scroll-area";
import TramitesTable from '@/components/TramitesTable';
import { Bar, Chart, Line } from "react-chartjs-2";
import { formatCombinedReclamacionesData } from "@/types/formatCombinedReclamacionesData";
import { ChevronDown, ChevronUp, Bell, FileText, CheckCircle } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  ChartData as ChartJSData
} from "chart.js";
import { ReclamacionesTrimestralesStats } from "@/types/interfaces";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend);

export default function DashboardPage() {
  const [fechaInicio, setFechaInicio] = useState("2022-01-01");
  const [fechaFin, setFechaFin] = useState("2025-12-31");
  const [tipo, setTipo] = useState("todos");
  const [expandedCausa, setExpandedCausa] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("resumen");

  const { data, loading, error } = useDashboardData(fechaInicio, fechaFin, tipo);
  console.log("📊 Datos crudos:", data.reclamacionesTrimestralesStats);

  const toggleExpanded = (rol: string) => {
    setExpandedCausa(expandedCausa === rol ? null : rol);
  };
  
  const renderContent = (content: React.ReactNode) => {
    if (loading) {
      return <div className="text-center py-8 text-gray-500">Cargando...</div>;
    }
    if (error) {
      return <div className="text-center py-8 text-red-500">Error: No se pudo cargar la información.</div>;
    }
    return content;
  };

  return (
    <div className="p-2 space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Métricas del TDLC</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
          <TabsTrigger value="analitica">Analítica</TabsTrigger>
          <TabsTrigger value="estado diario">Estado Diario</TabsTrigger>
        </TabsList>

        <TabsContent value="resumen" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Duración promedio de redacción de fallo</CardTitle>
              </CardHeader>
              <CardContent>
                {renderContent(
                  <p className="text-4xl font-semibold">
                    {data.promedioAudiencia !== null
                      ? `${data.promedioAudiencia.toString().replace(".", ",")} días`
                      : "Cargando..."}
                  </p>
                )}
                <p className="text-muted-foreground mt-2 text-sm">
                  Basado en todas las causas desde la audiencia.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Duración promedio desde el primer trámite</CardTitle>
              </CardHeader>
              <CardContent>
                {renderContent(
                  <p className="text-4xl font-semibold">
                    {data.promedioInicio !== null
                      ? `${data.promedioInicio.toString().replace(".", ",")} días`
                      : "Cargando..."}
                  </p>
                )}
                <p className="text-muted-foreground mt-2 text-sm">
                  Considerando todas las causas que terminan con sentencia o resolución.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Total de Causas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {renderContent(
                  <div>
                    <p className="text-4xl font-semibold">
                      {data.totalCausasConFallo !== null
                        ? `${data.totalCausasConFallo.toString().replace(".", ",")} con fallo`
                        : "Cargando..."}
                    </p>
                    <p className="text-muted-foreground mt-2 text-sm">
                      {data.totalCausas !== null
                        ? `de un total de ${data.totalCausas.toString().replace(".", ",")} causas detectadas`
                        : ""}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            <Card className="relative">
              <CardHeader>
                <CardTitle>Causas en período de fallo tdlc</CardTitle>
                  <p className="text-muted-foreground mt-2 text-sm">
                    El estimado toma en consideración el promedio de duración de redacción de fallos para las causas Contenciosas y las No contenciosas.
                    Al hacer click en la tarjeta de cada causa, podrás visitar directamente el expediente de la causa en el sitio web del TDLC.
                  </p>
              </CardHeader>
              <CardContent className="p-0">
                {renderContent(
                  <ScrollArea className="max-h-[580px] overflow-y-auto px-4 pb-4">
                    <div className="space-y-3 py-2">
                      {Array.isArray(data.esperandoFallo) && data.esperandoFallo.length > 0 ? (
                        data.esperandoFallo
                          .sort((a, b) => b.dias_desde_audiencia - a.dias_desde_audiencia)
                          .map((causa, index) => {
                            const diferencia = causa.dias_estimados_restantes;
                            const claseColor =
                              diferencia < -30
                                ? "bg-red-600 hover:bg-red-700"
                                : diferencia >= -30 && diferencia <= 30
                                ? "bg-yellow-500 hover:bg-yellow-600"
                                : "bg-green-600 hover:bg-green-700";

                            return (
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
                                    <div className={`${claseColor} text-white text-sm px-2 py-1 rounded-full min-w-[90px] text-center`}>
                                      Estimado: {diferencia < 0 ? diferencia : `+${diferencia}`} días
                                    </div>
                                  </div>
                                </div>
                              </a>
                            );
                          })
                      ) : (
                        <p className="text-muted-foreground text-sm px-4 py-2">No hay causas esperando fallo.</p>
                      )}
                    </div>
                  </ScrollArea>
                )}
                <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-background to-transparent" />
              </CardContent>
            </Card>

            <Card className="relative">
              <CardHeader>
                <CardTitle>Causas en período de fallo CS</CardTitle>
                  <p className="text-muted-foreground mt-2 text-sm">
                    El estimado toma en consideración el promedio de duración de redacción de fallos para las causas Contenciosas y las No contenciosas.
                    Al hacer click en la tarjeta de cada causa, podrás visitar directamente el expediente de la causa en el sitio web de la CS.
                  </p>
              </CardHeader>
            </Card>
          </div>
          <Separator />
        </TabsContent>

        <TabsContent value="analitica" className="space-y-6">
          <div className="space-y-3">
            <br />
            <h2 className="text-2xl font-semibold">Análisis de causas</h2>
            <br />
            <p className="text-muted-foreground">
              Esta sección permite monitorear la evolución de los tiempos de resolución de causas en el TDLC. Utiliza la fecha del primer trámite (`fecha_primer_tramite`) como punto de referencia para calcular el promedio de días que toma una causa en resolverse, ya sea desde la fecha de su última audiencia pública ( o causa de la vista) o desde la fecha de su primer trámite. Los resultados se presentan tanto en un promedio general como en un gráfico de evolución trimestral, y pueden ser filtrados por un rango de fechas o por tipo de causa para un análisis más específico.
            </p>
            <br />
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
          </div>
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Días promedio desde audiencia</CardTitle>
                </CardHeader>
                <CardContent>
                  {renderContent(
                    <p className="text-4xl font-semibold">
                      {data.diasDesdeAudiencia !== null ? `${data.diasDesdeAudiencia} días` : "Cargando..."}
                    </p>
                  )}
                  <p className="text-muted-foreground mt-2 text-sm">
                    Basado en {data.causasDesdeAudiencia ?? "…"} causas con audiencia vista o pública y fallo.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Días promedio desde primer trámite</CardTitle>
                </CardHeader>
                <CardContent>
                  {renderContent(
                    <p className="text-4xl font-semibold">
                      {data.diasDesdeInicio !== null ? `${data.diasDesdeInicio} días` : "Cargando..."}
                    </p>
                  )}
                  <p className="text-muted-foreground mt-2 text-sm">
                    Basado en {data.causasDesdeInicio ?? "…"} causas.
                  </p>
                </CardContent>
              </Card>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>Días desde la audiencia hasta el fallo por causa</CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  {renderContent(
                    <Bar
                      data={data.evolucionAudienciaData as ChartJSData<"bar", number[], string>}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          x: {
                            ticks: {
                              color: "#4d4d4d",
                              font: { size: 10 }
                            }
                          }
                        }
                      }}
                    />
                  )}
                </CardContent>
              </Card>
              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>Días desde inicio de expediente hasta el fallo por causa</CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  {renderContent(
                    <Bar
                      data={data.evolucionInicioData as ChartJSData<"bar", number[], string>}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          x: {
                            ticks: {
                              color: "#4d4d4d",
                              font: { size: 10 }
                            }
                          }
                        }
                      }}
                    />
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>Promedio trimestral: días desde la audiencia hasta el fallo</CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  {renderContent(
                    <Line
                      data={data.promedioTrimestralAudiencia as ChartJSData<"line", number[], string>}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          x: {
                            ticks: {
                              color: "#4d4d4d",
                              font: { size: 10 }
                            }
                          }
                        }
                      }}
                    />
                  )}
                </CardContent>
              </Card>
              <Card className="h-[400px]">
                <CardHeader>
                  <CardTitle>Promedio trimestral: días desde el inicio al fallo</CardTitle>
                </CardHeader>
                <CardContent className="h-full">
                  {renderContent(
                    <Line
                      data={data.promedioTrimestralInicio as ChartJSData<"line", number[], string>}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          x: {
                            ticks: {
                              color: "#4d4d4d",
                              font: { size: 10 }
                            }
                          }
                        }
                      }}
                    />
                  )}
                </CardContent>
              </Card>
            </div>

          <Separator />
          <br />
            <h2 className="text-2xl font-semibold">Reclamaciones después del Fallo</h2>
          <br />
            <p className="text-muted-foreground">
              Esta sección identifica las reclamaciones presentadas tras la emisión de fallos en causas y permite monitorear los estados de dichas reclamaciones. Se presentan estadísticas clave como el número total de reclamaciones, cuántas han sido revocadas total o parcialmente, y el porcentaje correspondiente.
            </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Total causas</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-bold">
              {data.reclamacionesStats?.total_causas_periodo ?? "-"}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Total reclamaciones</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-bold">
              {data.reclamacionesStats?.total_reclamaciones ?? "-"}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Reclamaciones revocadas</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-bold">
              {data.reclamacionesStats?.revocadas ?? "-"}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revocadas parcialmente</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-bold">
              {data.reclamacionesStats?.revocadas_parcialmente ?? "-"}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>% Revocadas</CardTitle>
            </CardHeader>
            <CardContent className="text-2xl font-bold">
              {(data.reclamacionesStats?.porcentaje_revocadas ?? 0).toLocaleString("es-CL", {
                style: "percent",
                minimumFractionDigits: 1,
                maximumFractionDigits: 1,
              })}
            </CardContent>
          </Card>
        </div>
        <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-1 mt-8">
          <Card className="h-[400px]">
            <CardHeader>
              <CardTitle>
                Evolución Trimestral: Causas, Reclamaciones y Revocaciones
              </CardTitle>
            </CardHeader>
            <CardContent className="h-full">
              {renderContent(
                <Chart<"bar" | "line", number[], string>
                  type="bar"
                  data={formatCombinedReclamacionesData(data.reclamacionesTrimestralesStats)}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      x: {
                        stacked: false,
                        title: { display: true, text: "Trimestre" },
                        ticks: { color: "#4d4d4d", font: { size: 10 } }
                      },
                      y: {
                        stacked: false,
                        beginAtZero: true,
                        title: { display: true, text: "Cantidad de Casos" },
                        ticks: { color: "#4d4d4d" }
                      }
                    },
                    plugins: {
                      legend: {
                        labels: {
                          boxWidth: 12,
                          usePointStyle: true
                        }
                      }
                    }
                  }}
                />
              )}
            </CardContent>
          </Card>
        </div>

        </TabsContent>
        <TabsContent value="estado diario" className="space-y-2">
          <br />
          <p className="text-muted-foreground">
            Esta sección permite monitorear y acceder rápidamente a los trámites realizados durante el día.
          </p>
          {renderContent(
            <div className="mt-8">
              <h2 className="text-xl font-bold mb-4">Listado completo de trámites del día</h2>
              {data.tramitesDelDia && data.tramitesDelDia.length > 0 ? (
                <TramitesTable
                  tramitesDelDia={data.tramitesDelDia}
                  causasDelDia={data.causasDelDia}
                />
              ) : (
                <p>No se encontraron trámites para el día de hoy.</p>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}