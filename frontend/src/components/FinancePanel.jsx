import { useState } from "react";
import { api } from "../api";

export function FinancePanel() {
  const [accountId, setAccountId] = useState("");
  const [txType, setTxType] = useState("expense");
  const [category, setCategory] = useState("General");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [uploadedInvoicePath, setUploadedInvoicePath] = useState("");
  const [message, setMessage] = useState("");

  async function uploadInvoice() {
    if (!invoiceFile || !accountId) {
      setMessage("Please provide Account ID and select an invoice file.");
      return;
    }

    const formData = new FormData();
    formData.append("account_id", String(Number(accountId)));
    formData.append("invoice", invoiceFile);

    const { data } = await api.post("/funding/invoices/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setUploadedInvoicePath(data.invoice_path);
    setMessage(`Invoice uploaded: ${data.filename}`);
  }

  async function submitTransaction() {
    const { data } = await api.post("/funding/transactions", {
      account_id: Number(accountId),
      transaction_type: txType,
      category,
      amount: Number(amount),
      note,
      invoice_path: uploadedInvoicePath || null,
    });

    if (data.overspending_warning) {
      const confirmed = window.confirm(
        "Warning: Expenses exceed 110% of budget. Do you want to confirm this submission?"
      );
      if (!confirmed) {
        setMessage("Secondary confirmation declined by operator.");
        return;
      }
    }
    setMessage("Transaction recorded.");
  }

  return (
    <section className="panel">
      <h2>Financial Administrator</h2>
      <p>Record income/expense, upload invoice attachment to local disk, and trigger overspending warnings.</p>

      <div className="grid two-col">
        <input value={accountId} onChange={(e) => setAccountId(e.target.value)} placeholder="Account ID" />
        <select value={txType} onChange={(e) => setTxType(e.target.value)}>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category" />
        <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Amount" type="number" />
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setInvoiceFile(e.target.files?.[0] || null)}
        />
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note" />
      </div>

      <button onClick={uploadInvoice}>Upload Invoice</button>
      {uploadedInvoicePath && <p>Saved invoice path: {uploadedInvoicePath}</p>}

      <button onClick={submitTransaction}>Save Transaction</button>
      {message && <p className="ok">{message}</p>}
    </section>
  );
}
