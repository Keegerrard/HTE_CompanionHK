import type { Metadata } from "next";
import { Nunito, Nunito_Sans } from "next/font/google";
import { WeatherProvider } from "@/components/weather-provider";
import "./globals.css";

const nunito = Nunito({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
  weight: ["400", "600", "700"],
});

const nunitoSans = Nunito_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "港伴AI — CompanionHK",
  description:
    "Your warm AI companion for Hong Kong: emotional support, local guidance, and study help.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${nunito.variable} ${nunitoSans.variable}`}>
      <body>
        <WeatherProvider>{children}</WeatherProvider>
      </body>
    </html>
  );
}
