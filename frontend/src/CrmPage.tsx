import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  ApiError,
  archiveLead,
  convertLead,
  createLead,
  createLeadActivity,
  createLeadSource,
  getAccounts,
  getCrmDashboard,
  getLead,
  listLeadActivities,
  listLeads,
  listLeadSources,
  updateLead,
  updateLeadSource,
} from "./authApi";
import type {
  AccountRole,
  ClientCandidate,
  Lead,
  LeadActivity,
  LeadPriority,
  LeadSource,
  LeadStatus,
  UserProfile,
} from "./authApi";

type CrmSummary = Awaited<ReturnType<typeof getCrmDashboard>>;
type LeadList = Awaited<ReturnType<typeof listLeads>>;
type Screen = { kind: "list" } | { kind: "form"; lead?: Lead } | { kind: "detail"; id: string };

type CrmPageProps = {
  currentUser: UserProfile;
  onSessionExpired: () => void;
};

const statusLabels: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  proposal_sent: "Proposal sent",
  negotiation: "Negotiation",
  won: "Won",
  lost: "Lost",
};

const priorityLabels: Record<LeadPriority, string> = {
  low: "Low",
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
};

const statusOrder: LeadStatus[] = ["new", "contacted", "qualified", "proposal_sent", "negotiation", "won", "lost"];
const pageSize = 20;

function isAdmin(role: AccountRole) {
  return role === "admin";
}

function errorMessage(reason: unknown) {
  return reason instanceof Error ? reason.message : "The request could not be completed.";
}

function formatDate(value: string | null) {
  if (!value) return "Not scheduled";
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

function formatMoney(value: string | null, currency: string) {
  if (!value) return "Not estimated";
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(Number(value));
  } catch {
    return `${currency} ${value}`;
  }
}

export default function CrmPage({ currentUser, onSessionExpired }: CrmPageProps) {
  const [screen, setScreen] = useState<Screen>({ kind: "list" });
  const [summary, setSummary] = useState<CrmSummary | null>(null);
  const [leadPage, setLeadPage] = useState<LeadList | null>(null);
  const [sources, setSources] = useState<LeadSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState({ search: "", status: "", priority: "", source: "", ordering: "-updated_at", offset: 0 });
  const [refresh, setRefresh] = useState(0);
  const [sourceManagerOpen, setSourceManagerOpen] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ limit: String(pageSize), ordering: query.ordering });
    if (query.offset) params.set("offset", String(query.offset));
    if (query.search) params.set("search", query.search);
    if (query.status) params.set("status", query.status);
    if (query.priority) params.set("priority", query.priority);
    if (query.source) params.set("source", query.source);

    Promise.all([getCrmDashboard(), listLeads(params), listLeadSources()])
      .then(([nextSummary, nextLeads, nextSources]) => {
        if (!active) return;
        setSummary(nextSummary);
        setLeadPage(nextLeads);
        setSources(nextSources);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
        setError(errorMessage(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [query, refresh, onSessionExpired]);

  function refreshData() {
    setRefresh((value) => value + 1);
  }

  if (screen.kind === "form") {
    return (
      <LeadForm
        lead={screen.lead}
        sources={sources.filter((source) => source.is_active)}
        admin={isAdmin(currentUser.role)}
        onCancel={() => setScreen({ kind: screen.lead ? "detail" : "list", ...(screen.lead ? { id: screen.lead.id } : {}) } as Screen)}
        onSave={async (values) => {
          try {
            const saved = screen.lead ? await updateLead(screen.lead.id, values) : await createLead(values);
            setMessage(screen.lead ? "Lead updated." : "Lead created.");
            refreshData();
            setScreen({ kind: "detail", id: saved.id });
          } catch (reason) {
            if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
            throw reason;
          }
        }}
        onSessionExpired={onSessionExpired}
      />
    );
  }

  if (screen.kind === "detail") {
    return (
      <LeadDetail
        id={screen.id}
        user={currentUser}
        onBack={() => { setScreen({ kind: "list" }); refreshData(); }}
        onEdit={(lead) => setScreen({ kind: "form", lead })}
        onSessionExpired={onSessionExpired}
        onUpdated={(text) => { setMessage(text); refreshData(); }}
      />
    );
  }

  const totalPages = leadPage ? Math.max(1, Math.ceil(leadPage.count / pageSize)) : 1;
  const currentPage = Math.floor(query.offset / pageSize) + 1;

  return (
    <div className="crm-page">
      <div className="page-heading crm-page-heading">
        <p className="eyebrow">CUSTOMER RELATIONSHIPS</p>
        <h1>CRM &amp; Leads</h1>
        <p>Track prospects, ownership, follow-ups and progress through the pipeline.</p>
      </div>
      {summary && (
        <section className="crm-summary-grid" aria-label="CRM lead summary">
          <article className="crm-summary-item"><span>Total active leads</span><strong>{summary.total}</strong></article>
          <article className="crm-summary-item"><span>Follow-ups due</span><strong>{summary.follow_ups_due}</strong></article>
          {statusOrder.map((status) => (
            <button className="crm-summary-item crm-summary-button" key={status} onClick={() => setQuery((current) => ({ ...current, status, offset: 0 }))}>
              <span>{statusLabels[status]}</span><strong>{summary.by_status[status] ?? 0}</strong>
            </button>
          ))}
        </section>
      )}
      {message && <p className="notice" role="status">{message}</p>}
      {error && <div className="error-message crm-error" role="alert"><span>{error}</span><button className="button button-secondary button-small" onClick={refreshData}>Retry</button></div>}
      <section className="crm-lead-section">
        <div className="crm-toolbar">
          <div>
            <h2>Leads</h2>
            <span className="section-count">{leadPage ? `${leadPage.count} matching leads` : "Loading lead records"}</span>
          </div>
          <div className="crm-toolbar-actions">
            {isAdmin(currentUser.role) && <button className="button button-secondary" onClick={() => setSourceManagerOpen(true)}>Manage sources</button>}
            <button className="button button-primary" onClick={() => setScreen({ kind: "form" })}>Add lead</button>
          </div>
        </div>
        <form className="crm-filter-bar" onSubmit={(event) => { event.preventDefault(); setQuery((current) => ({ ...current, search: searchInput.trim(), offset: 0 })); }}>
          <label className="crm-search-field">
            <span className="visually-hidden">Search leads</span>
            <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search name, company, email or phone" />
          </label>
          <label>
            <span className="visually-hidden">Filter by status</span>
            <select value={query.status} onChange={(event) => setQuery((current) => ({ ...current, status: event.target.value, offset: 0 }))}>
              <option value="">All statuses</option>
              {statusOrder.map((status) => <option value={status} key={status}>{statusLabels[status]}</option>)}
            </select>
          </label>
          <label>
            <span className="visually-hidden">Filter by priority</span>
            <select value={query.priority} onChange={(event) => setQuery((current) => ({ ...current, priority: event.target.value, offset: 0 }))}>
              <option value="">All priorities</option>
              {Object.entries(priorityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
          </label>
          <label>
            <span className="visually-hidden">Filter by source</span>
            <select value={query.source} onChange={(event) => setQuery((current) => ({ ...current, source: event.target.value, offset: 0 }))}>
              <option value="">All sources</option>
              {sources.filter((source) => source.is_active).map((source) => <option value={source.id} key={source.id}>{source.name}</option>)}
            </select>
          </label>
          <label>
            <span className="visually-hidden">Sort leads</span>
            <select value={query.ordering} onChange={(event) => setQuery((current) => ({ ...current, ordering: event.target.value, offset: 0 }))}>
              <option value="-updated_at">Recently updated</option>
              <option value="follow_up_date">Follow-up date</option>
              <option value="name">Name A–Z</option>
              <option value="-estimated_value">Highest estimate</option>
              <option value="-priority">Priority</option>
            </select>
          </label>
          <button className="button button-secondary" type="submit">Search</button>
        </form>
        <div className="crm-table-wrap">
          <table className="crm-table">
            <thead><tr><th>Lead</th><th>Status</th><th>Priority</th><th>Owner</th><th>Follow-up</th><th>Estimate</th></tr></thead>
            <tbody>
              {loading && <tr><td className="crm-table-message" colSpan={6}>Loading leads…</td></tr>}
              {!loading && leadPage?.results.map((lead) => (
                <tr key={lead.id} className="crm-click-row" onClick={() => setScreen({ kind: "detail", id: lead.id })}>
                  <td><button className="crm-lead-link" onClick={(event) => { event.stopPropagation(); setScreen({ kind: "detail", id: lead.id }); }}>
                    <strong>{lead.name}</strong><span>{lead.company_name || lead.email || lead.phone || "Contact details not provided"}</span>
                  </button></td>
                  <td><span className={`crm-status status-${lead.status}`}>{statusLabels[lead.status]}</span></td>
                  <td><span className={`crm-priority priority-${lead.priority}`}>{priorityLabels[lead.priority]}</span></td>
                  <td>{lead.assigned_to_email || "Unassigned"}</td>
                  <td>{formatDate(lead.follow_up_date)}</td>
                  <td>{formatMoney(lead.estimated_value, lead.currency)}</td>
                </tr>
              ))}
              {!loading && leadPage?.results.length === 0 && <tr><td className="crm-table-message" colSpan={6}>No leads match these filters. Create a lead or adjust the search.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="crm-pagination">
          <span>{leadPage ? `Page ${currentPage} of ${totalPages}` : ""}</span>
          <div><button className="button button-secondary button-small" disabled={query.offset === 0 || loading} onClick={() => setQuery((current) => ({ ...current, offset: Math.max(0, current.offset - pageSize) }))}>Previous</button>
            <button className="button button-secondary button-small" disabled={!leadPage || query.offset + pageSize >= leadPage.count || loading} onClick={() => setQuery((current) => ({ ...current, offset: current.offset + pageSize }))}>Next</button></div>
        </div>
      </section>
      {sourceManagerOpen && <LeadSourceManager sources={sources} onClose={() => setSourceManagerOpen(false)} onChanged={refreshData} onSessionExpired={onSessionExpired} />}
    </div>
  );
}

function LeadForm({ lead, sources, admin, onCancel, onSave, onSessionExpired }: {
  lead?: Lead;
  sources: LeadSource[];
  admin: boolean;
  onCancel: () => void;
  onSave: (values: Partial<Lead>) => Promise<void>;
  onSessionExpired: () => void;
}) {
  const [team, setTeam] = useState<UserProfile[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fields, setFields] = useState({
    name: lead?.name ?? "",
    email: lead?.email ?? "",
    phone: lead?.phone ?? "",
    company_name: lead?.company_name ?? "",
    source: lead?.source ?? "",
    interested_service: lead?.interested_service ?? "",
    status: lead?.status ?? "new",
    priority: lead?.priority ?? "normal",
    assigned_to: lead?.assigned_to ?? "",
    estimated_value: lead?.estimated_value ?? "",
    currency: lead?.currency ?? "INR",
    follow_up_date: lead?.follow_up_date ?? "",
    notes: lead?.notes ?? "",
  });

  useEffect(() => {
    if (!admin) return;
    let active = true;
    getAccounts().then((users) => { if (active) setTeam(users.filter((user) => user.role === "team" && user.is_active)); }).catch((reason) => {
      if (reason instanceof ApiError && reason.status === 401) onSessionExpired();
      else if (active) setError(errorMessage(reason));
    });
    return () => { active = false; };
  }, [admin, onSessionExpired]);

  function change(field: keyof typeof fields, value: string) {
    setFields((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const payload: Partial<Lead> = {
      name: fields.name.trim(),
      email: fields.email.trim(),
      phone: fields.phone.trim(),
      company_name: fields.company_name.trim(),
      source: fields.source || null,
      interested_service: fields.interested_service.trim(),
      status: fields.status as LeadStatus,
      priority: fields.priority as LeadPriority,
      estimated_value: fields.estimated_value || null,
      currency: fields.currency.toUpperCase(),
      follow_up_date: fields.follow_up_date || null,
      notes: fields.notes.trim(),
    };
    if (admin) payload.assigned_to = fields.assigned_to || null;
    try {
      await onSave(payload);
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="crm-form-page">
      <button className="crm-back-link" onClick={onCancel}>← Back to leads</button>
      <div className="page-heading"><p className="eyebrow">CRM &amp; LEADS</p><h1>{lead ? "Edit lead" : "Add lead"}</h1><p>Lead values are stored as decimal amounts; INR is the default currency.</p></div>
      {error && <p className="error-message" role="alert">{error}</p>}
      <form className="crm-form" onSubmit={submit}>
        <div className="crm-form-grid">
          <label>Lead name<input required maxLength={200} value={fields.name} onChange={(event) => change("name", event.target.value)} /></label>
          <label>Company / business<input maxLength={200} value={fields.company_name} onChange={(event) => change("company_name", event.target.value)} /></label>
          <label>Email<input type="email" value={fields.email} onChange={(event) => change("email", event.target.value)} /></label>
          <label>Phone<input type="tel" maxLength={40} value={fields.phone} onChange={(event) => change("phone", event.target.value)} /></label>
          <label>Lead source<select value={fields.source} onChange={(event) => change("source", event.target.value)}><option value="">No source</option>{sources.map((source) => <option value={source.id} key={source.id}>{source.name}</option>)}</select></label>
          <label>Interested service<input maxLength={160} value={fields.interested_service} onChange={(event) => change("interested_service", event.target.value)} /></label>
          <label>Status<select value={fields.status} onChange={(event) => change("status", event.target.value)}>{statusOrder.map((status) => <option value={status} key={status}>{statusLabels[status]}</option>)}</select></label>
          <label>Priority<select value={fields.priority} onChange={(event) => change("priority", event.target.value)}>{Object.entries(priorityLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          {admin && <label>Assigned team member<select value={fields.assigned_to} onChange={(event) => change("assigned_to", event.target.value)}><option value="">Unassigned</option>{team.map((member) => <option value={member.id} key={member.id}>{member.email}</option>)}</select></label>}
          <label>Estimated deal value<input type="number" min="0" step="0.01" value={fields.estimated_value} onChange={(event) => change("estimated_value", event.target.value)} /></label>
          <label>Currency code<input maxLength={3} minLength={3} pattern="[A-Za-z]{3}" value={fields.currency} onChange={(event) => change("currency", event.target.value)} required /></label>
          <label>Follow-up date<input type="date" value={fields.follow_up_date} onChange={(event) => change("follow_up_date", event.target.value)} /></label>
          <label className="crm-form-wide">Notes<textarea rows={4} value={fields.notes} onChange={(event) => change("notes", event.target.value)} /></label>
        </div>
        <div className="crm-form-actions"><button className="button button-secondary" type="button" onClick={onCancel}>Cancel</button><button className="button button-primary" type="submit" disabled={saving}>{saving ? "Saving…" : lead ? "Save changes" : "Create lead"}</button></div>
      </form>
    </section>
  );
}

function LeadDetail({ id, user, onBack, onEdit, onSessionExpired, onUpdated }: {
  id: string;
  user: UserProfile;
  onBack: () => void;
  onEdit: (lead: Lead) => void;
  onSessionExpired: () => void;
  onUpdated: (message: string) => void;
}) {
  const [lead, setLead] = useState<Lead | null>(null);
  const [activities, setActivities] = useState<LeadActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activityText, setActivityText] = useState("");
  const [activityKind, setActivityKind] = useState("note");
  const [busy, setBusy] = useState(false);
  const [confirmAction, setConfirmAction] = useState<"archive" | "convert" | "duplicate" | null>(null);
  const [duplicateCandidates, setDuplicateCandidates] = useState<ClientCandidate[]>([]);
  const [selectedClientId, setSelectedClientId] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [nextLead, nextActivities] = await Promise.all([getLead(id), listLeadActivities(id)]);
      setLead(nextLead);
      setActivities(nextActivities);
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [id]);

  const canEdit = Boolean(lead && (user.role === "admin" || lead.assigned_to === user.id));

  async function addActivity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activityText.trim()) return;
    setBusy(true);
    setError("");
    try {
      await createLeadActivity(id, { kind: activityKind, description: activityText.trim() });
      setActivityText("");
      await load();
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  async function performArchive() {
    setBusy(true);
    setError("");
    try {
      await archiveLead(id);
      onUpdated("Lead archived.");
      onBack();
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
      setConfirmAction(null);
    }
  }

  async function performConversion(clientId?: string) {
    setBusy(true);
    setError("");
    try {
      const result = await convertLead(id, clientId);
      setConfirmAction(null);
      setDuplicateCandidates([]);
      onUpdated(`Converted to ${result.client.display_name}.`);
      await load();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409 && reason.payload.code === "POSSIBLE_DUPLICATE_CLIENT") {
        setDuplicateCandidates(reason.payload.candidates ?? []);
        setConfirmAction("duplicate");
      } else {
        if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
        setError(errorMessage(reason));
      }
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <section className="crm-detail-state" aria-live="polite">Loading lead details…</section>;
  if (error && !lead) return <section className="crm-detail-state"><p className="error-message" role="alert">{error}</p><button className="button button-secondary" onClick={onBack}>Back to leads</button></section>;
  if (!lead) return null;

  return (
    <section className="crm-detail-page">
      <button className="crm-back-link" onClick={onBack}>← Back to leads</button>
      {error && <p className="error-message" role="alert">{error}</p>}
      <div className="crm-detail-heading">
        <div><p className="eyebrow">LEAD DETAILS</p><h1>{lead.name}</h1><p>{lead.company_name || lead.interested_service || "Prospect"}</p></div>
        <div className="crm-detail-actions">
          {canEdit && <button className="button button-secondary" onClick={() => onEdit(lead)}>Edit lead</button>}
          {canEdit && !lead.archived_at && <button className="button button-secondary" onClick={() => setConfirmAction("archive")}>Archive</button>}
          {canEdit && lead.status === "won" && !lead.converted_client && <button className="button button-primary" onClick={() => setConfirmAction("convert")}>Convert to client</button>}
        </div>
      </div>
      <div className="crm-detail-grid">
        <section className="crm-detail-panel">
          <div className="crm-detail-status"><span className={`crm-status status-${lead.status}`}>{statusLabels[lead.status]}</span><span className={`crm-priority priority-${lead.priority}`}>{priorityLabels[lead.priority]}</span></div>
          <dl className="crm-detail-fields">
            <div><dt>Email</dt><dd>{lead.email || "Not provided"}</dd></div>
            <div><dt>Phone</dt><dd>{lead.phone || "Not provided"}</dd></div>
            <div><dt>Company</dt><dd>{lead.company_name || "Not provided"}</dd></div>
            <div><dt>Source</dt><dd>{lead.source_name || "Not provided"}</dd></div>
            <div><dt>Interested service</dt><dd>{lead.interested_service || "Not specified"}</dd></div>
            <div><dt>Assigned to</dt><dd>{lead.assigned_to_email || "Unassigned"}</dd></div>
            <div><dt>Estimated value</dt><dd>{formatMoney(lead.estimated_value, lead.currency)}</dd></div>
            <div><dt>Follow-up</dt><dd>{formatDate(lead.follow_up_date)}</dd></div>
            <div><dt>Created by</dt><dd>{lead.created_by_email || "Unknown"}</dd></div>
            {lead.converted_client && <div><dt>Converted client</dt><dd>{lead.converted_client_name || lead.converted_client}</dd></div>}
          </dl>
          <div className="crm-notes"><h2>Notes</h2><p>{lead.notes || "No internal notes."}</p></div>
        </section>
        <section className="crm-activity-panel">
          <div className="section-heading"><div><p className="eyebrow">HISTORY</p><h2>Lead activity</h2></div></div>
          {canEdit && (
            <form className="crm-activity-form" onSubmit={addActivity}>
              <label><span className="visually-hidden">Activity type</span><select value={activityKind} onChange={(event) => setActivityKind(event.target.value)}><option value="note">Note</option><option value="call">Call</option><option value="email">Email</option><option value="follow_up">Follow-up</option></select></label>
              <label className="visually-hidden" htmlFor="lead-activity-description">Add activity</label>
              <textarea id="lead-activity-description" rows={2} placeholder="Add a note or follow-up record" value={activityText} onChange={(event) => setActivityText(event.target.value)} />
              <button className="button button-primary button-small" disabled={busy || !activityText.trim()}>Add activity</button>
            </form>
          )}
          <div className="crm-timeline">
            {activities.map((activity) => (
              <article className="crm-timeline-item" key={activity.id}>
                <span className="timeline-dot" aria-hidden="true" />
                <div><div className="timeline-heading"><strong>{activity.kind.replaceAll("_", " ")}</strong><time>{new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(activity.created_at))}</time></div><p>{activity.description}</p><small>{activity.actor_email || "Former user"}</small></div>
              </article>
            ))}
            {activities.length === 0 && <p className="crm-inline-empty">No activity recorded yet.</p>}
          </div>
        </section>
      </div>
      {confirmAction && (
        <div className="crm-modal-backdrop" role="presentation">
          <section className="crm-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="crm-confirm-title">
            <h2 id="crm-confirm-title">{confirmAction === "archive" ? "Archive this lead?" : confirmAction === "duplicate" ? "Possible matching clients" : "Convert this Won lead?"}</h2>
            {confirmAction === "archive" && <p>The lead will leave active lists, but its history will be retained.</p>}
            {confirmAction === "convert" && <p>A client record will be created from the lead after duplicate checks.</p>}
            {confirmAction === "duplicate" && <><p>Select an existing client to link, or cancel to review the matches. No new client was created.</p><div className="crm-candidate-list">{duplicateCandidates.map((candidate) => <label key={candidate.id}><input type="radio" name="client-candidate" value={candidate.id} checked={selectedClientId === candidate.id} onChange={() => setSelectedClientId(candidate.id)} /><span><strong>{candidate.display_name}</strong><small>{candidate.company_name || candidate.email || candidate.phone}</small></span></label>)}</div></>}
            <div className="crm-form-actions"><button className="button button-secondary" disabled={busy} onClick={() => { setConfirmAction(null); setSelectedClientId(""); }}>Cancel</button>{confirmAction === "archive" ? <button className="button button-primary" disabled={busy} onClick={() => void performArchive()}>{busy ? "Archiving…" : "Archive lead"}</button> : confirmAction === "convert" ? <button className="button button-primary" disabled={busy} onClick={() => void performConversion()}>{busy ? "Converting…" : "Convert lead"}</button> : <button className="button button-primary" disabled={busy || !selectedClientId} onClick={() => void performConversion(selectedClientId)}>{busy ? "Linking…" : "Link existing client"}</button>}</div>
          </section>
        </div>
      )}
    </section>
  );
}

function LeadSourceManager({ sources, onClose, onChanged, onSessionExpired }: {
  sources: LeadSource[];
  onClose: () => void;
  onChanged: () => void;
  onSessionExpired: () => void;
}) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function addSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await createLeadSource(name.trim());
      setName("");
      onChanged();
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  async function toggleSource(source: LeadSource) {
    setError("");
    try {
      await updateLeadSource(source.id, { is_active: !source.is_active });
      onChanged();
    } catch (reason) {
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) onSessionExpired();
      setError(errorMessage(reason));
    }
  }

  return (
    <div className="crm-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="crm-source-dialog" role="dialog" aria-modal="true" aria-labelledby="crm-source-title">
        <div className="section-heading"><div><p className="eyebrow">ADMINISTRATION</p><h2 id="crm-source-title">Lead sources</h2></div><button className="button button-secondary button-small" onClick={onClose}>Close</button></div>
        {error && <p className="error-message" role="alert">{error}</p>}
        <form className="crm-source-form" onSubmit={addSource}><label>Source name<input value={name} onChange={(event) => setName(event.target.value)} maxLength={100} required /></label><button className="button button-primary" disabled={busy || !name.trim()}>{busy ? "Adding…" : "Add source"}</button></form>
        <div className="crm-source-list">{sources.length === 0 && <p className="crm-inline-empty">No sources configured.</p>}{sources.map((source) => <div key={source.id}><span>{source.name}</span><button className="button button-secondary button-small" onClick={() => void toggleSource(source)}>{source.is_active ? "Deactivate" : "Activate"}</button></div>)}</div>
      </section>
    </div>
  );
}
