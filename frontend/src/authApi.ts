export type AccountRole = "admin" | "team";

export type UserProfile = {
  id: string;
  email: string;
  is_active: boolean;
  role: AccountRole;
};

export type DashboardSummary = {
  current_user: Pick<UserProfile, "id" | "email" | "role">;
  team_accounts: {
    total: number;
    active: number;
  };
  system: {
    api: "connected";
    cache: "connected" | "unavailable";
    cache_backend: "redis" | "local";
  };
};

export type LeadStatus = "new" | "contacted" | "qualified" | "proposal_sent" | "negotiation" | "won" | "lost";
export type LeadPriority = "low" | "normal" | "high" | "urgent";

export type LeadSource = {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Lead = {
  id: string;
  name: string;
  email: string;
  phone: string;
  company_name: string;
  source: string | null;
  source_name: string | null;
  interested_service: string;
  status: LeadStatus;
  priority: LeadPriority;
  assigned_to: string | null;
  assigned_to_email: string | null;
  estimated_value: string | null;
  currency: string;
  follow_up_date: string | null;
  notes: string;
  created_by: string | null;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  converted_client: string | null;
  converted_client_name: string | null;
  converted_at: string | null;
};

export type LeadActivity = {
  id: string;
  kind: string;
  description: string;
  previous_values: Record<string, unknown>;
  new_values: Record<string, unknown>;
  actor: string | null;
  actor_email: string | null;
  created_at: string;
};

export type LeadListResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Lead[];
};

export type ClientCandidate = {
  id: string;
  display_name: string;
  company_name: string;
  email: string;
  phone: string;
};

type UserResponse = { user: UserProfile };
type AccountsResponse = { accounts: UserProfile[] };
type DashboardResponse = { data: DashboardSummary };
type ErrorResponse = { detail?: string; password?: string[]; code?: string; candidates?: ClientCandidate[] };

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
let csrfToken = "";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly payload: ErrorResponse = {}) {
    super(message);
    this.name = "ApiError";
  }
}

async function updateCsrfToken() {
  const response = await fetch(`${API_BASE_URL}/auth/csrf/`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new ApiError("Unable to initialize secure sign-in.", response.status);
  const payload = await response.json() as { csrfToken: string };
  csrfToken = payload.csrfToken;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    if (!csrfToken) await updateCsrfToken();
    headers.set("X-CSRFToken", csrfToken);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    method,
    credentials: "include",
    headers,
  });
  const payload = await response.json().catch(() => ({})) as ErrorResponse;
  if (!response.ok) {
    const passwordMessage = payload.password?.join(" ");
    throw new ApiError(payload.detail ?? passwordMessage ?? "The request could not be completed.", response.status, payload);
  }
  return payload as T;
}

export async function getCurrentUser(): Promise<UserProfile | null> {
  await updateCsrfToken();
  try {
    return (await request<UserResponse>("/auth/me/")).user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export async function login(email: string, password: string): Promise<UserProfile> {
  const response = await request<UserResponse>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  await updateCsrfToken();
  return response.user;
}

export async function logout() {
  await request<{ detail: string }>("/auth/logout/", { method: "POST", body: "{}" });
  csrfToken = "";
}

export async function getAccounts(): Promise<UserProfile[]> {
  return (await request<AccountsResponse>("/accounts/")).accounts;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return (await request<DashboardResponse>("/dashboard/summary/")).data;
}

export async function createAccount(account: { email: string; password: string; role: AccountRole }): Promise<UserProfile> {
  return (await request<UserResponse>("/accounts/", {
    method: "POST",
    body: JSON.stringify(account),
  })).user;
}

export async function updateAccount(id: string, changes: { role: AccountRole; is_active: boolean }): Promise<UserProfile> {
  return (await request<UserResponse>(`/accounts/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(changes),
  })).user;
}

export async function getCrmDashboard() {
  return request<{ total: number; by_status: Record<LeadStatus, number>; follow_ups_due: number }>("/crm/dashboard/");
}

export async function listLeads(params: URLSearchParams): Promise<LeadListResponse> {
  const query = params.toString();
  return request<LeadListResponse>(`/crm/leads/${query ? `?${query}` : ""}`);
}

export async function getLead(id: string): Promise<Lead> {
  return request<Lead>(`/crm/leads/${id}/`);
}

export async function createLead(lead: Partial<Lead>): Promise<Lead> {
  return request<Lead>("/crm/leads/", { method: "POST", body: JSON.stringify(lead) });
}

export async function updateLead(id: string, changes: Partial<Lead>): Promise<Lead> {
  return request<Lead>(`/crm/leads/${id}/`, { method: "PATCH", body: JSON.stringify(changes) });
}

export async function archiveLead(id: string): Promise<void> {
  await request<{ detail: string }>(`/crm/leads/${id}/archive/`, { method: "POST", body: "{}" });
}

export async function listLeadSources(): Promise<LeadSource[]> {
  return request<LeadSource[]>("/crm/lead-sources/");
}

export async function createLeadSource(name: string): Promise<LeadSource> {
  return request<LeadSource>("/crm/lead-sources/", { method: "POST", body: JSON.stringify({ name }) });
}

export async function updateLeadSource(id: string, changes: { is_active: boolean }): Promise<LeadSource> {
  return request<LeadSource>(`/crm/lead-sources/${id}/`, { method: "PATCH", body: JSON.stringify(changes) });
}

export async function listLeadActivities(id: string): Promise<LeadActivity[]> {
  return request<LeadActivity[]>(`/crm/leads/${id}/activities/`);
}

export async function createLeadActivity(id: string, activity: { kind: string; description: string }): Promise<LeadActivity> {
  return request<LeadActivity>(`/crm/leads/${id}/activities/`, { method: "POST", body: JSON.stringify(activity) });
}

export async function convertLead(id: string, existingClientId?: string) {
  return request<{ lead_id: string; client: ClientCandidate; created_new_client: boolean }>(
    `/crm/leads/${id}/convert/`,
    { method: "POST", body: JSON.stringify(existingClientId ? { existing_client_id: existingClientId } : {}) },
  );
}