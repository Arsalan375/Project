from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
def home():
    # Styled web interface with browser voice input + 7-day analytics.
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Task Master</title>
    <style>
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --panel-soft: #1f2937;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent: #22d3ee;
        --accent-2: #a78bfa;
        --good: #34d399;
        --warn: #f59e0b;
      }
      * { box-sizing: border-box; }
      body {
        font-family: system-ui, Arial;
        background: radial-gradient(circle at top, #1e293b, #0b1020 60%);
        color: var(--text);
        margin: 0;
      }
      .wrap { max-width: 1000px; margin: 28px auto; padding: 0 16px; }
      .hero {
        background: linear-gradient(135deg, rgba(34,211,238,0.25), rgba(167,139,250,0.2));
        border: 1px solid rgba(229,231,235,0.15);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 16px;
      }
      .hero h2 { margin: 0 0 6px; }
      .muted { color: var(--muted); font-size: 13px; }
      .row { display: flex; gap: 8px; flex-wrap: wrap; }
      input, button {
        font-size: 14px;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid rgba(229,231,235,0.15);
        background: var(--panel-soft);
        color: var(--text);
      }
      input { flex: 1; min-width: 250px; }
      button { cursor: pointer; }
      .btn-accent { background: linear-gradient(120deg, var(--accent), var(--accent-2)); color: #0b1020; font-weight: 700; border: none; }
      .section {
        background: rgba(17,24,39,0.8);
        border: 1px solid rgba(229,231,235,0.12);
        border-radius: 14px;
        padding: 14px;
        margin-top: 14px;
      }
      .kpis { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; }
      .kpi {
        background: rgba(31,41,55,0.85);
        border-radius: 12px;
        padding: 12px;
      }
      .kpi .num { font-size: 24px; font-weight: 800; }
      .cards { margin-top: 6px; }
      .card {
        border: 1px solid rgba(229,231,235,0.12);
        background: rgba(31,41,55,0.72);
        border-radius: 12px;
        padding: 12px;
        margin: 10px 0;
      }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; background: rgba(34,211,238,0.18); font-size: 12px; }
      .line { display: flex; justify-content: space-between; gap: 8px; }
      .chart-row { display: grid; grid-template-columns: 80px 1fr 50px; align-items: center; gap: 10px; margin: 8px 0; }
      .bar-bg { height: 10px; border-radius: 999px; background: rgba(229,231,235,0.1); overflow: hidden; }
      .bar { height: 10px; background: linear-gradient(120deg, var(--good), var(--accent)); }
      .warn { color: var(--warn); }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="hero">
        <h2>Task Master - Smart Planner</h2>
        <p class="muted">Try: <b>submit assignment tomorrow 9am</b> or use the mic for voice input.</p>

        <div class="row">
          <input id="text" placeholder="Add task (NLP)..." />
          <button class="btn-accent" onclick="add()">Add</button>
          <button onclick="toggleVoice()">🎤 Voice</button>
          <button onclick="load()">Refresh</button>
        </div>
        <p id="voiceStatus" class="muted"></p>
      </div>

      <div class="section">
        <h3>Next 7 Days Analytics</h3>
        <div class="kpis">
          <div class="kpi"><div class="muted">Total</div><div id="kTotal" class="num">0</div></div>
          <div class="kpi"><div class="muted">Done</div><div id="kDone" class="num">0</div></div>
          <div class="kpi"><div class="muted">Pending</div><div id="kPending" class="num">0</div></div>
          <div class="kpi"><div class="muted">Overdue</div><div id="kOverdue" class="num warn">0</div></div>
        </div>
        <div id="weekChart" style="margin-top:10px;"></div>
      </div>

      <div class="section">
        <h3>Tasks</h3>
        <div id="list" class="cards"></div>
      </div>
    </div>

    <script>
      let recognition = null;

      function formatDateLabel(d) {
        return d.toLocaleDateString(undefined, { weekday: 'short', day: '2-digit' });
      }

      function buildAnalytics(tasks) {
        const now = new Date();
        const total = tasks.length;
        const done = tasks.filter(t => t.status === 'done').length;
        const overdue = tasks.filter(t => t.due_at && new Date(t.due_at) < now && t.status !== 'done').length;
        const pending = total - done;

        document.getElementById('kTotal').textContent = total;
        document.getElementById('kDone').textContent = done;
        document.getElementById('kPending').textContent = pending;
        document.getElementById('kOverdue').textContent = overdue;

        const days = [];
        for (let i = 0; i < 7; i++) {
          const d = new Date(now);
          d.setDate(now.getDate() + i);
          d.setHours(0, 0, 0, 0);
          days.push(d);
        }

        const counts = days.map(day => {
          const next = new Date(day);
          next.setDate(day.getDate() + 1);
          return tasks.filter(t => {
            if (!t.due_at) return false;
            const due = new Date(t.due_at);
            return due >= day && due < next;
          }).length;
        });

        const maxCount = Math.max(1, ...counts);
        const chart = document.getElementById('weekChart');
        chart.innerHTML = days.map((d, i) => `
          <div class="chart-row">
            <div class="muted">${formatDateLabel(d)}</div>
            <div class="bar-bg"><div class="bar" style="width:${(counts[i] / maxCount) * 100}%"></div></div>
            <div class="muted">${counts[i]}</div>
          </div>
        `).join('');
      }

      async function load() {
        const res = await fetch('/tasks');
        const tasks = await res.json();
        buildAnalytics(tasks);
        const root = document.getElementById('list');
        root.innerHTML = '';
        for (const t of tasks) {
          const el = document.createElement('div');
          el.className = 'card';
          el.innerHTML = `
            <div class="line">
              <div><b>${t.title}</b></div>
              <div class="pill">${t.status}</div>
            </div>
            <div class="muted">due: ${t.due_at ?? '—'} | reminders: ${t.reminder_count ?? 0}</div>
            <div style="margin-top: 10px; display:flex; gap: 8px; flex-wrap: wrap;">
              <button class="btn-accent" onclick="markDone(${t.id})">Mark done</button>
              <button onclick="del(${t.id})">Delete</button>
            </div>
          `;
          root.appendChild(el);
        }
      }

      async function add() {
        const text = document.getElementById('text').value.trim();
        if (!text) return;
        await fetch('/tasks/from-text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
        document.getElementById('text').value = '';
        await load();
      }

      function toggleVoice() {
        const status = document.getElementById('voiceStatus');
        const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!Ctor) {
          status.textContent = 'Voice input is not supported in this browser. Use Chrome/Edge.';
          return;
        }

        if (!recognition) {
          recognition = new Ctor();
          recognition.lang = 'en-US';
          recognition.continuous = false;
          recognition.interimResults = false;
          recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript || '';
            document.getElementById('text').value = transcript;
            status.textContent = `Heard: "${transcript}"`;
          };
          recognition.onerror = () => {
            status.textContent = 'Could not capture voice. Please try again.';
          };
          recognition.onend = () => {
            if (!status.textContent) status.textContent = 'Voice input stopped.';
          };
        }

        status.textContent = 'Listening... speak your task.';
        recognition.start();
      }

      async function markDone(id) {
        await fetch(`/tasks/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'done' }) });
        await load();
      }

      async function del(id) {
        await fetch(`/tasks/${id}`, { method: 'DELETE' });
        await load();
      }

      load();
    </script>
  </body>
</html>
"""

