import type { Metadata } from "next";
import { ChatKitScripts } from "@/components/ChatKitScripts";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentKit demo",
  description: "Demo of ChatKit with hosted workflow",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ChatKitScripts />
        {children}
      </body>
    </html>
  );
}
