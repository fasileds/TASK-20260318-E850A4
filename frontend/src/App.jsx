import { useMemo, useState } from "react";
import { LoginPanel } from "./components/LoginPanel";
import { ApplicantPanel } from "./components/ApplicantPanel";
import { ReviewerPanel } from "./components/ReviewerPanel";
import { FinancePanel } from "./components/FinancePanel";
import { AdminPanel } from "./components/AdminPanel";

export default function App() {
  const [user, setUser] = useState(null);

  const roleTitle = useMemo(() => {
    if (!user) return "Offline Integrated Platform";
    return `Logged in as ${user.username} (${user.role})`;
  }, [user]);

  return (
    <div className="app-shell">
      <header className="hero">
        <h1>Activity Registration and Funding Audit Management</h1>
        <p>{roleTitle}</p>
      </header>

      {!user && <LoginPanel onLoggedIn={setUser} />}

      {user?.role === "applicant" && <ApplicantPanel />}
      {user?.role === "reviewer" && <ReviewerPanel />}
      {user?.role === "financial_admin" && <FinancePanel />}
      {user?.role === "system_admin" && <AdminPanel />}
    </div>
  );
}
