import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";

import Home from "./components/Home";
import { FileManagementPage } from "./components/FileManagementPage";
import { useColorScheme } from "./hooks/useColorScheme";
import logoHolson from "./assets/Logo_Holson_la-performance-des-flottes_Coul_3.avif";

function AppContent() {
  const { scheme } = useColorScheme();
  const location = useLocation();

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-brand-primary/20 bg-white/90 backdrop-blur-sm dark:border-brand-primary/30 dark:bg-[#14243b]/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-3">
              <img
                src={logoHolson}
                alt="Holson"
                className="h-10 w-auto"
              />
            </Link>
            <div className="flex gap-6">
              <Link
                to="/"
                className={`text-base font-semibold transition-colors ${
                  location.pathname === "/"
                    ? "text-brand-link dark:text-brand-primary"
                    : "text-brand-text/70 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary"
                }`}
              >
                Chat
              </Link>
              <Link
                to="/files"
                className={`text-base font-semibold transition-colors ${
                  location.pathname === "/files"
                    ? "text-brand-link dark:text-brand-primary"
                    : "text-brand-text/70 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary"
                }`}
              >
                Files
              </Link>
            </div>
          </div>
        </div>
      </nav>
      <Routes>
        <Route
          path="/"
          element={<Home scheme={scheme} />}
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

