"use client";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import { Inter } from "next/font/google";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const inter = Inter({ subsets: ["latin"] });

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
        isActive
          ? "bg-accent/20 text-accent shadow-[0_0_8px_rgba(59,130,246,0.3)]"
          : "text-text-secondary hover:text-text-primary hover:bg-white/[0.05]"
      }`}
    >
      {children}
    </Link>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  return (
    <html lang="en" className={inter.className}>
      <head>
        <title>Healthcare Dearth Map</title>
        <meta
          name="description"
          content="Interactive map visualizing healthcare provider shortages across US counties"
        />
      </head>
      <body className="min-h-screen flex flex-col">
        <QueryClientProvider client={queryClient}>
          <nav className="fixed top-0 left-0 right-0 z-50 h-10 bg-surface-800/90 backdrop-blur-md border-b border-white/[0.06] flex items-center px-4">
            <Link href="/" className="flex items-center gap-2 mr-6">
              <svg
                className="w-5 h-5 text-accent"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 21c-4.97-4.97-8-8.03-8-11a8 8 0 1116 0c0 2.97-3.03 6.03-8 11z"
                />
                <circle cx="12" cy="10" r="2.5" fill="currentColor" />
              </svg>
              <span className="text-sm font-semibold text-text-primary tracking-tight">
                Healthcare Dearth Map
              </span>
            </Link>
            <div className="flex gap-1">
              <NavLink href="/">Map</NavLink>
              <NavLink href="/table">Table</NavLink>
              <NavLink href="/about">About</NavLink>
            </div>
          </nav>
          <main className="pt-10 flex-1">{children}</main>
        </QueryClientProvider>
      </body>
    </html>
  );
}
