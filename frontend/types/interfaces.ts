// src/types/interfaces.ts

// Interfaz para la data del gráfico de Chart.js
export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    tension?: number;
    type?: 'line' | 'bar' | 'pie';
    yAxisID?: string;
    stack?: string;
  }[];
}


// Interfaz para el componente AwaitingFalloCard
export type AwaitingFallo = {
  rol: string;
  caratula: string;
  link: string;
  dias_desde_audiencia: number;
  fecha_audiencia: string;
  dias_estimados_restantes: number;
};

// Interfaz para los trámites del día
export interface TramiteDelDia {
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

// Interfaz para las causas del día
export interface CausaDelDia {
  fecha_estado_diario: string;
  rol: string;
  descripcion: string;
  tramites: number;
  link: string;
}

// Interfaz para los datos trimestrales de reclamaciones
export interface ReclamacionesTrimestralesStats {
  trimestre: string;
  total_causas: number;
  total_reclamaciones: number;
  revocadas: number;
  revocadas_parcialmente: number;
  confirma: number;
  conciliacion: number;
  avenimiento: number;
  no_reclamacion: number;
  pendiente: number;
}

// Interfaz para el estado completo del dashboard
export interface DashboardData {
  promedioAudiencia: number | null;
  promedioInicio: number | null;
  diasDesdeAudiencia: number | null;
  causasDesdeAudiencia: number | null;
  diasDesdeInicio: number | null;
  causasDesdeInicio: number | null;
  esperandoFallo: AwaitingFallo[];
  evolucionAudienciaData: ChartData;
  evolucionInicioData: ChartData;
  totalCausas: number | null;
  totalCausasConFallo: number | null;
  causasDelDia: CausaDelDia[];
  tramitesDelDia: TramiteDelDia[];
  promedioTrimestralAudiencia: ChartData;
  promedioTrimestralInicio: ChartData;
  reclamacionesStats?: ReclamacionesStats | null;
  reclamacionesTrimestralesStats: ReclamacionesTrimestralesStats[];
}

export interface ReclamacionesStats {
  total_causas_periodo: number;
  total_reclamaciones: number;
  revocadas: number;
  revocadas_parcialmente: number;
  confirmadas: number;
  no_se_interpusieron_recursos: number;
  anula_de_oficio: number;
  conciliacion: number;
  avenimiento: number;
  desistimiento: number;
  total_confirmadas_o_otras: number;
  porcentaje_revocadas: number;
}