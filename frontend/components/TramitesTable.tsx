import React from 'react';

// Interfaz para cada trámite
interface Tramite {
  idCausa: string;
  rol: string;
  TipoTramite: string;
  Fecha: string;
  Referencia: string;
  Foja: string;
  Link_Descarga?: string;
  Tiene_Detalles?: string;
  Tiene_Firmantes?: string;
}

// Interfaz para la causa del día
interface Causa {
  rol: string;
  descripcion: string;
}

// Props del componente
interface TramitesTableProps {
  tramitesDelDia: Tramite[];
  causasDelDia: Causa[];
}

const TramitesTable: React.FC<TramitesTableProps> = ({ tramitesDelDia, causasDelDia }) => {
  // Crear mapa rol → causa
  const causasMap = causasDelDia.reduce((map, causa) => {
    map[causa.rol] = causa;
    return map;
  }, {} as { [key: string]: Causa });

  if (!tramitesDelDia || tramitesDelDia.length === 0) {
    return <p>No se encontraron trámites para el día de hoy.</p>;
  }

  return (
    <div className="border rounded-lg overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Carátula</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Referencia</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Link</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {tramitesDelDia.map((tramite, index) => {
            const causaAsociada = causasMap[tramite.rol];
            const descripcion = causaAsociada?.descripcion ?? "(sin carátula)";
            const linkFinal = tramite.Link_Descarga || `https://consultas.tdlc.cl/estadoDiario?idCausa=${tramite.idCausa}`;

            return (
              <tr key={index}>
                <td className="px-4 py-2 whitespace-nowrap text-xs font-medium text-gray-900">{tramite.rol}</td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 max-w-xs truncate">{descripcion}</td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">{tramite.TipoTramite}</td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500">{tramite.Fecha}</td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-gray-500 max-w-xs truncate">{tramite.Referencia}</td>
                <td className="px-4 py-2 whitespace-nowrap text-xs text-blue-500 hover:underline">
                  <a href={linkFinal} target="_blank" rel="noopener noreferrer">
                    Ver causa
                  </a>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default TramitesTable;
