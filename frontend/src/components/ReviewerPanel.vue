<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const registrations = ref([]);
const selected = ref([]);
const comment = ref("");
const message = ref("");

async function load() {
  try {
    const { data } = await api.get("/registrations");
    registrations.value = data;
  } catch (err) {
    console.error("Failed to load registrations", err);
  }
}

onMounted(() => {
  load();
});

async function batch(action) {
  const ids = selected.value.slice(0, 50);
  try {
    const { data } = await api.post("/reviews/batch", {
      registration_ids: ids,
      action,
      comments: comment.value,
    });
    message.value = `Updated ${data.count} records.`;
    load();
  } catch (err) {
    message.value = "Batch review failed";
  }
}

function toggleAll(e) {
  if (e.target.checked) {
    selected.value = registrations.value.map(r => r.id);
  } else {
    selected.value = [];
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <h2>Application Review Queue</h2>
      <div class="stats-mini">
        <span class="badge secondary">{{ registrations.length }} Total</span>
        <span class="badge secondary">{{ selected.length }} Selected</span>
      </div>
    </div>
    
    <div class="workflow-controls">
      <textarea v-model="comment" placeholder="Provide review feedback or correction reasons..." />
      <div class="row">
        <button @click="batch('approve')" class="success-btn">Approve</button>
        <button @click="batch('reject')" class="error-btn">Reject</button>
        <button @click="batch('supplement')" class="secondary">Request correction</button>
        <button @click="batch('cancel')" class="secondary">Cancel</button>
        <button @click="batch('promote')" class="secondary">Promote</button>
      </div>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th style="width: 40px"><input type="checkbox" @change="toggleAll" /></th>
            <th>ID</th>
            <th>Registration Title</th>
            <th>Current Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in registrations" :key="r.id" :class="{ selected: selected.includes(r.id) }">
            <td>
              <input type="checkbox" :value="r.id" v-model="selected" />
            </td>
            <td><span class="id-tag">#{{ r.id }}</span></td>
            <td><strong>{{ r.title }}</strong></td>
            <td>
              <span class="status-badge" :class="r.status">
                {{ r.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="message" class="ok">{{ message }}</p>
  </section>
</template>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.panel-header h2 { border: none; padding: 0; }
.workflow-controls {
  margin-bottom: 32px;
  background: #f8fafc;
  padding: 20px;
  border-radius: var(--radius-md);
}
textarea {
  margin-bottom: 12px;
  min-height: 80px;
}
.table-container {
  overflow-x: auto;
}
.id-tag {
  font-family: monospace;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--text-muted);
}
.status-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.status-badge.submitted { background: #dcfce7; color: #166534; }
.status-badge.supplemented { background: #fef9c3; color: #854d0e; }
.status-badge.approved { background: #dbeafe; color: #1e40af; }
.status-badge.rejected { background: #fee2e2; color: #991b1b; }

.success-btn { background: var(--success); }
.success-btn:hover { background: #059669; }
.error-btn { background: var(--error); }
.error-btn:hover { background: #dc2626; }

tr.selected td { background-color: var(--accent-soft); }
</style>
