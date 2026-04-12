import { useEffect, useState } from "react";

import { fetchJobs, fetchMe, fetchOverview, fetchViews, saveView, triggerJob } from "./api";
import { getKeycloak, initializeAuth } from "./auth";

const DEFAULT_RUN_FORM = {
  request_count: 120,
  seed: 7,
};

function StatCard({ label, value, accent }) {
  return (
    <article className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value" style={{ color: accent }}>
        {value}
      </strong>
    </article>
  );
}

function ModuleChart({ rows }) {
  if (!rows.length) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>Module Failure Rate</h2>
          <p>Run the pipeline to populate analytics.</p>
        </div>
      </section>
    );
  }

  const maxValue = Math.max(...rows.map((row) => row.failure_rate_pct), 1);
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Module Failure Rate</h2>
        <p>Live aggregation from PostgreSQL</p>
      </div>
      <div className="chart-grid">
        {rows.map((row) => (
          <div key={row.ai_module_name} className="chart-row">
            <div className="chart-copy">
              <strong>{row.ai_module_name}</strong>
              <span>{row.failed_runs} failed runs</span>
            </div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${Math.max((row.failure_rate_pct / maxValue) * 100, 12)}%` }}
              />
            </div>
            <span className="chart-value">{row.failure_rate_pct}%</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function RunsPanel({ jobs, canTrigger, formState, onChange, onSubmit, isSubmitting }) {
  return (
    <section className="panel panel-tall">
      <div className="panel-header">
        <h2>Pipeline Runs</h2>
        <p>Queue ETL refresh jobs and track execution state</p>
      </div>

      <div className="run-grid">
        <div className="run-trigger">
          <h3>Trigger New Run</h3>
          <label>
            Request count
            <input
              type="number"
              min="10"
              max="1000"
              value={formState.request_count}
              onChange={(event) => onChange("request_count", Number(event.target.value))}
              disabled={!canTrigger}
            />
          </label>
          <label>
            Seed
            <input
              type="number"
              min="1"
              max="999999"
              value={formState.seed}
              onChange={(event) => onChange("seed", Number(event.target.value))}
              disabled={!canTrigger}
            />
          </label>
          <button className="primary-button" onClick={onSubmit} disabled={!canTrigger || isSubmitting}>
            {canTrigger ? (isSubmitting ? "Queueing..." : "Run ETL Job") : "Admin role required"}
          </button>
        </div>

        <div className="run-table-wrap">
          <table className="run-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Status</th>
                <th>Seed</th>
                <th>Requests</th>
                <th>Triggered By</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>#{job.id}</td>
                  <td>
                    <span className={`status-pill status-${job.status}`}>{job.status}</span>
                  </td>
                  <td>{job.seed}</td>
                  <td>{job.request_count}</td>
                  <td>{job.triggered_by_username || "system"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function ViewsPanel({ views, onSave }) {
  const [viewName, setViewName] = useState("");

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Saved Views</h2>
        <p>Persistent user-specific dashboard state</p>
      </div>
      <div className="saved-view-creator">
        <input
          type="text"
          placeholder="Morning ops cut"
          value={viewName}
          onChange={(event) => setViewName(event.target.value)}
        />
        <button
          className="secondary-button"
          onClick={() => {
            if (!viewName.trim()) return;
            onSave({
              name: viewName.trim(),
              filters_json: { focus: "default" },
              layout_json: { cards: ["latency", "jobs", "modules"] },
            });
            setViewName("");
          }}
        >
          Save current layout
        </button>
      </div>
      <div className="view-list">
        {views.map((view) => (
          <article key={view.id} className="view-card">
            <strong>{view.name}</strong>
            <span>Created {new Date(view.created_at).toLocaleString()}</span>
          </article>
        ))}
        {views.length === 0 ? <p className="empty-state">No saved views yet.</p> : null}
      </div>
    </section>
  );
}

export default function App() {
  const [bootStatus, setBootStatus] = useState("booting");
  const [token, setToken] = useState("");
  const [me, setMe] = useState(null);
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [views, setViews] = useState([]);
  const [error, setError] = useState("");
  const [runForm, setRunForm] = useState(DEFAULT_RUN_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadDashboard(authToken) {
    const [meData, overviewData, jobsData, viewsData] = await Promise.all([
      fetchMe(authToken),
      fetchOverview(authToken),
      fetchJobs(authToken),
      fetchViews(authToken),
    ]);
    setMe(meData);
    setOverview(overviewData);
    setJobs(jobsData);
    setViews(viewsData);
  }

  useEffect(() => {
    let intervalId;

    initializeAuth()
      .then(async (instance) => {
        setToken(instance.token);
        await loadDashboard(instance.token);
        setBootStatus("ready");

        intervalId = window.setInterval(async () => {
          try {
            await instance.updateToken(30);
            setToken(instance.token);
            await loadDashboard(instance.token);
          } catch (refreshError) {
            setError(String(refreshError));
          }
        }, 15000);
      })
      .catch((bootError) => {
        setBootStatus("error");
        setError(String(bootError));
      });

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, []);

  const canTrigger = Boolean(me?.roles?.includes("admin"));

  if (bootStatus === "booting") {
    return <div className="app-shell loading-shell">Initializing observability control room...</div>;
  }

  if (bootStatus === "error") {
    return <div className="app-shell loading-shell">Failed to boot: {error}</div>;
  }

  const keycloak = getKeycloak();

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Synthetic Medical AI Workflow Observatory</span>
          <h1>ETL telemetry, auth, job control, and user state in one stack.</h1>
          <p>
            This UI reads live analytics from PostgreSQL, authenticates through Keycloak, triggers new ETL runs
            through the backend API, and stores user-specific dashboard views.
          </p>
        </div>
        <div className="hero-card">
          <span className="user-chip">{me?.username}</span>
          <span>{me?.roles?.join(", ")}</span>
          <button className="secondary-button" onClick={() => keycloak.logout()}>
            Sign out
          </button>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="stats-grid">
        <StatCard label="Total jobs" value={overview?.total_jobs ?? 0} accent="#155eef" />
        <StatCard label="Failed jobs" value={overview?.failed_jobs ?? 0} accent="#d92d20" />
        <StatCard
          label="Avg queue delay"
          value={`${overview?.avg_queue_delay_minutes ?? 0} min`}
          accent="#dc6803"
        />
        <StatCard
          label="Avg end-to-end"
          value={`${overview?.avg_end_to_end_minutes ?? 0} min`}
          accent="#087443"
        />
      </section>

      <section className="content-grid">
        <ModuleChart rows={overview?.module_summaries ?? []} />
        <ViewsPanel
          views={views}
          onSave={async (payload) => {
            try {
              const saved = await saveView(token, payload);
              setViews((current) => [saved, ...current]);
            } catch (saveError) {
              setError(String(saveError));
            }
          }}
        />
      </section>

      <RunsPanel
        jobs={jobs}
        canTrigger={canTrigger}
        formState={runForm}
        onChange={(key, value) => setRunForm((current) => ({ ...current, [key]: value }))}
        onSubmit={async () => {
          setIsSubmitting(true);
          setError("");
          try {
            const created = await triggerJob(token, runForm);
            setJobs((current) => [created, ...current]);
          } catch (submitError) {
            setError(String(submitError));
          } finally {
            setIsSubmitting(false);
          }
        }}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
