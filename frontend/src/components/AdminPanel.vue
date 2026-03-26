<script setup>
import { ref } from "vue";
import { api } from "../api";

const quality = ref([]);
const alerts = ref([]);
const msg = ref("");

async function refreshQuality() {
  try {
    const { data } = await api.post("/system/quality/refresh");
    quality.value = data;
  } catch (err) {
    msg.value = "Failed to refresh quality metrics";
  }
}

async function loadAlerts() {
  try {
    const { data } = await api.get("/system/alerts");
    alerts.value = data;
  } catch (err) {
    msg.value = "Failed to load alerts";
  }
}

async function backup() {
  try {
    const { data } = await api.post("/system/backup");
    msg.value = `Backup created: ${data.backup_file}`;
  } catch (err) {
    msg.value = "Backup failed";
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <h2>System Governance</h2>
      <div class="stats-mini">
        <span class="badge secondary">Server: Online</span>
      </div>
    </div>

    <div class="admin-actions row">
      <button @click="refreshQuality" class="secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
        Audit Metrics
      </button>
      <button @click="loadAlerts" class="secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        System Alerts
      </button>
      <button @click="backup" class="secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        Run Backup
      </button>
    </div>

    <div v-if="quality.length" class="metrics-section">
      <h3>Quality Validation Results</h3>
      <table>
        <thead>
          <tr>
            <th>Metric Key</th>
            <th>Calculated Value</th>
            <th>Defined Threshold</th>
            <th>Alert Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in quality" :key="m.metric_key + m.metric_value">
            <td><strong>{{ m.metric_key }}</strong></td>
            <td>{{ m.metric_value.toFixed(3) }}</td>
            <td>{{ m.threshold ?? "-" }}</td>
            <td>
              <span :class="m.exceeded ? 'status-critical' : 'status-ok'">
                {{ m.exceeded ? 'Exceeded' : 'Healthy' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="alerts.length" class="alerts-section">
      <h3>Active System Alerts</h3>
      <div class="alert-grid">
        <div v-for="(a, i) in alerts" :key="a.metric + i" class="alert-card">
          <span class="alert-icon">⚠️</span>
          <div class="content">
            <span class="metric">{{ a.metric }}</span>
            <span class="val">{{ a.value }} exceeds {{ a.threshold }}</span>
          </div>
        </div>
      </div>
    </div>

    <p v-if="msg" :class="msg.includes('fail') ? 'error' : 'ok'">{{ msg }}</p>
  </section>
</template>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}
.panel-header h2 { border: none; padding: 0; margin: 0; }
.admin-actions {
  padding-bottom: 32px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 32px;
}
h3 { font-size: 14px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; }
.status-ok { color: var(--success); font-weight: 600; }
.status-critical { color: var(--error); font-weight: 700; animation: blink 2s infinite; }

.alert-grid { display: grid; gap: 12px; }
.alert-card {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  background: #fff5f5;
  border: 1px solid #fee2e2;
  border-radius: var(--radius-md);
}
.alert-card .metric { font-weight: 700; color: var(--error); margin-right: 8px; }
.alert-card .val { font-size: 13px; color: #991b1b; }

@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}
</style>
