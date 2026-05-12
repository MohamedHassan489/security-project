"""Tkinter GUI client."""

from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import messagebox, ttk

from secure_suite.net.client import SecureClient


class SecureChatGUI:
    """Tkinter GUI that uses the shared client core."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9999) -> None:
        self.client = SecureClient(host=host, port=port)
        self.client.connect()
        self.root = tk.Tk()
        self.root.title("Secure Communication Suite")
        self.root.geometry("700x500")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.recipient_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.known_recipients = ["alice", "bob", "charlie"]
        self.login_frame = ttk.Frame(self.root, padding=16)
        self.chat_frame = ttk.Frame(self.root, padding=16)
        self.history = tk.Text(self.chat_frame, height=18, width=70, state="disabled")
        self._build_login()
        self._build_chat()
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_login(self) -> None:
        ttk.Label(self.login_frame, text="Username").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(self.login_frame, textvariable=self.username_var, width=32).grid(
            row=0, column=1, sticky="ew", pady=4
        )
        ttk.Label(self.login_frame, text="Password").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self.login_frame, textvariable=self.password_var, width=32, show="*").grid(
            row=1, column=1, sticky="ew", pady=4
        )
        ttk.Button(self.login_frame, text="Register", command=self.register).grid(
            row=2, column=0, sticky="ew", pady=8
        )
        ttk.Button(self.login_frame, text="Login", command=self.login).grid(
            row=2, column=1, sticky="ew", pady=8
        )

    def _build_chat(self) -> None:
        self.history.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=(0, 12))
        ttk.Label(self.chat_frame, text="Recipient").grid(row=1, column=0, sticky="w")
        recipient_combo = ttk.Combobox(
            self.chat_frame,
            textvariable=self.recipient_var,
            values=self.known_recipients,
            width=20,
        )
        recipient_combo.grid(row=1, column=1, sticky="ew", padx=(0, 12))
        recipient_combo["state"] = "normal"
        ttk.Entry(self.chat_frame, textvariable=self.message_var, width=42).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=8
        )
        ttk.Button(self.chat_frame, text="Send", command=self.send_message).grid(
            row=2, column=2, sticky="ew", pady=8
        )
        ttk.Button(self.chat_frame, text="Refresh", command=self.refresh_messages).grid(
            row=1, column=2, sticky="ew"
        )
        ttk.Button(self.chat_frame, text="Logout", command=self.logout).grid(
            row=3, column=2, sticky="ew"
        )
        self.chat_frame.columnconfigure(1, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

    def show_login(self) -> None:
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_chat(self) -> None:
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.root.after(1000, self._poll_messages)

    def append_history(self, line: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", line + "\n")
        self.history.see("end")
        self.history.configure(state="disabled")

    def register(self) -> None:
        try:
            result = self.client.register(self.username_var.get().strip(), self.password_var.get())
            messagebox.showinfo("Register", result["status"])
        except Exception as exc:
            messagebox.showerror("Register", str(exc))

    def login(self) -> None:
        try:
            result = self.client.login(self.username_var.get().strip(), self.password_var.get())
            self.append_history(f'Logged in as {self.username_var.get().strip()}')
            messagebox.showinfo("Login", result["status"])
            self.show_chat()
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
            messagebox.showwarning("Send", "Recipient and message are required.")
            return
        try:
            self.client.send_message(recipient, text)
            if recipient not in self.known_recipients:
                self.known_recipients.append(recipient)
            self.append_history(f"You -> {recipient}: {text}")
            self.message_var.set("")
        except Exception as exc:
            messagebox.showerror("Send", str(exc))

    def refresh_messages(self) -> None:
        try:
            messages = self.client.fetch_messages()
            for message in messages:
                status = message.get("integrity", "?")
                self.append_history(f'[{status}] {message["from"]}: {message["text"]}')
        except Exception as exc:
            messagebox.showerror("Refresh", str(exc))

    def _poll_messages(self) -> None:
        if self.client.auth is None:
            return
        try:
            messages = self.client.fetch_messages()
            for message in messages:
                status = message.get("integrity", "?")
                self.append_history(f'[{status}] {message["from"]}: {message["text"]}')
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
