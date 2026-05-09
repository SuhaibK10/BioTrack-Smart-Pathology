/**
 * BioTrack AI — API Client
 * Connects to FastAPI backend. Falls back to demo data if backend is unreachable.
 */

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function analyzeReport({ file, name, age, sex }) {
  const form = new FormData();
  form.append("file", file);
  form.append("patient_name", name || "Unknown Patient");
  form.append("patient_age",  String(age || 0));
  form.append("patient_sex",  sex || "");

  const res = await fetch(`${BASE}/api/reports/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error ${res.status}`);
  }

  return res.json();
}

export async function getDashboardSummary() {
  const res = await fetch(`${BASE}/api/dashboard/summary`);
  return res.json();
}
