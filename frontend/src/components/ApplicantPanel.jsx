import { useMemo, useState } from "react";
import { api } from "../api";

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/png"];

export function ApplicantPanel() {
  const [step, setStep] = useState(1);
  const [registrationId, setRegistrationId] = useState(null);
  const [title, setTitle] = useState("");
  const [deadlineAt, setDeadlineAt] = useState("");
  const [formData, setFormData] = useState({
    applicant_name: "",
    id_number: "",
    contact_phone: "",
    activity_name: "",
  });
  const [checklistItemId, setChecklistItemId] = useState("");
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");

  const totalSizeMB = useMemo(() => files.reduce((s, f) => s + f.size, 0) / (1024 * 1024), [files]);

  function onFileChange(event) {
    const selected = Array.from(event.target.files || []);
    const valid = selected.filter((file) => ACCEPTED_TYPES.includes(file.type) && file.size <= 20 * 1024 * 1024);
    setFiles(valid);
  }

  async function createRegistration() {
    const payload = {
      title,
      deadline_at: new Date(deadlineAt).toISOString(),
      form_data: formData,
    };
    const { data } = await api.post("/registrations", payload);
    setRegistrationId(data.id);
    setStep(2);
    setMessage(`Registration #${data.id} created.`);
  }

  async function uploadFile(file) {
    const body = new FormData();
    body.append("file", file);
    body.append("label", "Submitted");
    await api.post(`/materials/${checklistItemId}/upload`, body, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  }

  async function submitRegistration() {
    if (!registrationId) return;
    await api.post(`/registrations/${registrationId}/submit`);
    setMessage("Submitted successfully.");
  }

  return (
    <section className="panel">
      <h2>Applicant Workspace</h2>
      <p>Wizard Step {step}/3 with real-time file checks (&lt;=20MB each, &lt;=200MB total).</p>

      <div className="grid two-col">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Registration title" />
        <input value={deadlineAt} onChange={(e) => setDeadlineAt(e.target.value)} type="datetime-local" />
        <input
          value={formData.applicant_name}
          onChange={(e) => setFormData((s) => ({ ...s, applicant_name: e.target.value }))}
          placeholder="Applicant name"
        />
        <input
          value={formData.id_number}
          onChange={(e) => setFormData((s) => ({ ...s, id_number: e.target.value }))}
          placeholder="ID number"
        />
        <input
          value={formData.contact_phone}
          onChange={(e) => setFormData((s) => ({ ...s, contact_phone: e.target.value }))}
          placeholder="Contact phone"
        />
        <input
          value={formData.activity_name}
          onChange={(e) => setFormData((s) => ({ ...s, activity_name: e.target.value }))}
          placeholder="Activity name"
        />
      </div>

      <button onClick={createRegistration}>Create Registration</button>

      <hr />

      <div className="grid two-col">
        <input
          value={checklistItemId}
          onChange={(e) => setChecklistItemId(e.target.value)}
          placeholder="Checklist Item ID"
        />
        <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png" onChange={onFileChange} />
      </div>
      <p>Total selected: {totalSizeMB.toFixed(2)} MB / 200 MB</p>

      <div className="row">
        {files.map((f) => (
          <button key={f.name + f.size} onClick={() => uploadFile(f)}>
            Upload {f.name}
          </button>
        ))}
      </div>

      <button onClick={submitRegistration} disabled={!registrationId}>
        Final Submit
      </button>

      {message && <p className="ok">{message}</p>}
    </section>
  );
}
