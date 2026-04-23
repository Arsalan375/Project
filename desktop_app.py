from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import requests


class TaskMasterDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Master (Desktop)")
        self.geometry("700x520")

        self.api_base = tk.StringVar(value="http://127.0.0.1:8000")
        self.text = tk.StringVar()

        top = tk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="API Base").pack(side="left")
        tk.Entry(top, textvariable=self.api_base, width=35).pack(side="left", padx=8)

        tk.Entry(self, textvariable=self.text, width=80)
        entry = tk.Entry(self, textvariable=self.text)
        entry.pack(fill="x", padx=10)
        entry.insert(0, "submit assignment tomorrow 9am")

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=10, pady=10)
        tk.Button(btns, text="Add (NLP)", command=self.add_task).pack(side="left")
        tk.Button(btns, text="Refresh", command=self.refresh).pack(side="left", padx=8)
        tk.Button(btns, text="Mark Done", command=self.mark_done).pack(side="left", padx=8)
        tk.Button(btns, text="Delete", command=self.delete_task).pack(side="left", padx=8)

        self.listbox = tk.Listbox(self, height=18)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.status = tk.StringVar(value="Start the API: uvicorn app.main:app --reload")
        tk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=10, pady=(0, 10))

        self.refresh()

    def _url(self, path: str) -> str:
        return f"{self.api_base.get().rstrip('/')}{path}"

    def refresh(self):
        self.listbox.delete(0, tk.END)
        try:
            r = requests.get(self._url("/tasks"), timeout=5)
            r.raise_for_status()
            self.tasks = r.json()
        except Exception as e:
            self.tasks = []
            self.status.set(f"API not reachable: {e}")
            return

        for t in self.tasks:
            due = t.get("due_at") or "—"
            self.listbox.insert(
                tk.END,
                f"[{t['id']}] {t['status']:<12} {t['title']}  | due: {due} | reminders: {t.get('reminder_count', 0)}",
            )
        self.status.set(f"Loaded {len(self.tasks)} tasks.")

    def add_task(self):
        text = self.text.get().strip()
        if not text:
            return
        try:
            r = requests.post(self._url("/tasks/from-text"), json={"text": text}, timeout=5)
            r.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add task: {e}")
            return
        self.text.set("")
        self.refresh()

    def _selected_task_id(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if idx >= len(self.tasks):
            return None
        return self.tasks[idx]["id"]

    def mark_done(self):
        task_id = self._selected_task_id()
        if task_id is None:
            messagebox.showinfo("Select a task", "Select a task first.")
            return
        try:
            r = requests.patch(self._url(f"/tasks/{task_id}"), json={"status": "done"}, timeout=5)
            r.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not update task: {e}")
            return
        self.refresh()

    def delete_task(self):
        task_id = self._selected_task_id()
        if task_id is None:
            messagebox.showinfo("Select a task", "Select a task first.")
            return
        if not messagebox.askyesno("Confirm delete", f"Delete task {task_id}?"):
            return
        try:
            r = requests.delete(self._url(f"/tasks/{task_id}"), timeout=5)
            r.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete task: {e}")
            return
        self.refresh()


if __name__ == "__main__":
    TaskMasterDesktop().mainloop()

