import type { Metadata } from "next";
import "./globals.css";
import { PortStoreProvider } from "./hooks/usePortStore";

export const metadata: Metadata = {
  title: "Supply Chain Risk Dashboard",
  description: "Real-time port risk monitoring",
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
