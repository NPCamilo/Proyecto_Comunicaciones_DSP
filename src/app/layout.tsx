import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

const clashDisplay = localFont({
  src: "./fonts/ClashDisplay-Variable.woff2",
  variable: "--font-clash-display",
  display: "swap",
  weight: "200 700",
});

const satoshi = localFont({
  src: "./fonts/Satoshi-Variable.woff2",
  variable: "--font-satoshi",
  display: "swap",
  weight: "300 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMono-Variable.woff2",
  variable: "--font-geist-mono",
  display: "swap",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Cadena Integral de Audio DSP · UTP",
  description:
    "Plataforma interactiva de procesamiento, modulación analógica/digital, demodulación y reconstrucción DAC de señales de audio.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#09090b",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`dark ${clashDisplay.variable} ${satoshi.variable} ${geistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-(--canvas) text-(--ink) antialiased selection:bg-sky-500/20 selection:text-sky-500">
        {children}
      </body>
    </html>
  );
}
