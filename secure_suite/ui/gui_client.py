"""Tkinter GUI client."""

from __future__ import annotations

import argparse
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from secure_suite.net.client import SecureClient


BG_MAIN       = "#f0f2f5"
BG_HEADER     = "#1a73e8"
BG_CARD       = "#ffffff"
BG_INPUT      = "#e8eaed"
COLOR_SENT    = "#1a73e8"
COLOR_RECV    = "#202124"
COLOR_OK      = "#188038"
COLOR_TAMPER  = "#d93025"
COLOR_MUTED   = "#80868b"
FONT          = ("Segoe UI", 11)
FONT_BOLD     = ("Segoe UI", 11, "bold")
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_HEADER   = ("Segoe UI", 12, "bold")
FONT_MONO     = ("Consolas", 10)
FONT_ITALIC   = ("Segoe UI", 10, "italic")


class SecureChatGUI:
    """Tkinter GUI that uses the shared client core."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9999) -> None:
        self.client = SecureClient(host=host, port=port)
        self.client.connect()

        self.root = tk.Tk()
        self.root.title("Secure Communication Suite")
        self.root.geometry("1100x700")
        self.root.minsize(800, 560)
        self.root.state("zoomed")
        self.root.configure(bg=BG_MAIN)

        self.username_var  = tk.StringVar()
        self.password_var  = tk.StringVar()
        self.recipient_var = tk.StringVar()
        self.message_var   = tk.StringVar()
        self.status_var    = tk.StringVar(value="Connected")
        self.known_recipients: list[str] = []

        self._build_login()
        self._build_chat()
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ── Login screen ─────────────────────────────────────────────────────────

    def _build_login(self) -> None:
        self.login_frame = tk.Frame(self.root, bg=BG_MAIN)

        card = tk.Frame(self.login_frame, bg=BG_CARD, padx=44, pady=36)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Secure Chat", font=FONT_TITLE,
                 bg=BG_CARD, fg=BG_HEADER).grid(
            row=0, column=0, columnspan=2, pady=(0, 6))
        tk.Label(card, text="End-to-end encrypted messaging",
                 font=FONT_ITALIC, bg=BG_CARD, fg=COLOR_MUTED).grid(
            row=1, column=0, columnspan=2, pady=(0, 24))

        for row, label, var, kw in [
            (2, "Username", self.username_var, {}),
            (4, "Password", self.password_var, {"show": "●"}),
        ]:
            tk.Label(card, text=label, font=FONT, bg=BG_CARD,
                     fg="#5f6368").grid(row=row, column=0, columnspan=2,
                                        sticky="w", pady=(0, 2))
            e = ttk.Entry(card, textvariable=var, width=30, **kw)
            e.grid(row=row + 1, column=0, columnspan=2, sticky="ew",
                   pady=(0, 14), ipady=5)
            if row == 2:
                self.username_entry = e
            else:
                self.password_entry = e

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        tk.Button(btn_row, text="Login", command=self.login,
                  bg=BG_HEADER, fg="white", font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=24, pady=7).pack(
            side="left", expand=True, fill="x", padx=(0, 6))

        tk.Button(btn_row, text="Register", command=self.register,
                  bg=BG_CARD, fg=BG_HEADER, font=FONT_BOLD,
                  relief="solid", bd=1, cursor="hand2", padx=24, pady=7).pack(
            side="left", expand=True, fill="x", padx=(6, 0))

        self.username_entry.bind("<Return>", lambda _: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda _: self.login())

    # ── Chat screen ───────────────────────────────────────────────────────────

    def _build_chat(self) -> None:
        self.chat_frame = tk.Frame(self.root, bg=BG_MAIN)

        # Header
        header = tk.Frame(self.chat_frame, bg=BG_HEADER, pady=10, padx=16)
        header.pack(fill="x")
        self.header_label = tk.Label(header, text="", font=FONT_HEADER,
                                     bg=BG_HEADER, fg="white")
        self.header_label.pack(side="left")
        tk.Button(header, text="Logout", command=self.logout,
                  bg="white", fg=BG_HEADER, font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=12, pady=3).pack(side="right")

        # Message history
        hist_frame = tk.Frame(self.chat_frame, bg=BG_MAIN, padx=16, pady=12)
        hist_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(hist_frame)
        scrollbar.pack(side="right", fill="y")

        self.history = tk.Text(
            hist_frame, state="disabled", wrap="word",
            font=FONT, bg="white", relief="flat",
            yscrollcommand=scrollbar.set,
            padx=12, pady=10, spacing1=2, spacing3=5,
        )
        self.history.pack(fill="both", expand=True)
        scrollbar.config(command=self.history.yview)

        self.history.tag_config("sent",    foreground=BG_HEADER,   font=FONT_BOLD)
        self.history.tag_config("recv",    foreground=COLOR_RECV,   font=FONT_BOLD)
        self.history.tag_config("ok",      foreground=COLOR_OK)
        self.history.tag_config("tamper",  foreground=COLOR_TAMPER, font=FONT_BOLD)
        self.history.tag_config("time",    foreground=COLOR_MUTED,  font=FONT_MONO)
        self.history.tag_config("system",  foreground=COLOR_MUTED,  font=FONT_ITALIC)

        # Input bar
        input_bar = tk.Frame(self.chat_frame, bg=BG_INPUT, padx=16, pady=14)
        input_bar.pack(fill="x")

        tk.Label(input_bar, text="To:", font=FONT,
                 bg=BG_INPUT, fg="#5f6368").grid(row=0, column=0, padx=(0, 4))

        self.recipient_combo = ttk.Combobox(
            input_bar, textvariable=self.recipient_var,
            values=self.known_recipients, width=14, font=FONT,
        )
        self.recipient_combo.grid(row=0, column=1, padx=(0, 10))

        self.message_entry = ttk.Entry(input_bar, textvariable=self.message_var, font=FONT)
        self.message_entry.grid(row=0, column=2, sticky="ew", padx=(0, 10))
        self.message_entry.bind("<Return>", lambda _: self.send_message())

        tk.Button(input_bar, text="Send  ➤", command=self.send_message,
                  bg=BG_HEADER, fg="white", font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=14, pady=5).grid(row=0, column=3)

        input_bar.columnconfigure(2, weight=1)

        # Status bar
        tk.Label(self.chat_frame, textvariable=self.status_var,
                 font=("Segoe UI", 8), bg="#dadce0", fg=COLOR_MUTED,
                 anchor="w", padx=10, pady=3).pack(fill="x")

    # ── Navigation ────────────────────────────────────────────────────────────

    def show_login(self) -> None:
        self.chat_frame.pack_forget()
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.configure(state="disabled")
        self.username_var.set("")
        self.password_var.set("")
        self.login_frame.pack(fill="both", expand=True)
        self.root.title("Secure Communication Suite")
        self.root.after(100, self.username_entry.focus)

    def show_chat(self, username: str) -> None:
        self.login_frame.pack_forget()
        self.header_label.config(text=f"  {username}")
        self.root.title(f"Secure Chat — {username}")
        self.chat_frame.pack(fill="both", expand=True)
        self._system(f"Logged in as {username}")
        self.root.after(100, self.message_entry.focus)
        self.root.after(1000, self._poll_messages)

    # ── History helpers ───────────────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M")

    def _system(self, text: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"  {text}  \n", "system")
        self.history.see("end")
        self.history.configure(state="disabled")

    def _append_sent(self, recipient: str, text: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"{self._now()}  ", "time")
        self.history.insert("end", f"You → {recipient}  ", "sent")
        self.history.insert("end", text + "\n")
        self.history.see("end")
        self.history.configure(state="disabled")

    def _append_received(self, sender: str, text: str, integrity: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"{self._now()}  ", "time")
        self.history.insert("end", f"{sender}  ", "recv")
        self.history.insert("end", text)
        if integrity == "verified":
            self.history.insert("end", "  ✓\n", "ok")
        else:
            self.history.insert("end", f"  ⚠ {integrity}\n", "tamper")
        self.history.see("end")
        self.history.configure(state="disabled")

    # ── Actions ───────────────────────────────────────────────────────────────

    def register(self) -> None:
        try:
            self.client.register(self.username_var.get().strip(), self.password_var.get())
            messagebox.showinfo("Register", "Account created. You can now log in.")
        except Exception as exc:
            messagebox.showerror("Register", str(exc))

    def login(self) -> None:
        username = self.username_var.get().strip()
        try:
            self.client.login(username, self.password_var.get())
            self.password_var.set("")
            self.show_chat(username)
        except Exception as exc:
            messagebox.showerror("Login", str(exc))

    def logout(self) -> None:
        host, port = self.client.host, self.client.port
        try:
            self.client.logout()
        except Exception:
            pass
        self.client.close()
        self.client = SecureClient(host=host, port=port)
        try:
            self.client.connect()
        except Exception as exc:
            messagebox.showerror("Connection", f"Failed to reconnect: {exc}")
            return
        self.show_login()

    def send_message(self) -> None:
        recipient = self.recipient_var.get().strip()
        text = self.message_var.get().strip()
        if not recipient or not text:
            return
        try:
            self.client.send_message(recipient, text)
            if recipient not in self.known_recipients:
                self.known_recipients.append(recipient)
                self.recipient_combo["values"] = self.known_recipients
            self._append_sent(recipient, text)
            self.message_var.set("")
            self.status_var.set(f"Message sent to {recipient}")
        except Exception as exc:
            messagebox.showerror("Send", str(exc))

    def _poll_messages(self) -> None:
        if self.client.auth is None:
            return
        try:
            messages = self.client.fetch_messages()
            for msg in messages:
                self._append_received(msg["from"], msg["text"], msg.get("integrity", "?"))
            if messages:
                self.status_var.set(f"Received {len(messages)} new message(s)")
        except Exception:
            pass
        self.root.after(1000, self._poll_messages)

    def on_close(self) -> None:
        self.client.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Secure Communication Suite GUI client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    args = parser.parse_args(argv)
    app = SecureChatGUI(args.host, args.port)
    app.run()
    return 0
