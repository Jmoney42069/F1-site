import './globals.css'

export const metadata = {
  title: 'F1 — Engineering Perfection',
  description: 'Formula 1 car assembly sequence',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
