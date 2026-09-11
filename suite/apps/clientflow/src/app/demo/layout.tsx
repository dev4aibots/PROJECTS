import { DemoProvider } from '@/components/demo-provider';
import { AppShell } from '@/components/app-shell';
export default function DemoLayout({children}: {children:React.ReactNode}) {return <DemoProvider><AppShell>{children}</AppShell></DemoProvider>;}
