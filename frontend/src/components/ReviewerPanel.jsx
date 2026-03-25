import { useEffect, useState } from "react";
import { api } from "../api";

export function ReviewerPanel() {
  const [registrations, setRegistrations] = useState([]);
  const [selected, setSelected] = useState([]);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const { data } = await api.get("/registrations");
    setRegistrations(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function batch(action) {
    const ids = selected.slice(0, 50);
    const { data } = await api.post("/reviews/batch", {
      registration_ids: ids,
      action,
      comments: comment,
    });
    setMessage(`Updated ${data.count} records.`);
    load();
  }

  return (
    <section className="panel">
      <h2>Reviewer List Workflow</h2>
      <p>State machine: Submitted -> Supplemented -> Approved/Rejected/Canceled -> Promoted from Waitlist.</p>
      <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Review comments" />
      <div className="row">
        <button onClick={() => batch("approve")}>Batch Approve (&lt;=50)</button>
        <button onClick={() => batch("reject")}>Batch Reject (&lt;=50)</button>
        <button onClick={() => batch("supplement")}>Batch Request Correction</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Select</th>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {registrations.map((r) => (
            <tr key={r.id}>
              <td>
                <input
                  type="checkbox"
                  checked={selected.includes(r.id)}
                  onChange={(e) => {
                    setSelected((prev) =>
                      e.target.checked ? [...prev, r.id] : prev.filter((id) => id !== r.id)
                    );
                  }}
                />
              </td>
              <td>{r.id}</td>
              <td>{r.title}</td>
              <td>{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {message && <p className="ok">{message}</p>}
    </section>
  );
}
