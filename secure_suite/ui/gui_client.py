"""Tkinter GUI client."""

from __future__ import annotations

import argparse
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from secure_suite.net.client import SecureClient


# Warm, eye-comfortable palette
BG_MAIN       = "#ECE5DD"   # warm parchment
BG_HEADER     = "#075E54"   # deep teal
BG_HEADER2    = "#128C7E"   # medium teal (accents)
BG_SIDEBAR    = "#F7F3EE"   # warm cream
BG_CARD       = "#FFFFFF"
BG_INPUT      = "#F0F0F0"
BG_SENT       = "#DCF8C6"   # soft green bubble
BG_RECV       = "#FFFFFF"   # white bubble
COLOR_MUTED   = "#8696A0"   # warm grey
COLOR_OK      = "#53BDEB"   # light blue tick
COLOR_TAMPER  = "#C0392B"   # muted red

FONT          = ("Segoe UI", 9)
FONT_BOLD     = ("Segoe UI", 9, "bold")
FONT_TITLE    = ("Segoe UI", 15, "bold")
FONT_HEADER   = ("Segoe UI", 10, "bold")
FONT_MONO     = ("Segoe UI", 7)
FONT_ITALIC   = ("Segoe UI", 8, "italic")


class SecureChatGUI:
    """Tkinter GUI that uses the shared client core."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9999) -> None:
        self.client = SecureClient(host=host, port=port)
        self.client.connect()

        self.root = tk.Tk()
        self.root.title("Secure Chat")
        self.root.geometry("390x780")
        self.root.minsize(360, 640)
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)

        self.username_var    = tk.StringVar()
        self.password_var    = tk.StringVar()
        self.recipient_var   = tk.StringVar()
        self.new_contact_var = tk.StringVar()
        self.status_var      = tk.StringVar(value="  Connected")
        self.known_recipients: list[str] = []

        self._build_login()
        self._build_chat()
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ── Login ─────────────────────────────────────────────────────────────────

    def _build_login(self) -> None:
        self.login_frame = tk.Frame(self.root, bg=BG_MAIN)

        card = tk.Frame(self.login_frame, bg=BG_CARD, padx=36, pady=36)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(card, text="SecureChat", font=FONT_TITLE,
                 bg=BG_CARD, fg=BG_HEADER).grid(
            row=0, column=0, columnspan=2, pady=(0, 4))
        tk.Label(card, text="End-to-end encrypted", font=FONT_ITALIC,
                 bg=BG_CARD, fg=COLOR_MUTED).grid(
            row=1, column=0, columnspan=2, pady=(0, 26))

        # Fields
        for row, label, var, kw in [
            (2, "Username", self.username_var, {}),
            (4, "Password", self.password_var, {"show": "●"}),
        ]:
            tk.Label(card, text=label, font=FONT, bg=BG_CARD,
                     fg="#555").grid(row=row, column=0, columnspan=2,
                                     sticky="w", pady=(0, 2))
            e = ttk.Entry(card, textvariable=var, width=28, **kw)
            e.grid(row=row + 1, column=0, columnspan=2, sticky="ew",
                   pady=(0, 14), ipady=6)
            if row == 2:
                self.username_entry = e
            else:
                self.password_entry = e

        # Buttons
        row_btns = tk.Frame(card, bg=BG_CARD)
        row_btns.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        tk.Button(row_btns, text="Login", command=self.login,
                  bg=BG_HEADER, fg="white", font=FONT_BOLD,
                  relief="flat", cursor="hand2", pady=8).pack(
            side="left", expand=True, fill="x", padx=(0, 5))

        tk.Button(row_btns, text="Register", command=self.register,
                  bg=BG_HEADER2, fg="white", font=FONT_BOLD,
                  relief="flat", cursor="hand2", pady=8).pack(
            side="left", expand=True, fill="x", padx=(5, 0))

        self.username_entry.bind("<Return>", lambda _: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda _: self.login())

    # ── Chat ──────────────────────────────────────────────────────────────────

    def _build_chat(self) -> None:
        self.chat_frame = tk.Frame(self.root, bg=BG_MAIN)

        # Header
        header = tk.Frame(self.chat_frame, bg=BG_HEADER, pady=11, padx=14)
        header.pack(fill="x")
        self.header_label = tk.Label(
            header, text="", font=FONT_HEADER, bg=BG_HEADER, fg="white")
        self.header_label.pack(side="left")
        tk.Button(header, text="Logout", command=self.logout,
                  bg=BG_HEADER2, fg="white", font=FONT,
                  relief="flat", cursor="hand2", padx=10, pady=2).pack(side="right")

        # Body
        body = tk.Frame(self.chat_frame, bg=BG_MAIN)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(body, bg=BG_SIDEBAR, width=105)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Contacts", font=FONT_BOLD,
                 bg=BG_SIDEBAR, fg=BG_HEADER, pady=9).pack(fill="x", padx=10)

        tk.Frame(sidebar, bg="#D0CCC8", height=1).pack(fill="x")

        self.contacts_box = tk.Listbox(
            sidebar, font=FONT, relief="flat", bd=0,
            bg=BG_SIDEBAR, fg="#303030",
            selectbackground=BG_HEADER2, selectforeground="white",
            activestyle="none", cursor="hand2",
            highlightthickness=0,
        )
        self.contacts_box.pack(fill="both", expand=True, padx=4, pady=6)
        self.contacts_box.bind("<<ListboxSelect>>", self._on_contact_select)

        tk.Frame(sidebar, bg="#D0CCC8", height=1).pack(fill="x")

        add_frame = tk.Frame(sidebar, bg=BG_SIDEBAR, padx=6, pady=7)
        add_frame.pack(fill="x")
        new_entry = ttk.Entry(add_frame, textvariable=self.new_contact_var, font=FONT)
        new_entry.pack(fill="x", ipady=3, pady=(0, 5))
        new_entry.bind("<Return>", lambda _: self._add_contact())
        tk.Button(add_frame, text="+ Add", command=self._add_contact,
                  bg=BG_HEADER, fg="white", font=FONT,
                  relief="flat", cursor="hand2", pady=3).pack(fill="x")

        # ── Main area ────────────────────────────────────────────────────────
        main = tk.Frame(body, bg=BG_MAIN)
        main.pack(side="left", fill="both", expand=True)

        # Message history
        hist_wrap = tk.Frame(main, bg=BG_MAIN, padx=6, pady=6)
        hist_wrap.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(hist_wrap)
        sb.pack(side="right", fill="y")

        self.history = tk.Text(
            hist_wrap, state="disabled", wrap="word",
            font=FONT, bg=BG_MAIN, relief="flat",
            yscrollcommand=sb.set, bd=0,
            padx=4, pady=6, spacing1=2, spacing3=2,
        )
        self.history.pack(fill="both", expand=True)
        sb.config(command=self.history.yview)

        # Bubble tags
        self.history.tag_config(
            "sent_bubble", background=BG_SENT,
            lmargin1=40, lmargin2=40, rmargin=4,
            spacing1=5, spacing3=5,
        )
        self.history.tag_config(
            "recv_bubble", background=BG_RECV,
            lmargin1=4, lmargin2=4, rmargin=40,
            spacing1=5, spacing3=5,
        )
        self.history.tag_config("sent_name",
            foreground=BG_HEADER2, font=FONT_BOLD, background=BG_SENT)
        self.history.tag_config("recv_name",
            foreground=BG_HEADER, font=FONT_BOLD, background=BG_RECV)
        self.history.tag_config("time_sent",
            foreground=COLOR_MUTED, font=FONT_MONO, background=BG_SENT)
        self.history.tag_config("time_recv",
            foreground=COLOR_MUTED, font=FONT_MONO, background=BG_RECV)
        self.history.tag_config("ok",
            foreground=COLOR_OK, background=BG_SENT)
        self.history.tag_config("tamper",
            foreground=COLOR_TAMPER, font=FONT_BOLD, background=BG_RECV)
        self.history.tag_config("system",
            foreground=COLOR_MUTED, font=FONT_ITALIC, justify="center")

        # Input area
        input_wrap = tk.Frame(main, bg=BG_INPUT, padx=8, pady=8)
        input_wrap.pack(fill="x", pady=(0, 18))

        self.recipient_label = tk.Label(
            input_wrap, text="Select a contact →", font=FONT_ITALIC,
            bg=BG_INPUT, fg=COLOR_MUTED, anchor="w")
        self.recipient_label.grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        msg_wrap = tk.Frame(input_wrap, bg=BG_INPUT)
        msg_wrap.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self.message_box = tk.Text(
            msg_wrap, font=FONT, height=2, wrap="word",
            relief="solid", bd=1, padx=7, pady=5,
            bg="#FAFAFA",
        )
        self.message_box.pack(fill="both", expand=True)
        self.message_box.bind("<Return>", self._on_enter)
        self.message_box.bind("<Shift-Return>", lambda e: None)

        tk.Button(input_wrap, text="Send\n➤", command=self.send_message,
                  bg=BG_HEADER, fg="white", font=FONT_BOLD,
                  relief="flat", cursor="hand2",
                  width=5, pady=8).grid(row=1, column=1, sticky="nsew")

        input_wrap.columnconfigure(0, weight=1)

        # Status bar
        tk.Label(self.chat_frame, textvariable=self.status_var,
                 font=("Segoe UI", 7), bg="#D0CCC8", fg=COLOR_MUTED,
                 anchor="w", pady=3).pack(fill="x")

    # ── Navigation ────────────────────────────────────────────────────────────

    def show_login(self) -> None:
        self.chat_frame.pack_forget()
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.configure(state="disabled")
        self.username_var.set("")
        self.password_var.set("")
        self.login_frame.pack(fill="both", expand=True)
        self.root.title("Secure Chat")
        self.root.after(100, self.username_entry.focus)

    def show_chat(self, username: str) -> None:
        self.login_frame.pack_forget()
        self.header_label.config(text=f"  {username}")
        self.root.title(f"SecureChat — {username}")
        self.chat_frame.pack(fill="both", expand=True)
        self._system(f"Session started as {username}")
        self.root.after(100, self.message_box.focus)
        self.root.after(1000, self._poll_messages)

    # ── History helpers ───────────────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M")

    def _system(self, text: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"\n  {text}  \n\n", "system")
        self.history.see("end")
        self.history.configure(state="disabled")

    def _append_sent(self, recipient: str, text: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"You → {recipient}\n", ("sent_bubble", "sent_name"))
        self.history.insert("end", f"{text}\n", "sent_bubble")
        self.history.insert("end", f"{self._now()}\n\n", ("sent_bubble", "time_sent"))
        self.history.see("end")
        self.history.configure(state="disabled")

    def _append_received(self, sender: str, text: str, integrity: str) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"{sender}\n", ("recv_bubble", "recv_name"))
        self.history.insert("end", f"{text}\n", "recv_bubble")
        if integrity == "verified":
            self.history.insert("end", f"{self._now()} ✓\n\n", ("recv_bubble", "time_recv"))
        elif integrity == "TAMPERED":
            self.history.insert("end", f"{self._now()} ⚠ TAMPERED\n\n", ("recv_bubble", "tamper"))
        else:
            self.history.insert("end", f"{self._now()}\n\n", ("recv_bubble", "time_recv"))
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

    def _on_enter(self, event: tk.Event) -> str:
        if not event.state & 0x1:
            self.send_message()
            return "break"
        return ""

    def _on_contact_select(self, _event: tk.Event) -> None:
        sel = self.contacts_box.curselection()
        if sel:
            name = self.contacts_box.get(sel[0])
            self.recipient_var.set(name)
            self.recipient_label.config(text=f"To: {name}", fg=BG_HEADER,
                                        font=FONT_BOLD)

    def _add_contact(self) -> None:
        name = self.new_contact_var.get().strip()
        if name and name not in self.known_recipients:
            self.known_recipients.append(name)
            self.contacts_box.insert("end", name)
        self.new_contact_var.set("")

    def send_message(self) -> None:
        recipient = self.recipient_var.get().strip()
        text = self.message_box.get("1.0", "end").strip()
        if not recipient or not text:
            return
        try:
            self.client.send_message(recipient, text)
            if recipient not in self.known_recipients:
                self.known_recipients.append(recipient)
                self.contacts_box.insert("end", recipient)
            self._append_sent(recipient, text)
            self.message_box.delete("1.0", "end")
            self.status_var.set(f"  Sent to {recipient} at {self._now()}")
        except Exception as exc:
            messagebox.showerror("Send", str(exc))

    def _poll_messages(self) -> None:
        if self.client.auth is None:
            return
        try:
            messages = self.client.fetch_messages()
            for msg in messages:
                self._append_received(msg["from"], msg["text"],
                                      msg.get("integrity", "?"))
            if messages:
                self.status_var.set(
                    f"  {len(messages)} new message(s) at {self._now()}")
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
