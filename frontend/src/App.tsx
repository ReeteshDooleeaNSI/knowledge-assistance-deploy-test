import { useCallback } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";

import Home from "./components/Home";
import { FileManagementPage } from "./components/FileManagementPage";
import { useColorScheme, type ColorScheme } from "./hooks/useColorScheme";

function AppContent() {
  const { scheme, setScheme } = useColorScheme();
  const location = useLocation();

  const handleThemeChange = useCallback(
    (value: ColorScheme) => {
      setScheme(value);
    },
    [setScheme],
  );

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-brand-primary/20 bg-white/90 backdrop-blur-sm dark:border-brand-primary/30 dark:bg-[#14243b]/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex gap-6">
            <Link
              to="/"
              className={`text-sm font-semibold transition-colors ${
                location.pathname === "/"
                  ? "text-brand-link dark:text-brand-primary"
                  : "text-brand-text/70 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary"
              }`}
            >
              Chat
            </Link>
            <Link
              to="/files"
              className={`text-sm font-semibold transition-colors ${
                location.pathname === "/files"
                  ? "text-brand-link dark:text-brand-primary"
                  : "text-brand-text/70 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary"
              }`}
            >
              Files
            </Link>
          </div>
        </div>
      </nav>
      <Routes>
        <Route
          path="/"
          element={<Home scheme={scheme} onThemeChange={handleThemeChange} />}
        />
        <Route
          path="/files"
          element={<FileManagementPage scheme={scheme} />}
        />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

