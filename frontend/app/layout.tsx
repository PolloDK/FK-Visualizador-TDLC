import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "../components/Navbar";
import { ReactNode } from "react";

// Carga de fuentes
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Metadata para SEO
export const metadata: Metadata = {
  title: "Visualizador TDLC",
  description: "Explora sentencias y estadísticas del Tribunal de Defensa de la Libre Competencia",
};

// Tipado explícito para las props del layout
interface RootLayoutProps {
  children: ReactNode;
}

// Componente principal de layout
export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="es">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Navbar />
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
