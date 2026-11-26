"""Currency converter with a modern, rounded desktop interface."""

import ctypes
import json
import os
import threading
import urllib.request
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from tkinter import TclError, messagebox

import customtkinter as ctk
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


# -------------------- PALETTE --------------------

BG = "#EAF2F9"
CARD = "#FFFFFF"
CARD_SOFT = "#F4F8FC"
LINE = "#DCE8F2"

INK = "#1D3448"
INK_SOFT = "#5B7386"
MUTED = "#7B90A0"

ACCENT = "#2F6E9E"
ACCENT_HOVER = "#285F89"
ACCENT_SOFT = "#E3EFF8"
ACCENT_SOFT_HOVER = "#D3E6F4"

NAVY = "#14314B"
NAVY_LINE = "#2A4A65"
NAVY_SOFT = "#A8C2D6"
MINT = "#7CDFAF"

FONT_FAMILY = "Segoe UI"


def font(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


# -------------------- EXCHANGE RATE API --------------------

def fetch_rates(api_key):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
    request = urllib.request.Request(url, headers={"User-Agent": "CurrencyConverter/1.0"})

    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode())

    if data.get("result") != "success":
        raise RuntimeError(data.get("error-type", "API request failed"))

    return data["conversion_rates"], format_updated(data.get("time_last_update_utc", ""))


def format_updated(raw):
    try:
        stamp = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %z")
        return "Updated " + stamp.strftime("%d %b %Y · %H:%M UTC")
    except (ValueError, TypeError):
        return "Updated just now"


# -------------------- WINDOWS HELPERS --------------------

class _Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def work_area():
    rect = _Rect()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return rect


def window_frame(widget):
    hwnd = wintypes.HWND(widget.winfo_id())
    root_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)  # GA_ROOT
    rect = _Rect()
    ctypes.windll.user32.GetWindowRect(root_hwnd or hwnd, ctypes.byref(rect))
    return rect


# -------------------- APPLICATION --------------------

class CurrencyConverter(ctk.CTk):

    WINDOW_WIDTH = 460

    def __init__(self, api_key):
        super().__init__(fg_color=BG)

        self.api_key = api_key
        self.rates = {}
        self.updated_text = ""
        self.loading = False

        self.title("Currency Converter")
        self.resizable(False, False)
        self.withdraw()

        self.build_ui()
        self.size_window()
        self.deiconify()
        # CTk's mainloop re-withdraws the window to repaint the titlebar and
        # only re-shows it if the window already "exists"; without this
        # update() the startup withdraw/deiconify leaves it hidden forever.
        self.update()
        self.center_window()

        self.bind("<Return>", lambda event: self.convert(notify=True))
        self.after(80, self.refresh_rates)
        self.after(150, self.raise_window)

    # -------------------- LAYOUT --------------------

    def build_ui(self):
        page = ctk.CTkFrame(self, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=28, pady=(18, 10))

        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="Currency Converter",
            font=font(24, "bold"),
            text_color=INK,
            anchor="w",
        ).pack(side="left")

        self.refresh_button = ctk.CTkButton(
            header,
            text="↻",
            width=36,
            height=36,
            corner_radius=18,
            border_width=1,
            border_color=LINE,
            fg_color=CARD,
            hover_color=ACCENT_SOFT,
            text_color=ACCENT,
            font=font(16, "bold"),
            command=self.refresh_rates,
        )
        self.refresh_button.pack(side="right")

        ctk.CTkLabel(
            page,
            text="Live exchange rates for 160+ currencies",
            font=font(12),
            text_color=INK_SOFT,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Input card
        card = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=LINE,
        )
        card.pack(fill="x", pady=(14, 0))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=22, pady=16)

        field_label(body, "AMOUNT").pack(fill="x", pady=(0, 7))

        self.amount_entry = ctk.CTkEntry(
            body,
            height=42,
            corner_radius=11,
            border_width=1,
            border_color=LINE,
            fg_color=CARD_SOFT,
            text_color=INK,
            placeholder_text="Enter amount",
            placeholder_text_color=MUTED,
            font=font(17),
        )
        self.amount_entry.pack(fill="x")
        self.amount_entry.insert(0, "100")
        self.amount_entry.bind("<KeyRelease>", lambda event: self.convert())

        pair = ctk.CTkFrame(body, fg_color="transparent")
        pair.pack(fill="x", pady=(12, 0))
        pair.grid_columnconfigure((0, 2), weight=1, uniform="currency")

        field_label(pair, "FROM").grid(row=0, column=0, sticky="w")
        field_label(pair, "TO").grid(row=0, column=2, sticky="w")

        self.from_box = currency_box(pair, self.convert)
        self.from_box.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.from_box.set("USD")

        self.to_box = currency_box(pair, self.convert)
        self.to_box.grid(row=1, column=2, sticky="ew", pady=(8, 0))
        self.to_box.set("PKR")

        ctk.CTkButton(
            pair,
            text="⇅",
            width=40,
            height=40,
            corner_radius=20,
            fg_color=ACCENT_SOFT,
            hover_color=ACCENT_SOFT_HOVER,
            text_color=ACCENT,
            font=font(15, "bold"),
            command=self.swap_currencies,
        ).grid(row=1, column=1, padx=10, pady=(8, 0))

        ctk.CTkButton(
            body,
            text="Convert currency",
            height=46,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=font(14, "bold"),
            command=lambda: self.convert(notify=True),
        ).pack(fill="x", pady=(14, 0))

        # Result panel
        result = ctk.CTkFrame(page, fg_color=NAVY, corner_radius=18)
        result.pack(fill="x", pady=(10, 0))

        result_body = ctk.CTkFrame(result, fg_color="transparent")
        result_body.pack(fill="x", padx=22, pady=14)

        ctk.CTkLabel(
            result_body,
            text="CONVERTED AMOUNT",
            font=font(10, "bold"),
            text_color=NAVY_SOFT,
            anchor="w",
        ).pack(fill="x")

        self.result_label = ctk.CTkLabel(
            result_body,
            text="—",
            font=font(28, "bold"),
            text_color=NAVY_SOFT,
            anchor="w",
        )
        self.result_label.pack(fill="x", pady=(2, 0))

        self.rate_label = ctk.CTkLabel(
            result_body,
            text="Enter an amount to see the live rate",
            font=font(12),
            text_color=NAVY_SOFT,
            anchor="w",
        )
        self.rate_label.pack(fill="x", pady=(2, 0))

        ctk.CTkFrame(result_body, fg_color=NAVY_LINE, height=1, corner_radius=0).pack(
            fill="x", pady=(9, 0)
        )

        self.status_label = ctk.CTkLabel(
            result_body,
            text="Fetching latest rates…",
            font=font(10),
            text_color=NAVY_SOFT,
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(7, 0))

        ctk.CTkLabel(
            page,
            text="Exchange rates by ExchangeRate-API  ·  Press Enter to convert",
            font=font(10),
            text_color=MUTED,
        ).pack(pady=(12, 0))

    # -------------------- WINDOW PLACEMENT --------------------

    def size_window(self):
        self.update_idletasks()
        scale = ctk.ScalingTracker.get_window_scaling(self)
        height = round(self.winfo_reqheight() / scale)
        self.geometry(f"{self.WINDOW_WIDTH}x{height}")

    def center_window(self):
        self.update_idletasks()
        frame = window_frame(self)
        width = frame.right - frame.left
        height = frame.bottom - frame.top

        work = work_area()
        x = work.left + (work.right - work.left - width) // 2
        y = work.top + (work.bottom - work.top - height) // 2

        self.geometry(f"+{max(x, work.left)}+{max(y, work.top)}")

    def raise_window(self):
        # Launched from a terminal or IDE, the new window can open behind it;
        # a short topmost flash surfaces it even while the launcher holds the
        # foreground.
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(350, lambda: self.attributes("-topmost", False))

    # -------------------- DATA --------------------

    def refresh_rates(self):
        if self.loading:
            return

        self.loading = True
        self.refresh_button.configure(state="disabled", text="…")
        self.status_label.configure(text="Fetching latest rates…")

        threading.Thread(target=self.fetch_worker, daemon=True).start()

    def fetch_worker(self):
        try:
            rates, updated = fetch_rates(self.api_key)
            error = None
        except Exception as exc:
            rates, updated, error = None, "", exc

        try:
            self.after(0, lambda: self.apply_rates(rates, updated, error))
        except (RuntimeError, TclError):
            pass

    def apply_rates(self, rates, updated, error):
        if not self.winfo_exists():
            return

        self.loading = False
        self.refresh_button.configure(state="normal", text="↻")

        if error is not None:
            self.status_label.configure(text=self.updated_text or "Rates unavailable")
            if not self.rates:
                messagebox.showerror(
                    "Connection error",
                    f"Unable to load exchange rates.\n\n{error}",
                    parent=self,
                )
                self.destroy()
            else:
                messagebox.showerror(
                    "Refresh failed",
                    f"Could not refresh exchange rates.\n\n{error}",
                    parent=self,
                )
            return

        first_load = not self.rates
        self.rates = rates
        self.updated_text = updated
        self.status_label.configure(text=updated)

        codes = sorted(rates)
        self.from_box.configure(values=codes)
        self.to_box.configure(values=codes)

        if first_load:
            self.from_box.set("USD" if "USD" in rates else codes[0])
            self.to_box.set("PKR" if "PKR" in rates else codes[min(1, len(codes) - 1)])

        self.convert()

    # -------------------- CONVERSION --------------------

    def convert(self, notify=False):
        base = self.from_box.get()
        target = self.to_box.get()

        if not self.rates or not base or not target:
            if notify:
                messagebox.showinfo(
                    "Please wait",
                    "Exchange rates are still loading.",
                    parent=self,
                )
            return

        try:
            amount = float(self.amount_entry.get().strip().replace(",", ""))
        except ValueError:
            self.show_placeholder("Enter a valid amount to convert")
            if notify:
                messagebox.showerror(
                    "Invalid input",
                    "Please enter a valid numerical amount.\n\nExample: 250 or 1,250.50",
                    parent=self,
                )
            return

        if amount <= 0:
            self.show_placeholder("Amount must be greater than zero")
            if notify:
                messagebox.showwarning(
                    "Invalid amount",
                    "Please enter an amount greater than zero.",
                    parent=self,
                )
            return

        rate = self.rates[target] / self.rates[base]
        converted = amount * rate

        self.result_label.configure(text=f"{converted:,.2f} {target}", text_color=MINT)
        self.rate_label.configure(text=f"1 {base} = {rate:,.4f} {target}")

    def show_placeholder(self, message):
        self.result_label.configure(text="—", text_color=NAVY_SOFT)
        self.rate_label.configure(text=message)

    def swap_currencies(self):
        source, target = self.from_box.get(), self.to_box.get()
        self.from_box.set(target)
        self.to_box.set(source)
        self.convert()


# -------------------- WIDGET HELPERS --------------------

def field_label(master, text):
    return ctk.CTkLabel(
        master,
        text=text,
        font=font(11, "bold"),
        text_color=INK_SOFT,
        anchor="w",
    )


def currency_box(master, on_change):
    combo = ctk.CTkComboBox(
        master,
        values=["USD"],
        state="readonly",
        height=42,
        corner_radius=11,
        border_width=1,
        border_color=LINE,
        fg_color=CARD_SOFT,
        button_color=ACCENT_SOFT,
        button_hover_color=ACCENT_SOFT_HOVER,
        dropdown_fg_color=CARD,
        dropdown_hover_color=ACCENT_SOFT,
        dropdown_text_color=INK,
        text_color=INK,
        font=font(13, "bold"),
        dropdown_font=font(12),
        command=on_change,
    )

    # CustomTkinter has no public API for opening the dropdown, and its
    # built-in arrow is a thick canvas shape that renders poorly, so a
    # clean chevron sits on top and forwards clicks to the dropdown.
    chevron = ctk.CTkLabel(
        combo,
        text="▾",
        width=26,
        height=26,
        corner_radius=0,
        fg_color=ACCENT_SOFT,
        text_color=ACCENT,
        font=font(12, "bold"),
        cursor="hand2",
    )
    chevron.place(relx=1.0, rely=0.5, x=-8, anchor="e")
    chevron.bind("<Button-1>", lambda event: combo._open_dropdown_menu())
    chevron.bind("<Enter>", lambda event: chevron.configure(fg_color=ACCENT_SOFT_HOVER))
    chevron.bind("<Leave>", lambda event: chevron.configure(fg_color=ACCENT_SOFT))

    return combo


# -------------------- START --------------------

def main():
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    if not api_key:
        raise ValueError("API key not found. Please check your .env file.")

    CurrencyConverter(api_key).mainloop()


if __name__ == "__main__":
    main()
