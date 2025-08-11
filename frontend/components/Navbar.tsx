"use client"; // si estás usando app router

import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="bg-white shadow-md px-6 py-4 flex justify-between items-center">
      <div className="text-xl font-bold text-gray-800">
        Visualizador TDLC
      </div>
      <div className="space-x-4">
        <Link href="/" className="text-gray-700 hover:text-blue-600">Inicio</Link>
        <Link href="/calendar" className="text-gray-700 hover:text-blue-600">Sentencias</Link>
        <Link href="/estadisticas" className="text-gray-700 hover:text-blue-600">Estadísticas</Link>
        <Link href="/acerca" className="text-gray-700 hover:text-blue-600">Acerca de</Link>
      </div>
    </nav>
  );
}
