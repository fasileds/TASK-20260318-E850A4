<script setup>
import { ref } from "vue";
import { api } from "../api";

const accountId = ref("");
const txType = ref("expense");
const category = ref("General");
const amount = ref("");
const note = ref("");
const invoiceFile = ref(null);
const uploadedInvoicePath = ref("");
const message = ref("");

async function onFileChange(event) {
  invoiceFile.value = event.target.files?.[0] || null;
}

async function uploadInvoice() {
  if (!invoiceFile.value || !accountId.value) {
    message.value = "Please provide Account ID and select an invoice file.";
    return;
  }

  const formData = new FormData();
  formData.append("account_id", String(Number(accountId.value)));
  formData.append("invoice", invoiceFile.value);

  try {
    const { data } = await api.post("/funding/invoices/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    uploadedInvoicePath.value = data.invoice_path;
    message.value = `Invoice uploaded: ${data.filename}`;
  } catch (err) {
    message.value = "Invoice upload failed";
  }
}

async function submitTransaction() {
  const payload = {
    account_id: Number(accountId.value),
    transaction_type: txType.value,
    category: category.value,
    amount: Number(amount.value),
    note: note.value,
    invoice_path: uploadedInvoicePath.value || null,
    confirmed_overspending: false,
  };

  try {
    let { data } = await api.post("/funding/transactions", payload);

    if (data.overspending_warning && data.id === 0) {
      const confirmed = window.confirm(
        "Warning: Expenses exceed 110% of budget. Do you want to confirm this submission?"
      );
      if (!confirmed) {
        message.value = "Secondary confirmation declined by operator.";
        return;
      }
      // Resubmit with confirmation
      const res = await api.post("/funding/transactions", { 
        ...payload, 
        confirmed_overspending: true 
      });
      data = res.data;
    }
    message.value = "Transaction recorded.";
  } catch (err) {
    message.value = "Transaction submission failed";
  }
}
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <h2>Financial Administration</h2>
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
    </div>
    
    <div class="financial-form">
      <div class="grid two-col">
        <div class="field">
          <label>Target Funding Account (ID)</label>
          <input v-model="accountId" placeholder="e.g. 1" />
        </div>
        <div class="field">
          <label>Transaction Type</label>
          <select v-model="txType">
            <option value="income">Income (+)</option>
            <option value="expense">Expense (-)</option>
          </select>
        </div>
        <div class="field">
          <label>Category</label>
          <input v-model="category" placeholder="e.g. Venue, Catering..." />
        </div>
        <div class="field">
          <label>Amount (USD)</label>
          <input v-model="amount" placeholder="0.00" type="number" />
        </div>
        <div class="field full-width">
          <label>Supporting Evidence (Invoice Attachment)</label>
          <div class="file-action-group">
            <input type="file" accept=".pdf,.jpg,.jpeg,.png" @change="onFileChange" />
            <button class="secondary small" @click="uploadInvoice" :disabled="!invoiceFile">Upload Attachment</button>
          </div>
          <p v-if="uploadedInvoicePath" class="path-label">Stored: {{ uploadedInvoicePath }}</p>
        </div>
        <div class="field full-width">
          <label>Operation Notes</label>
          <textarea v-model="note" placeholder="Internal remarks..." rows="2"></textarea>
        </div>
      </div>

      <div class="form-actions">
        <button @click="submitTransaction" :disabled="!accountId || !amount">
          Commit Transaction
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
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
  border-bottom: 4px solid var(--accent);
  padding-bottom: 16px;
  margin-bottom: 32px;
}
.panel-header h2 { border: none; padding: 0; margin: 0; }
.financial-form {
  background: #fdfdfd;
}
.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.full-width { grid-column: 1 / -1; }
.file-action-group {
  display: flex;
  gap: 12px;
}
.path-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  word-break: break-all;
}
.form-actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
}
.small { padding: 8px 16px; font-size: 12px; }
</style>
