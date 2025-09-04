// utils/formatCombinedReclamacionesData.ts

import { ChartData } from "chart.js";
import {ReclamacionesTrimestralesStats} from "@/types/interfaces";

export function formatCombinedReclamacionesData(
  data: ReclamacionesTrimestralesStats[]
): ChartData<"bar" | "line", number[], string> {
  return {
    labels: data.map((item) => item.trimestre),
    datasets: [
      {
        type: "line",
        label: "Total de Causas",
        data: data.map((item) => item.total_causas),
        borderColor: "#3399FF",
        backgroundColor: "#3399FF",
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        yAxisID: "y",
      },
      {
        type: "line",
        label: "Total de Reclamaciones",
        data: data.map((item) => item.total_reclamaciones),
        borderColor: "#FF6699",
        backgroundColor: "#FF6699",
        borderWidth: 2,
        fill: false,
        tension: 0.3,
        yAxisID: "y",
      },
      {
        type: "bar",
        label: "Revocadas",
        data: data.map((item) => item.revocadas),
        backgroundColor: "#56C1B1",
        yAxisID: "y",
      },
      {
        type: "bar",
        label: "Revocadas Parcialmente",
        data: data.map((item) => item.revocadas_parcialmente),
        backgroundColor: "#F7A541",
        yAxisID: "y",
      },
    ],
  };
}
