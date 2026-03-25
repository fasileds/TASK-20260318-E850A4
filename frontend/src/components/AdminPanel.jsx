import { useState } from "react";
import { api } from "../api";

export function AdminPanel() {
  const [quality, setQuality] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [msg, setMsg] = useState("");

  async function refreshQuality() {
    const { data } = await api.post("/system/quality/refresh");
    setQuality(data);
  }

  async function loadAlerts() {
    const { data } = await api.get("/system/alerts");
    setAlerts(data);
  }

  async function backup() {
    const { data } = await api.post("/system/backup");
    setMsg(`Backup created: ${data.backup_file}`);
  }

  return (
    <section className="panel">
      <h2>System Administrator</h2>
      <div className="row">
        <button onClick={refreshQuality}>Refresh Quality Metrics</button>
        <button onClick={loadAlerts}>View Local Alerts</button>
        <button onClick={backup}>Create Daily Backup</button>
      </div>

      {!!quality.length && (
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Threshold</th>
              <th>Exceeded</th>
            </tr>
          </thead>
          <tbody>
            {quality.map((m) => (
              <tr key={m.metric_key + m.metric_value}>
                <td>{m.metric_key}</td>
                <td>{m.metric_value.toFixed(3)}</td>
                <td>{m.threshold ?? "-"}</td>
                <td>{String(m.exceeded)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!!alerts.length && (
        <ul>
          {alerts.map((a, i) => (
            <li key={a.metric + i}>
              {a.metric}: {a.value} / {a.threshold}
            </li>
          ))}
        </ul>
      )}

      {msg && <p className="ok">{msg}</p>}
    </section>
  );
}
