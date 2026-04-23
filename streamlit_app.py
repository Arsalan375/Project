from __future__ import annotations

from datetime import datetime, timedelta
import io
from urllib.parse import urlparse

import requests
import streamlit as st

st.set_page_config(page_title="Task Master Dashboard", page_icon="✅", layout="wide")

http = requests.Session()
REQUEST_TIMEOUT_SECONDS = 10


def normalize_api_base(raw: str) -> str:
    """
    Streamlit users often paste URLs with stray characters (e.g. http://127.0.0.1:8000),
    which breaks `requests` with: Failed to parse: ...
    """
    base = (raw or "").strip()
    base = base.rstrip("/").strip()

    # Remove common trailing junk from copy/paste mistakes
    while base.endswith(")"):
        base = base[:-1].rstrip()

    parsed = urlparse(base)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid API base URL: {raw!r}")

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


api_raw = st.sidebar.text_input(
    "FastAPI base URL (NOT Streamlit)",
    value="http://127.0.0.1:8000",
    help="This must point to your FastAPI server (uvicorn). Streamlit runs separately (usually :8501).",
)
st.sidebar.caption("Example: `http://127.0.0.1:8000` (do not use the Streamlit :8501 URL here).")
try:
    API_BASE = normalize_api_base(api_raw)
except Exception as e:
    st.sidebar.error(f"Bad API URL: {e}")
    st.stop()
st.markdown(
    """
    <style>
      .stApp {
        background: radial-gradient(circle at top, #1e293b 0%, #0f172a 45%, #020617 100%);
      }
      .tm-title {
        background: linear-gradient(120deg, #22d3ee, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.2rem;
      }
      .tm-sub {
        color: #cbd5e1;
        margin-bottom: 1rem;
      }
      .tm-card {
        border: 1px solid rgba(148,163,184,0.35);
        border-radius: 14px;
        padding: 14px;
        background: rgba(15, 23, 42, 0.55);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='tm-title'>Task Master Dashboard</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='tm-sub'>Smart tasks with NLP, reminders, and weekly insight.</div>",
    unsafe_allow_html=True,
)

st.info(
    "Mic tip: VS Code’s embedded Streamlit preview often **does not show** the microphone widget. "
    "Open the dashboard in **Chrome/Edge** using the URL Streamlit prints in the terminal (usually `http://localhost:8000`)."
)

st.subheader("Quick add (NLP)")
text = st.text_input("Type a task", placeholder="submit assignment tomorrow 9am")

st.subheader("Voice add (Streamlit mic)")
audio_bytes = st.audio_input("Record a short voice command", label_visibility="visible")
if audio_bytes is not None:
    try:
        import speech_recognition as sr  # type: ignore
    except Exception:
        st.error("Voice dependencies missing. Run: `pip install -r requirements.txt`")
    else:
        r = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(audio_bytes.getvalue())) as source:
                audio = r.record(source)
            transcript = r.recognize_google(audio)
            st.success(f"Heard: {transcript}")
            if st.button("Add from voice transcript"):
                try:
                    http.post(
                        f"{API_BASE}/tasks/from-text",
                        json={"text": transcript},
                        timeout=REQUEST_TIMEOUT_SECONDS,
                    ).raise_for_status()
                except Exception as e:
                    st.error(f"Could not add task via API: {e}")
                else:
                    st.rerun()
        except sr.UnknownValueError:
            st.warning("Could not understand audio. Try speaking closer to the mic and record again.")
        except sr.RequestError as e:
            st.warning(f"Speech recognition service error: {e}")
        except Exception as e:
            st.warning(
                "Could not read this recording as audio. If you installed deps recently, restart Streamlit. "
                "If it still fails, install FFmpeg (some browsers record formats that need conversion).\n\n"
                f"Details: {e}"
            )

col1, col2 = st.columns([1, 1])
with col1:
    add_btn = st.button("Add task")
with col2:
    refresh_btn = st.button("Refresh list")

if add_btn and text.strip():
    try:
        http.post(
            f"{API_BASE}/tasks/from-text",
            json={"text": text.strip()},
            timeout=REQUEST_TIMEOUT_SECONDS,
        ).raise_for_status()
    except Exception as e:
        st.error(f"Could not add task via API: {e}")
    else:
        st.rerun()


def fetch_tasks():
    r = http.get(f"{API_BASE}/tasks", timeout=REQUEST_TIMEOUT_SECONDS)
    r.raise_for_status()
    return r.json()


def parse_due(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return None


if refresh_btn:
    st.rerun()

st.subheader("Tasks")
try:
    tasks = fetch_tasks()
except Exception as e:
    st.error(
        "Could not reach API. Make sure FastAPI is running in a separate terminal:\n"
        "`uvicorn app.main:app --reload`\n\n"
        "Then verify `http://127.0.0.1:8000/docs` opens in your browser.\n\n"
        f"Current API base URL: `{API_BASE}`\n\n"
        f"Error: {e}"
    )
    st.stop()

if not tasks:
    st.info("No tasks yet.")
    st.stop()

now = datetime.now()

done_count = sum(1 for t in tasks if t["status"] == "done")
pending_count = sum(1 for t in tasks if t["status"] != "done")
overdue_count = sum(
    1
    for t in tasks
    if parse_due(t.get("due_at")) and parse_due(t.get("due_at")) < now and t["status"] != "done"
)

st.subheader("Next 7 Days Analytics")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total", len(tasks))
k2.metric("Done", done_count)
k3.metric("Pending", pending_count)
k4.metric("Overdue", overdue_count)

daily_labels = []
daily_counts = []
for i in range(7):
    day_start = (now + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    count = 0
    for t in tasks:
        due = parse_due(t.get("due_at"))
        if due and day_start <= due < day_end:
            count += 1
    daily_labels.append(day_start.strftime("%a %d"))
    daily_counts.append(count)

chart_data = [{"Day": d, "Tasks Due": c} for d, c in zip(daily_labels, daily_counts)]
st.bar_chart(chart_data, x="Day", y="Tasks Due", color="#22d3ee")

st.divider()
st.subheader("Task Board")

for t in tasks:
    with st.container(border=True):
        st.write(f"**{t['title']}**  —  `{t['status']}`")
        due = t.get("due_at")
        st.caption(
            f"due: {due or '—'} | reminders: {t.get('reminder_count', 0)} | id: {t['id']}"
        )

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Done", key=f"done-{t['id']}"):
                try:
                    http.patch(
                        f"{API_BASE}/tasks/{t['id']}",
                        json={"status": "done"},
                        timeout=REQUEST_TIMEOUT_SECONDS,
                    ).raise_for_status()
                except Exception as e:
                    st.error(f"Could not update task: {e}")
                else:
                    st.rerun()
        with c2:
            if st.button("Delete", key=f"del-{t['id']}"):
                try:
                    http.delete(
                        f"{API_BASE}/tasks/{t['id']}",
                        timeout=REQUEST_TIMEOUT_SECONDS,
                    ).raise_for_status()
                except Exception as e:
                    st.error(f"Could not delete task: {e}")
                else:
                    st.rerun()
        with c3:
            new_due = st.text_input(
                "Reschedule (YYYY-MM-DD HH:MM)",
                key=f"due-{t['id']}",
                placeholder="2026-04-20 09:00",
            )
            if st.button("Save due", key=f"save-due-{t['id']}") and new_due.strip():
                try:
                    dt = datetime.strptime(new_due.strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    st.error("Invalid date format. Use `YYYY-MM-DD HH:MM`, e.g. `2026-04-20 09:00`.")
                else:
                    try:
                        http.patch(
                            f"{API_BASE}/tasks/{t['id']}",
                            json={"due_at": dt.isoformat()},
                            timeout=REQUEST_TIMEOUT_SECONDS,
                        ).raise_for_status()
                    except Exception as e:
                        st.error(f"Could not reschedule task: {e}")
                    else:
                        st.rerun()
