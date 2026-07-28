<template>
  <div class="chat-page">
    <!-- 标题栏 -->
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon">📊</span>
        <h1 class="app-title">智库问答助手</h1>
      </div>
      <p class="app-subtitle">智能数据查询与分析平台</p>
    </header>

    <!-- 消息区 -->
    <div ref="messagesEl" class="messages">
      <!-- 自我介绍（每次刷新都显示） -->
      <div v-if="showIntro" class="intro-card">
        <div class="intro-avatar">🤖</div>
        <div class="intro-content">
          <h3>你好，我是智库问答助手</h3>
          <p>我可以帮你查询数据库、分析数据。请直接输入你的问题，我会自动理解并执行。</p>
          <div class="intro-examples">
            <span class="intro-tag" @click="setQuestion('统计上海地区的销售总额')">📈 统计销售额</span>
            <span class="intro-tag" @click="setQuestion('查看最近7天的订单量')">📋 查看订单</span>
            <span class="intro-tag" @click="setQuestion('各产品类别的占比情况')">📊 数据分析</span>
          </div>
        </div>
        <button class="intro-close" @click="showIntro = false">✕</button>
      </div>

      <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-row', msg.role]"
      >
        <div v-if="msg.role === 'assistant'" class="avatar assistant-avatar">🤖</div>

        <div class="bubble">
          <!-- 文本 -->
          <div v-if="msg.type === 'text'">
            {{ msg.content }}
          </div>

          <!-- 进度步骤 -->
          <div v-else-if="msg.type === 'steps'" class="steps">
            <div v-for="(step, sIdx) in msg.steps" :key="sIdx" class="step">
              <span class="dot" :class="step.status"></span>
              <span class="step-text">{{ step.text }}</span>
            </div>
          </div>

          <!-- 表格 -->
          <div v-else-if="msg.type === 'table'" class="table-wrap">
            <div class="table-title">📋 查询结果</div>
            <table class="result-table">
              <thead>
              <tr>
                <th v-for="col in msg.columns" :key="col">
                  {{ col }}
                </th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="(row, rIdx) in msg.rows" :key="rIdx">
                <td v-for="col in msg.columns" :key="col">
                  {{ row[col] }}
                </td>
              </tr>
              </tbody>
            </table>
          </div>

          <!-- 错误 -->
          <div v-else-if="msg.type === 'error'" class="error-text">
            <span class="error-icon">⚠️</span>
            {{ msg.content }}
          </div>
        </div>

        <div v-if="msg.role === 'user'" class="avatar user-avatar">🧑</div>
      </div>
      <div class="messages-bottom-spacer"></div>
    </div>

    <!-- 悬浮输入框 -->
    <div class="input-wrapper">
      <div class="input-box">
        <input
            v-model="question"
            @keyup.enter="sendQuestion"
            placeholder="请输入你的问题，例如：统计上海地区的销售总额..."
        />
        <button @click="sendQuestion" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>发送</span>
        </button>
      </div>
      <p class="input-hint">按 Enter 发送，支持自然语言查询数据库</p>
    </div>
  </div>
</template>

<script setup>
import {nextTick, ref} from "vue";

const API_URL = "/api/query";

const question = ref("");
const loading = ref(false);
const messages = ref([]);
const messagesEl = ref(null);
const showIntro = ref(true);  // ✅ 每次刷新都显示

function setQuestion(text) {
  question.value = text;
  sendQuestion();
}

function scrollToBottom() {
  const el = messagesEl.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

async function sendQuestion() {
  if (!question.value || loading.value) return;

  const q = question.value;
  question.value = "";
  loading.value = true;

  // 发送问题时隐藏自我介绍
  showIntro.value = false;

  messages.value.push({role: "user", type: "text", content: q});

  // steps 容器
  const stepIndex =
      messages.value.push({
        role: "assistant",
        type: "steps",
        steps: [],
      }) - 1;

  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({query: q}),
    });

    if (!response.body) throw new Error("服务器未返回流");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const {value, done} = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, {stream: true});
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        const line = evt.trim();
        if (!line.startsWith("data:")) continue;

        const rawData = line.replace(/^data:\s*/, "");
        let data;

        try {
          data = JSON.parse(rawData);
        } catch {
          data = {
            type: "progress",
            step: rawData.replace(/^"|"$/g, ""),
            status: "running",
          };
        }

        const steps = messages.value[stepIndex].steps;

        if (data.type === "progress" && data.step) {
          let step = steps.find((s) => s.text === data.step);
          if (!step) {
            steps.push({
              text: data.step,
              status: data.status || "running",
            });
          } else {
            step.status = data.status || "running";
          }
        } else if (typeof data === "string") {
          const stepText = data.replace(/^"|"$/g, "");
          let step = steps.find((s) => s.text === stepText);
          if (!step) {
            steps.push({
              text: stepText,
              status: "running",
            });
          }
        } else if (data.type === "result" && Array.isArray(data.data)) {
          messages.value.push({
            role: "assistant",
            type: "table",
            columns: Object.keys(data.data[0] || {}),
            rows: data.data,
          });
        } else if (data.type === "error") {
          messages.value.push({
            role: "assistant",
            type: "error",
            content: data.message || "发生错误",
          });
        }

        await nextTick();
        scrollToBottom();
      }
    }
  } catch (e) {
    messages.value.push({
      role: "assistant",
      type: "error",
      content: e?.message || "请求失败",
    });
  } finally {
    loading.value = false;
    await nextTick();
    scrollToBottom();
  }
}
</script>

<style scoped>
/* 覆盖 Vite 默认居中 */
:global(html),
:global(body) {
  height: 100%;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

:global(body) {
  display: block !important;
  place-items: unset !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

:global(#app) {
  height: 100%;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 页面 */
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 标题栏 */
.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
  z-index: 10;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.app-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #888;
}

/* 消息区 */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20% 180px;
  background: linear-gradient(180deg, #f8f9ff 0%, #ffffff 100%);
}

/* 自我介绍卡片 */
.intro-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: linear-gradient(135deg, #667eea15, #764ba215);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  position: relative;
  animation: slideIn 0.5s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.intro-avatar {
  font-size: 36px;
  flex-shrink: 0;
}

.intro-content h3 {
  margin: 0 0 8px;
  color: #333;
  font-size: 16px;
}

.intro-content p {
  margin: 0 0 12px;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.intro-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.intro-tag {
  display: inline-block;
  padding: 6px 14px;
  background: #fff;
  border: 1px solid #667eea;
  border-radius: 20px;
  font-size: 13px;
  color: #667eea;
  cursor: pointer;
  transition: all 0.2s;
}

.intro-tag:hover {
  background: #667eea;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.intro-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  font-size: 16px;
  color: #999;
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.intro-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

/* 消息行 */
.message-row {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-row.user {
  justify-content: flex-end;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin: 0 10px;
  flex-shrink: 0;
}

.assistant-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.user-avatar {
  background: linear-gradient(135deg, #11998e, #38ef7d);
  box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
}

.bubble {
  max-width: min(820px, 72%);
  padding: 14px 18px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  line-height: 1.6;
  font-size: 14px;
  color: #333;
}

.message-row.user .bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

/* 步骤 */
.steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.dot.running {
  background: #f1c40f;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.dot.success {
  background: #2ecc71;
}

.dot.error {
  background: #e74c3c;
}

.step-text {
  color: #555;
  font-size: 13px;
}

/* 表格 */
.table-wrap {
  max-width: 100%;
  overflow-x: auto;
}

.table-title {
  font-size: 13px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.result-table {
  width: max-content;
  min-width: 100%;
  table-layout: auto;
  border-collapse: collapse;
  font-size: 13px;
}

.result-table th,
.result-table td {
  border: 1px solid #e8e8e8;
  padding: 10px 14px;
  white-space: nowrap;
  text-align: left;
}

.result-table th {
  background: linear-gradient(135deg, #667eea08, #764ba208);
  font-weight: 600;
  color: #555;
  position: sticky;
  top: 0;
  z-index: 1;
}

.result-table tr:nth-child(even) {
  background: #fafbfc;
}

.result-table tr:hover {
  background: #f0f4ff;
}

/* 错误 */
.error-text {
  color: #e74c3c;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-icon {
  font-size: 16px;
}

/* 悬浮输入框 */
.input-wrapper {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 20px 24px;
  background: linear-gradient(to top, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.8) 70%, transparent 100%);
  pointer-events: none;
}

.input-box {
  pointer-events: auto;
  width: 100%;
  max-width: 720px;
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 28px;
  background: #fff;
  border: 1px solid rgba(102, 126, 234, 0.15);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.12);
  transition: box-shadow 0.3s;
}

.input-box:focus-within {
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.3);
}

.input-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: #333;
}

.input-box input::placeholder {
  color: #aaa;
}

.input-box button {
  padding: 10px 24px;
  border-radius: 20px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.input-box button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.input-box button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.input-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #999;
  pointer-events: auto;
}

.messages-bottom-spacer {
  height: 160px;
}
</style>