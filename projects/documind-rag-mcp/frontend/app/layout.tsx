import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind — Evidence-grounded document intelligence",
  description: "Ask PDF questions with inspectable evidence and validated citations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
