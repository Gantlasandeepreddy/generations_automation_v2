import type { Metadata } from 'next'
import './globals.css'
import SessionProvider from '../components/SessionProvider'

export const metadata: Metadata = {
  title: 'Generations Automation Tool',
  description: 'Automated client notes extraction from Generations IDB system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  )
}
