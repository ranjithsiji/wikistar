<template>
  <div class="rule-card">
    <h2 class="rule-title">⚖️ Platform Rules</h2>

    <div v-if="loading" class="loading">Loading rules...</div>
    <div v-else>
      <div
        v-for="(rule, index) in rules"
        :key="index"
        class="rule-item"
      >
        <div class="rule-header">
          <h3>{{ rule.title }}</h3>
          <span class="rule-id">#{{ index + 1 }}</span>
        </div>
        <p>{{ rule.description }}</p>
      </div>
    </div>

    <button @click="fetchRules" class="refresh-btn">🔄 Refresh</button>
  </div>
</template>

<script>
export default {
  name: "RuleCard",
  data() {
    return {
      rules: [],
      loading: false,
    };
  },
  methods: {
    async fetchRules() {
      this.loading = true;
      try {
        // ✅ Replace this mock API with your backend endpoint later
        const res = await fetch("http://localhost:5000/api/rules");
        if (!res.ok) throw new Error("Failed to fetch rules");
        const data = await res.json();
        this.rules = data.rules || [];
      } catch (err) {
        console.error("Error fetching rules:", err);
        this.rules = [
          { title: "Respect all users", description: "No hate speech or harassment." },
          { title: "Share verified content", description: "Avoid sharing misinformation." },
          { title: "Keep discussions civil", description: "No spamming or personal attacks." },
        ];
      } finally {
        this.loading = false;
      }
    },
  },
  mounted() {
    this.fetchRules();
  },
};
</script>

<style scoped>
.rule-card {
  background: #f9fafb;
  border-radius: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
  max-width: 700px;
  margin: 2rem auto;
  transition: all 0.3s ease;
}

.rule-title {
  font-size: 1.8rem;
  color: #222;
  text-align: center;
  margin-bottom: 1.2rem;
  font-weight: 700;
}

.loading {
  text-align: center;
  color: #888;
  font-size: 1.1rem;
}

.rule-item {
  background: white;
  border-radius: 15px;
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid #e2e8f0;
  transition: transform 0.2s ease;
}

.rule-item:hover {
  transform: scale(1.02);
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}

.rule-header h3 {
  color: #1e293b;
  font-size: 1.2rem;
  margin: 0;
}

.rule-id {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.3rem 0.6rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.refresh-btn {
  display: block;
  margin: 1.5rem auto 0;
  padding: 0.7rem 1.5rem;
  font-size: 1rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.refresh-btn:hover {
  background-color: #1d4ed8;
}
</style>
