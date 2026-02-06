"use client";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

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
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? "bg-blue-700 text-white"
          : "text-blue-100 hover:bg-blue-600 hover:text-white"
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
    <html lang="en">
      <head>
        <title>Healthcare Dearth Map</title>
        <meta
          name="description"
          content="Interactive map visualizing healthcare provider shortages across US counties"
        />
      </head>
      <body className="min-h-screen flex flex-col">
        <QueryClientProvider client={queryClient}>
          <nav className="bg-blue-800 text-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-14">
                <Link href="/" className="text-lg font-bold tracking-tight">
                  Healthcare Dearth Map
                </Link>
                <div className="flex gap-1">
                  <NavLink href="/">Map</NavLink>
                  <NavLink href="/table">Table</NavLink>
                  <NavLink href="/about">About</NavLink>
                </div>
              </div>
            </div>
          </nav>
          <main className="flex-1">{children}</main>
        </QueryClientProvider>
      </body>
    </html>
  );
}
