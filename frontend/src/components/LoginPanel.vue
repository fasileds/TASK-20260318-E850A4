<script setup>
import { ref } from "vue";
import { api, setAuthToken, setUsernameHeader } from "../api";

const emit = defineEmits(["loggedIn"]);

const username = ref("");
const password = ref("");
const error = ref("");

async function handleLogin() {
  error.value = "";
  try {
    const { data } = await api.post("/auth/login", {
      username: username.value,
      password: password.value,
    });
    setAuthToken(data.token);
    setUsernameHeader(data.user.username);
    emit("loggedIn", data.user);
  } catch (err) {
    error.value = err.response?.data?.detail || "Login failed";
  }
}
</script>

<template>
  <section class="panel login-panel">
    <div class="header">
      <div class="icon-circle">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
      </div>
      <h2>Internal Access Login</h2>
      <p class="subtitle">Enter your credentials to manage registrations</p>
    </div>
    
    <form class="grid" @submit.prevent="handleLogin">
      <div class="input-group">
        <label>Username</label>
        <input v-model="username" placeholder="applicant_demo" required />
      </div>
      <div class="input-group">
        <label>Password</label>
        <input v-model="password" type="password" placeholder="••••••••" required />
      </div>
      <button type="submit" class="full-width">
        Sign In
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
      </button>
    </form>
    
    <transition name="shake">
      <p v-if="error" class="error">{{ error }}</p>
    </transition>
  </section>
</template>

<style scoped>
.login-panel {
  max-width: 440px;
  margin: 0 auto;
}
.header {
  text-align: center;
  margin-bottom: 32px;
}
.header h2 {
  border: none;
  padding: 0;
  margin-bottom: 8px;
}
.subtitle {
  font-size: 14px;
  color: var(--text-muted);
}
.icon-circle {
  width: 56px;
  height: 56px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.input-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-muted);
}
.full-width {
  width: 100%;
  margin-top: 8px;
}

/* Error Shake */
.shake-enter-active {
  animation: shake 0.4s;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
</style>
