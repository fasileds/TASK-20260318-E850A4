<script setup>
import { ref, computed } from "vue";
import LoginPanel from "./components/LoginPanel.vue";
import ApplicantPanel from "./components/ApplicantPanel.vue";
import ReviewerPanel from "./components/ReviewerPanel.vue";
import FinancePanel from "./components/FinancePanel.vue";
import AdminPanel from "./components/AdminPanel.vue";

const user = ref(null);

const roleTitle = computed(() => {
  if (!user.value) return "Offline Integrated Platform";
  return `Logged in as ${user.value.username} (${user.value.role})`;
});

function onLoggedIn(loggedInUser) {
  user.value = loggedInUser;
}
</script>

<template>
  <div class="app-shell">
    <header class="hero">
      <h1>Activity Registration and Funding Audit</h1>
      <p v-if="user" class="badge">
        {{ user.username }} • <span class="role">{{ user.role }}</span>
      </p>
      <p v-else>{{ roleTitle }}</p>
    </header>

    <main class="main-content">
      <transition name="fade" mode="out-in">
        <LoginPanel v-if="!user" @loggedIn="onLoggedIn" />

        <div v-else :key="user.role">
          <ApplicantPanel v-if="user.role === 'applicant'" />
          <ReviewerPanel v-if="user.role === 'reviewer'" />
          <FinancePanel v-if="user.role === 'financial_admin'" />
          <AdminPanel v-if="user.role === 'system_admin'" />
        </div>
      </transition>
    </main>

    <footer class="app-footer">
      <p>© 2026 Integrated Offline Platform • Closed-Loop Management</p>
    </footer>
  </div>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 6px 16px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 600;
  margin-top: 12px;
}
.role {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 11px;
}
.main-content {
  min-height: 60vh;
}
.app-footer {
  text-align: center;
  padding: 48px 0;
  color: var(--text-muted);
  font-size: 12px;
}

/* Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
