"use client";

import {
  createContext,
  useContext,
} from "react";
import {
  ThemeProvider as NextThemeProvider,
  useTheme as useNextTheme,
  type ThemeProviderProps,
} from "next-themes";

interface ThemeContextValue {
  theme: string | undefined;
  resolvedTheme: string | undefined;
  setTheme: (theme: string) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({
  children,
  ...props
}: Partial<ThemeProviderProps> & { children: React.ReactNode }) {
  return (
    <NextThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      storageKey="leadradar-theme"
      {...props}
    >
      {children}
    </NextThemeProvider>
  );
}

export function useTheme() {
  const nextTheme = useNextTheme();
  const ctx = useContext(ThemeContext);
  return ctx ?? nextTheme;
}
