import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
  message: string;
  timestamp: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/health/`)
      .then(async (response) => {
        if (!response.ok) throw new Error(`API returned HTTP ${response.status}`);
        return (await response.json()) as HealthResponse;
      })
      .then(setHealth)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Could not reach the API");
      });
  }, []);

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand-mark">MCS</div>
        <div>
          <strong>Mahi-Tech Platform</strong>
          <span>Business Management System</span>
        </div>
      </header>

      <section className="hero">
        <p className="eyebrow">STAGE 1 · PROJECT FOUNDATION</p>
        <h1>Your Vision. Our Technology.</h1>
        <p className="intro">
          The new foundation for managing leads, clients, projects, proposals,
          invoices, finances and client communication.
        </p>
        <div className="status-card">
          <h2>Backend API connection</h2>
          {health && (
            <p className="success">
              Connected: {health.service} · {health.message}
            </p>
          )}
          {error && <p className="error">Not connected: {error}</p>}
          {!health && !error && <p>Checking backend connection…</p>}
          <small>API endpoint: {API_BASE_URL}/health/</small>
        </div>
      </section>
      <footer>Internal agency platform · Foundation build</footer>
    </main>
  );
}
