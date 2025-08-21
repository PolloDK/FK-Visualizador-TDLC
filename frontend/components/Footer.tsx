"use client";

import Image from "next/image";
import { FaLinkedin, FaGlobeAmericas } from "react-icons/fa";

export default function Footer() {
  return (
    <footer className="bg-[#2f2f2f] text-gray-300 py-10 px-6 md:px-12 mt-10">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-6">

        {/* Logo FK */}
        <div className="flex-shrink-0">
          <Image
            src="/logo_fk.png"  // Asegúrate que esté en public/
            alt="FK Economics"
            width={100}
            height={100}
            className="h-auto w-auto"
          />
        </div>

        {/* Texto e íconos */}
        <div className="flex-1">
          <p className="text-base mb-2 font-semibold text-gray-300">
            Visualizador TDLC by FK Economics © 2025
          </p>

          <div className="flex flex-col gap-2 mb-3">
            <a
              href="https://www.linkedin.com/company/fkeconomics"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 hover:text-blue-400 transition-colors"
            >
              <FaLinkedin size={18} />
              <span>LinkedIn FK</span>
            </a>
            <a
              href="https://www.fkeconomics.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 hover:text-blue-400 transition-colors"
            >
              <FaGlobeAmericas size={18} />
              <span>Página Web FK</span>
            </a>
          </div>

          <p className="text-sm text-gray-400">
            Desarrollado por el equipo de FK Economics
          </p>
        </div>
      </div>
    </footer>
  );
}
