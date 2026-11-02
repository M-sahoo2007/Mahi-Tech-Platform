import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  ApiError,
  createAccount,
  getAccounts,
  getDashboardSummary,
  getCurrentUser,
  login,
  logout,
  updateAccount,
} from "./authApi";
import type { AccountRole, DashboardSummary, UserProfile } from "./authApi";
import CrmPage from "./CrmPage";

type Account = UserProfile;
type WorkspaceView = "dashboard" | "crm" | "team";

const plannedModules = [
  "Clients",
  "Projects",
  "Tasks",
  "Proposals",
  "Invoices",
  "Payments",
  "Finance",
  "Documents",
  "Reports",
  "Settings",
];

export default function App() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [activeView, setActiveView] = useState<WorkspaceView>("dashboard");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [dashboardReload, setDashboardReload] = useState(0);

  useEffect(() => {
    let active = true;
    getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setNotice("The service is temporarily unavailable. Try again shortly.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!user || activeView !== "dashboard") return;
    let active = true;
    setDashboardLoading(true);
    setDashboardError("");
    getDashboardSummary()
      .then((summary) => {
        if (active) setDashboard(summary);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) {
          setUser(null);
          setDashboard(null);
          setNotice("Your session has expired. Sign in again.");
        } else {
          setDashboardError(reason instanceof Error ? reason.message : "Unable to load dashboard data.");
        }
      })
      .finally(() => {
        if (active) setDashboardLoading(false);
      });
    return () => {
      active = false;
    };
  }, [user, activeView, dashboardReload]);

  async function handleLogin(email: string, password: string) {
    const signedInUser = await login(email, password);
    setNotice("");
    setUser(signedInUser);
  }

  async function handleLogout() {
    try {
      await logout();
      setUser(null);
      setDashboard(null);
      setActiveView("dashboard");
      setNotice("");
    } catch {
      setNotice("Sign out could not reach the server. Check your connection and try again.");
    }
  }

  function handleSessionExpired() {
    setUser(null);
    setNotice("Your session has expired. Sign in again.");
  }

  if (loading) {
    return <main className="loading-screen" aria-live="polite">Loading secure workspace…</main>;
  }

  if (!user) {
    return <LoginScreen onLogin={handleLogin} notice={notice} />;
  }

  return (
    <div className={`app-shell${mobileNavOpen ? " nav-open" : ""}`}>
      {mobileNavOpen && (
        <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)} />
      )}
      <aside className="sidebar" aria-label="Primary navigation">
        <a className="sidebar-brand" href="/" aria-label="Mahi-Tech Platform home">
          <span className="brand-mark">MCS</span>
          <span className="sidebar-brand-copy">
            <strong>Mahi-Tech</strong>
            <small>Consultant &amp; Services</small>
          </span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="side-nav-list">
          <button
            className={`nav-item${activeView === "dashboard" ? " active" : ""}`}
            aria-current={activeView === "dashboard" ? "page" : undefined}
            onClick={() => { setActiveView("dashboard"); setMobileNavOpen(false); }}
          >
            <span className="nav-icon" aria-hidden="true">OV</span>
            <span>Dashboard</span>
          </button>
          <button
            className={`nav-item${activeView === "crm" ? " active" : ""}`}
            aria-current={activeView === "crm" ? "page" : undefined}
            onClick={() => { setActiveView("crm"); setMobileNavOpen(false); }}
          >
            <span className="nav-icon" aria-hidden="true">CR</span>
            <span>CRM &amp; Leads</span>
          </button>
          {plannedModules.slice(0, 8).map((label) => (
            <button className="nav-item nav-item-disabled" key={label} disabled title={`${label} module not implemented`}>
              <span className="nav-icon" aria-hidden="true">{label.slice(0, 2).toUpperCase()}</span>
              <span>{label}</span>
              <span className="nav-status">Planned</span>
            </button>
          ))}
          {user.role === "admin" ? (
            <button
              className={`nav-item${activeView === "team" ? " active" : ""}`}
              aria-current={activeView === "team" ? "page" : undefined}
              onClick={() => { setActiveView("team"); setMobileNavOpen(false); }}
            >
              <span className="nav-icon" aria-hidden="true">TM</span>
              <span>Team</span>
            </button>
          ) : (
            <button className="nav-item nav-item-disabled" disabled title="Team management is admin-only">
              <span className="nav-icon" aria-hidden="true">TM</span>
              <span>Team</span>
              <span className="nav-status">Admin</span>
            </button>
          )}
          {plannedModules.slice(8).map((label) => (
            <button className="nav-item nav-item-disabled" key={label} disabled title={`${label} module not implemented`}>
              <span className="nav-icon" aria-hidden="true">{label.slice(0, 2).toUpperCase()}</span>
              <span>{label}</span>
              <span className="nav-status">Planned</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-profile">
          <span className="profile-avatar" aria-hidden="true">{user.email.slice(0, 1).toUpperCase()}</span>
          <span className="sidebar-profile-copy">
            <strong>{user.email}</strong>
            <small>{user.role === "admin" ? "Administrator" : "Team member"}</small>
          </span>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="app-header">
          <button className="mobile-menu-button" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}>
            <span className="hamburger-icon" aria-hidden="true"><i /><i /><i /></span>
          </button>
          <div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{activeView === "team" ? "Team accounts" : activeView === "crm" ? "CRM & Leads" : "Dashboard"}</strong></div>
          <div className="header-actions">
            <span className="header-role">{user.role === "admin" ? "Administrator" : "Team member"}</span>
            <button className="button button-secondary" onClick={() => void handleLogout()}>Sign out</button>
          </div>
        </header>
        {notice && <p className="workspace-notice" role="status">{notice}</p>}
        <main className="workspace-content">
          {activeView === "team" && user.role === "admin" ? (
            <>
              <div className="page-heading">
                <p className="eyebrow">ADMINISTRATION</p>
                <h1>Team accounts</h1>
                <p>Create staff access and manage account status and roles.</p>
              </div>
              <AccountManagement currentUser={user} onSessionExpired={handleSessionExpired} />
            </>
          ) : activeView === "crm" ? (
            <CrmPage currentUser={user} onSessionExpired={handleSessionExpired} />
          ) : (
            <DashboardPage
              summary={dashboard}
              loading={dashboardLoading}
              error={dashboardError}
              onRetry={() => setDashboardReload((current) => current + 1)}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function DashboardPage({
  summary,
  loading,
  error,
  onRetry,
}: {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string;
  onRetry: () => void;
}) {
  if (loading) {
    return <section className="dashboard-state" aria-live="polite"><span className="loading-dot" />Loading dashboard data…</section>;
  }
  if (error || !summary) {
    return (
      <section className="dashboard-error" role="alert">
        <div><h1>Dashboard unavailable</h1><p>{error || "No dashboard response was received."}</p></div>
        <button className="button button-primary" onClick={onRetry}>Retry</button>
      </section>
    );
  }

  const emptyPanels = [
    { title: "Leads overview", module: "CRM & Leads", message: "CRM module not implemented yet." },
    { title: "Active projects", module: "Projects", message: "Projects module not implemented yet." },
    { title: "Pending tasks", module: "Tasks", message: "Tasks module not implemented yet." },
    { title: "Revenue overview", module: "Finance", message: "Finance module not implemented yet." },
    { title: "Recent activity", module: "Activity feed", message: "Business activity feed not implemented yet." },
    { title: "Upcoming follow-ups", module: "CRM & Leads", message: "Follow-up scheduling is not implemented yet." },
  ];

  return (
    <div className="dashboard-page">
      <section className="dashboard-heading">
        <div>
          <p className="eyebrow">MAHI-TECH CONSULTANT &amp; SERVICES</p>
          <h1>Dashboard</h1>
          <p>Welcome back, <strong>{summary.current_user.email}</strong>.</p>
        </div>
        <div className="dashboard-health" aria-label="System status">
          <span className="health-dot" />
          <span>API connected</span>
          <span className="health-divider" />
          <span className={`health-dot${summary.system.cache === "unavailable" ? " health-dot-warning" : ""}`} />
          <span>{summary.system.cache === "connected" ? `${summary.system.cache_backend === "redis" ? "Redis" : "Local cache"} available` : "Cache unavailable"}</span>
        </div>
      </section>

      <section className="metric-grid" aria-label="Team summary">
        <MetricCard label="Team accounts" value={summary.team_accounts.total} detail="Registered team members" tone="blue" />
        <MetricCard label="Active accounts" value={summary.team_accounts.active} detail="Currently enabled" tone="green" />
        <MetricCard label="Signed in as" value={summary.current_user.role === "admin" ? "Admin" : "Team"} detail={summary.current_user.email} tone="ink" />
        <MetricCard label="API status" value="Connected" detail="Django session API" tone="blue" />
      </section>

      <section className="dashboard-section">
        <div className="section-heading dashboard-section-heading">
          <div><p className="eyebrow">OPERATIONS</p><h2>Business overview</h2></div>
          <span className="section-count">Modules not yet available are clearly marked</span>
        </div>
        <div className="overview-grid">
          {emptyPanels.map((panel) => (
            <article className="overview-panel" key={panel.title}>
              <div className="overview-panel-heading"><h3>{panel.title}</h3><span>{panel.module}</span></div>
              <div className="module-empty-state"><span className="empty-state-mark" aria-hidden="true">—</span><p>{panel.message}</p></div>
            </article>
          ))}
        </div>
      </section>

    </div>
  );
}

function MetricCard({ label, value, detail, tone }: { label: string; value: string | number; detail: string; tone: "blue" | "green" | "ink" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function LoginScreen({ onLogin, notice }: { onLogin: (email: string, password: string) => Promise<void>; notice: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await onLogin(email, password);
      setPassword("");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Unable to sign in. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <header className="login-topbar">
        <a className="brand" href="/" aria-label="Mahi-Tech Platform">
          <span className="brand-mark">MCS</span>
          <span className="brand-copy">
            <strong>Mahi-Tech Platform</strong>
            <small>Business Management System</small>
          </span>
        </a>
      </header>
      <section className="login-layout">
        <div className="login-intro">
          <p className="eyebrow">STAFF ACCESS</p>
          <h1>Your Vision.<br />Our Technology.</h1>
          <p className="intro-copy">Sign in to your Mahi-Tech workspace.</p>
          <div className="login-rule" />
          <p className="login-caption">Secure access for authorized administrators and team members.</p>
        </div>
        <form className="login-panel" onSubmit={submit}>
          <div>
            <p className="eyebrow">WELCOME BACK</p>
            <h2>Sign in</h2>
          </div>
          {notice && <p className="notice" role="status">{notice}</p>}
          {error && <p className="error-message" role="alert">{error}</p>}
          <label>
            Email address
            <input autoComplete="username" autoFocus type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Password
            <input autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button className="button button-primary" type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <p className="form-footnote">Accounts are created by an administrator. Public registration is disabled.</p>
        </form>
      </section>
      <footer className="login-footer">Mahi-Tech Consultant &amp; Services <span>·</span> Internal access</footer>
    </main>
  );
}

function AccountManagement({ currentUser, onSessionExpired }: { currentUser: UserProfile; onSessionExpired: () => void }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AccountRole>("team");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function refreshAccounts() {
    try {
      setAccounts(await getAccounts());
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) onSessionExpired();
      else setError(reason instanceof Error ? reason.message : "Could not load accounts.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshAccounts();
  }, []);

  async function createTeamAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await createAccount({ email, password, role });
      setEmail("");
      setPassword("");
      setMessage("Account created.");
      await refreshAccounts();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) onSessionExpired();
      else setError(reason instanceof Error ? reason.message : "Could not create account.");
    }
  }

  function editAccount(id: string, changes: Partial<Pick<Account, "role" | "is_active">>) {
    setAccounts((current) => current.map((account) => account.id === id ? { ...account, ...changes } : account));
  }

  async function saveAccount(account: Account) {
    setError("");
    setMessage("");
    try {
      const updated = await updateAccount(account.id, { role: account.role, is_active: account.is_active });
      setAccounts((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage(`Updated ${updated.email}.`);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) onSessionExpired();
      else setError(reason instanceof Error ? reason.message : "Could not update account.");
    }
  }

  return (
    <section className="admin-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>Team accounts</h2>
        </div>
        <span className="section-count">{accounts.length} accounts</span>
      </div>
      <form className="account-create-form" onSubmit={createTeamAccount}>
        <label>
          Email address
          <input type="email" autoComplete="off" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Initial password
          <input type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
        </label>
        <label>
          Role
          <select value={role} onChange={(event) => setRole(event.target.value as AccountRole)}>
            <option value="team">Team member</option>
            <option value="admin">Administrator</option>
          </select>
        </label>
        <button className="button button-primary" type="submit">Create account</button>
      </form>
      {(message || error) && <p className={error ? "error-message" : "notice"} role={error ? "alert" : "status"}>{error || message}</p>}
      <div className="account-table-wrap">
        <table className="account-table">
          <thead>
            <tr><th>Account</th><th>Role</th><th>Status</th><th><span className="visually-hidden">Actions</span></th></tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={4}>Loading accounts…</td></tr>}
            {!loading && accounts.map((account) => {
              const isCurrentUser = account.id === currentUser.id;
              return (
                <tr key={account.id}>
                  <td><strong>{account.email}</strong>{isCurrentUser && <small className="self-label">You</small>}</td>
                  <td>
                    <select aria-label={`Role for ${account.email}`} value={account.role} disabled={isCurrentUser} onChange={(event) => editAccount(account.id, { role: event.target.value as AccountRole })}>
                      <option value="team">Team member</option>
                      <option value="admin">Administrator</option>
                    </select>
                  </td>
                  <td>
                    <label className="active-toggle">
                      <input type="checkbox" checked={account.is_active} disabled={isCurrentUser} onChange={(event) => editAccount(account.id, { is_active: event.target.checked })} />
                      <span>{account.is_active ? "Active" : "Inactive"}</span>
                    </label>
                  </td>
                  <td><button className="button button-secondary button-small" disabled={isCurrentUser} onClick={() => void saveAccount(account)}>Save</button></td>
                </tr>
              );
            })}
            {!loading && accounts.length === 0 && <tr><td colSpan={4}>No accounts found.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  );
}
