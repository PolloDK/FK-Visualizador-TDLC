"use client";

import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="bg-black px-6 py-4 flex justify-between items-center shadow-md">
      <div className="flex items-center space-x-3">
        <Image src="/logo_fk.png" alt="FK Logo" width={36} height={36} />
      </div>
      <div className="space-x-6">
        <Link href="/" className="text-white hover:text-blue-400">Inicio</Link>
        <Link href="/pages/dashboard" className="text-white hover:text-blue-400">Dashboard</Link>
        <Link href="/pages/calendar" className="text-white hover:text-blue-400">Calendario</Link>
      </div>
    </nav>
  );
}
