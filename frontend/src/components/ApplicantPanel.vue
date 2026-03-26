<script setup>
import { ref, computed } from "vue";
import { api } from "../api";

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/png"];

const step = ref(1);
const registrationId = ref(null);
const title = ref("");
const deadlineAt = ref("");
const formData = ref({
  applicant_name: "",
  id_number: "",
  contact_phone: "",
  activity_name: "",
});
const checklistItemId = ref("");
const files = ref([]);
const message = ref("");

const totalSizeMB = computed(() => 
  files.value.reduce((s, f) => s + f.size, 0) / (1024 * 1024)
);

function onFileChange(event) {
  const selected = Array.from(event.target.files || []);
  const valid = selected.filter(
    (file) => ACCEPTED_TYPES.includes(file.type) && file.size <= 20 * 1024 * 1024
  );
  files.value = valid;
}

async function createRegistration() {
  const payload = {
    title: title.value,
    deadline_at: new Date(deadlineAt.value).toISOString(),
    form_data: formData.value,
  };
  const { data } = await api.post("/registrations", payload);
  registrationId.value = data.id;
  step.value = 2;
  message.value = `Registration #${data.id} created.`;
}

async function uploadFile(file) {
  const body = new FormData();
  body.append("file", file);
  body.append("label", "Submitted");
  await api.post(`/materials/${checklistItemId.value}/upload`, body, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

async function submitRegistration() {
  if (!registrationId.value) return;
  await api.post(`/registrations/${registrationId.value}/submit`);
  message.value = "Submitted successfully.";
}
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <h2>Registration Wizard</h2>
      <div class="steps">
        <span :class="{ active: step >= 1 }">1 Profile</span>
        <span class="sep"></span>
        <span :class="{ active: step >= 2 }">2 Materials</span>
        <span class="sep"></span>
        <span :class="{ active: step >= 3 }">3 Review</span>
      </div>
    </div>

    <!-- Step 1: Basic Info -->
    <div v-if="step === 1" class="wizard-step">
      <h3>Step 1: Activity & Applicant Details</h3>
      <div class="grid two-col">
        <div class="field">
          <label>Registration Title</label>
          <input v-model="title" placeholder="e.g. Annual Symposium 2026" />
        </div>
        <div class="field">
          <label>Submission Deadline</label>
          <input v-model="deadlineAt" type="datetime-local" />
        </div>
        <div class="field">
          <label>Applicant Legal Name</label>
          <input v-model="formData.applicant_name" placeholder="Full name as on ID" />
        </div>
        <div class="field">
          <label>ID Identification Number</label>
          <input v-model="formData.id_number" placeholder="Sensitive (masked after save)" />
        </div>
        <div class="field">
          <label>Contact Phone</label>
          <input v-model="formData.contact_phone" placeholder="+1..." />
        </div>
        <div class="field">
          <label>Activity Official Name</label>
          <input v-model="formData.activity_name" placeholder="Full activity name" />
        </div>
      </div>
      <div class="actions">
        <button @click="createRegistration" :disabled="!title || !deadlineAt">
          Initialize Registration
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </button>
      </div>
    </div>

    <!-- Step 2: Uploads -->
    <div v-if="step === 2" class="wizard-step">
      <h3>Step 2: Material Checklist Upload</h3>
      <p class="desc">Upload PDF/JPG/PNG images. Self-test validation applied (Max 20MB/file, 200MB total).</p>
      
      <div class="grid two-col upload-controls">
        <div class="field">
          <label>Target Checklist Item ID</label>
          <input v-model="checklistItemId" placeholder="1, 2, 3..." />
        </div>
        <div class="field">
          <label>File Selection</label>
          <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png" @change="onFileChange" />
        </div>
      </div>

      <div class="upload-stats">
        <div class="stat">
          <span class="label">Total Size:</span>
          <span class="value" :class="{ error: totalSizeMB > 200 }">{{ totalSizeMB.toFixed(2) }} MB / 200 MB</span>
        </div>
      </div>

      <div v-if="files.length" class="file-list">
        <div v-for="f in files" :key="f.name + f.size" class="file-card">
          <div class="info">
            <span class="name">{{ f.name }}</span>
            <span class="size">{{ (f.size/1024/1024).toFixed(2) }} MB</span>
          </div>
          <button class="secondary small" @click="uploadFile(f)">Upload</button>
        </div>
      </div>

      <div class="actions">
        <button class="secondary" @click="step = 1">Back</button>
        <button @click="step = 3">Review Submission</button>
      </div>
    </div>

    <!-- Step 3: Final -->
    <div v-if="step === 3" class="wizard-step">
      <h3>Step 3: Final Audit Submission</h3>
      <p>Please ensure all required materials from the checklist are uploaded and versions are correct.</p>
      <div class="actions">
        <button class="secondary" @click="step = 2">Back</button>
        <button @click="submitRegistration" :disabled="!registrationId">
          Finalize and Lock
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
        </button>
      </div>
    </div>

    <p v-if="message" :class="message.includes('fail') ? 'error' : 'ok'">{{ message }}</p>
  </section>
</template>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  border-bottom: 4px solid var(--accent);
  padding-bottom: 16px;
  margin-bottom: 32px;
}
.panel-header h2 { border: none; padding: 0; margin: 0; }
.steps {
  display: flex;
  align-items: center;
  gap: 12px;
}
.steps span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}
.steps span.active { color: var(--accent); }
.sep {
  width: 24px;
  height: 2px;
  background: var(--border-color);
}
.wizard-step h3 {
  margin-bottom: 24px;
  font-size: 1.1rem;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
}
.desc { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }
.upload-stats {
  padding: 16px;
  background: var(--bg-color);
  border-radius: var(--radius-md);
  margin: 24px 0;
}
.stat .label { font-size: 13px; font-weight: 600; color: var(--text-muted); margin-right: 8px; }
.stat .value.error { color: var(--error); font-weight: 700; }

.file-list {
  display: grid;
  gap: 12px;
  margin: 16px 0;
}
.file-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fdfdfd;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}
.file-card .info { display: flex; flex-direction: column; }
.file-card .name { font-size: 14px; font-weight: 500; }
.file-card .size { font-size: 12px; color: var(--text-muted); }
.small { padding: 6px 12px; font-size: 12px; }
</style>
