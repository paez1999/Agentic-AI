import type { Metadata } from "next";
import "./globals.css";
import { PortStoreProvider } from "./hooks/usePortStore";

export const metadata: Metadata = {
  title: "ShieldStock — Risk Monitoring",
  description: "Real-time supply chain risk monitoring",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <PortStoreProvider>{children}</PortStoreProvider>
      </body>
    </html>
  );
}
