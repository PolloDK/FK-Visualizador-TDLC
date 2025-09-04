import { useEffect, useState } from "react";
// Importa las interfaces desde el nuevo archivo
import {
  AwaitingFallo,
  CausaDelDia,
  TramiteDelDia,
  ChartData,
  DashboardData,
  ReclamacionesStats,
  // --- AÑADE LA INTERFACE PARA LOS DATOS TRIMESTRALES DE RECLAMACIONES ---
  ReclamacionesTrimestralesStats
} from "@/types/interfaces";

const API_BASE_URL = "http://localhost:8000";

const formatDateToDDMMYYYY = (dateString: string) => {
  const [year, month, day] = dateString.split("-");
  return `${day}-${month}-${year}`;
};

const processResponse = async (response: Response) => {
  if (!response.ok) {
    console.error(`Error en la respuesta de la API: ${response.status} ${response.statusText}`);
    return [];
  }
  const data = await response.json();
  return Array.isArray(data) ? data : [];
};

const formatDataByRol = (data: any, label: string): ChartData => {
  if (!Array.isArray(data)) return { labels: [], datasets: [] };
  const sorted = [...data].sort(
    (a, b) => new Date(a.fecha_primer_tramite).getTime() - new Date(b.fecha_primer_tramite).getTime()
  );
  return {
    labels: sorted.map((item) => item.rol),
    datasets: [{
      label,
      data: sorted.map((item) => item.dias),
      borderColor: "rgb(75, 192, 192)",
      backgroundColor: "rgba(75, 192, 192, 1)",
      tension: 0.1,
    }],
  };
};

const formatTrimestralData = (data: any, label: string): ChartData => {
  if (!Array.isArray(data)) return { labels: [], datasets: [] };
  return {
    labels: data.map(item => item.trimestre),
    datasets: [{
      label,
      data: data.map(item => parseFloat(item.dias.toFixed(2))),
      borderColor: "rgb(255, 99, 132)",
      backgroundColor: "rgba(255, 99, 132, 0.5)",
      tension: 0.1,
    }],
  };
};

export function useDashboardData(fechaInicio: string, fechaFin: string, tipo: string) {
  const [data, setData] = useState<DashboardData>({
    promedioAudiencia: null,
    promedioInicio: null,
    diasDesdeAudiencia: null,
    causasDesdeAudiencia: null,
    diasDesdeInicio: null,
    causasDesdeInicio: null,
    esperandoFallo: [],
    evolucionAudienciaData: { labels: [], datasets: [] },
    evolucionInicioData: { labels: [], datasets: [] },
    totalCausas: null,
    totalCausasConFallo: null,
    causasDelDia: [],
    tramitesDelDia: [],
    promedioTrimestralAudiencia: { labels: [], datasets: [] },
    promedioTrimestralInicio: { labels: [], datasets: [] },
    reclamacionesStats: undefined,
    // --- NUEVO CAMPO PARA LOS DATOS TRIMESTRALES ---
    reclamacionesTrimestralesStats: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!fechaInicio || !fechaFin || fechaInicio.length !== 10 || fechaFin.length !== 10) {
        console.warn("⏳ Esperando fechas válidas para llamar a la API...");
        return;
      }
      setLoading(true);
      try {
        const params = `fecha_inicio=${formatDateToDDMMYYYY(fechaInicio)}&fecha_fin=${formatDateToDDMMYYYY(fechaFin)}&tipo=${tipo}`;

        const [
          audienciageneralRes, tramitegeneralRes, audienciaRes, tramiteRes,
          esperandoRes, evolucionAudienciaRes, evolucionInicioRes,
          promedioTrimestralAudienciaRes, promedioTrimestralInicioRes,
          totalCausasRes, causasDelDiaRes, tramitesDelDiaRes,
          reclamacionesStatsRes,
          // --- NUEVA LLAMADA A LA API ---
          reclamacionesTrimestralesRes
        ] = await Promise.all([
          fetch(`${API_BASE_URL}/causas/promedio-dias-audiencia-general`),
          fetch(`${API_BASE_URL}/causas/promedio-dias-inicio-general`),
          fetch(`${API_BASE_URL}/causas/promedio-dias-fallo?${params}`),
          fetch(`${API_BASE_URL}/causas/promedio-dias-desde-primer-tramite?${params}`),
          fetch(`${API_BASE_URL}/causas/causas-esperando-fallo`),
          fetch(`${API_BASE_URL}/causas/evolucion-diaria-audiencia?${params}`),
          fetch(`${API_BASE_URL}/causas/evolucion-diaria-inicio?${params}`),
          fetch(`${API_BASE_URL}/causas/promedio-trimestral-audiencia?${params}`),
          fetch(`${API_BASE_URL}/causas/promedio-trimestral-inicio?${params}`),
          fetch(`${API_BASE_URL}/causas/total-causas`),
          fetch(`${API_BASE_URL}/estado-diario/causas-del-dia`),
          fetch(`${API_BASE_URL}/estado-diario/tramites-del-dia`),
          fetch(`${API_BASE_URL}/causas/reclamaciones/porcentaje-revocadas?${params}`),
          // --- NUEVA LLAMADA A LA API ---
          fetch(`${API_BASE_URL}/causas/reclamaciones/revocaciones-trimestrales?${params}`)
        ]);

        const [
          promedioAudiencia, promedioInicio, audienciaData, tramiteData,
          esperandoData, evolucionAudiencia, evolucionInicio,
          promedioTrimestralAudiencia, promedioTrimestralInicio,
          totalCausas, causasDelDia, tramitesDelDia,
          reclamacionesStats,
          // --- NUEVO DATO OBTENIDO ---
          reclamacionesTrimestralesData
        ] = await Promise.all([
          audienciageneralRes.json(), tramitegeneralRes.json(), audienciaRes.json(), tramiteRes.json(),
          esperandoRes.json(), evolucionAudienciaRes.json(), evolucionInicioRes.json(),
          processResponse(promedioTrimestralAudienciaRes), processResponse(promedioTrimestralInicioRes),
          totalCausasRes.json(), causasDelDiaRes.json(), tramitesDelDiaRes.json(),
          reclamacionesStatsRes.json(),
          // --- PROCESA EL NUEVO DATO ---
          processResponse(reclamacionesTrimestralesRes)
        ]);

        setData({
          promedioAudiencia: promedioAudiencia.promedio_dias,
          promedioInicio: promedioInicio.promedio_dias,
          diasDesdeAudiencia: audienciaData.promedio_dias,
          causasDesdeAudiencia: audienciaData.n_causas,
          diasDesdeInicio: tramiteData.promedio_dias,
          causasDesdeInicio: tramiteData.n_causas,
          esperandoFallo: Array.isArray(esperandoData) ? esperandoData : [],
          evolucionAudienciaData: formatDataByRol(evolucionAudiencia, "Desde audiencia"),
          evolucionInicioData: formatDataByRol(evolucionInicio, "Desde inicio"),
          totalCausas: totalCausas.total_causas,
          totalCausasConFallo: totalCausas.total_con_fallo,
          causasDelDia: Array.isArray(causasDelDia.causas_del_dia) ? causasDelDia.causas_del_dia : [],
          tramitesDelDia: Array.isArray(tramitesDelDia) ? tramitesDelDia : [],
          promedioTrimestralAudiencia: formatTrimestralData(promedioTrimestralAudiencia, "Promedio trimestral desde audiencia"),
          promedioTrimestralInicio: formatTrimestralData(promedioTrimestralInicio, "Promedio trimestral desde inicio"),
          reclamacionesStats: reclamacionesStats,
          // --- GUARDA EL NUEVO DATO EN EL ESTADO ---
          reclamacionesTrimestralesStats: reclamacionesTrimestralesData
        });

      } catch (err) {
        setError("Error al obtener datos del dashboard.");
        console.error("Error al obtener métricas del dashboard:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [fechaInicio, fechaFin, tipo]);

  return { data, loading, error };
}