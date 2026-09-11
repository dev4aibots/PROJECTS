import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:{default:'ClientFlow — Studio North',template:'%s | ClientFlow'},description:'A focused project workspace for small agencies. Explicit, credential-free portfolio demo.'};
export default function RootLayout({children}: Readonly<{children:React.ReactNode}>) {return <html lang="en"><body><a className="skip-link" href="#main-content">Skip to main content</a>{children}</body></html>;}
