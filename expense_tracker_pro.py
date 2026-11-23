# MY EXPENSE TRACKER - Pydroid 3 (Kivy)
# Offline app: income, expenses, auto-save, delete, PIN lock,
# daily/weekly/monthly reports, charts, and Excel export.

import os
import json
import hashlib
from datetime import datetime, date, timedelta

from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView


BG = (0.055, 0.065, 0.12, 1)
PANEL = (0.075, 0.09, 0.16, 1)
GREEN = (0.05, 0.75, 0.34, 1)
RED = (0.78, 0.07, 0.13, 1)
CYAN = (0.12, 0.82, 0.75, 1)
WHITE = (0.94, 0.96, 1, 1)
MUTED = (0.68, 0.72, 0.82, 1)


def money(value):
    return "\u20b9 {:,.2f}".format(float(value))


def make_button(text, color=CYAN, height=dp(48)):
    b = Button(
        text=text, size_hint_y=None, height=height,
        background_normal="", background_color=color,
        color=WHITE, font_size="16sp"
    )
    return b


def make_label(text, size=16, color=WHITE, height=None, bold=False):
    kwargs = dict(text=text, font_size=str(size) + "sp", color=color,
                  halign="center", valign="middle", bold=bold)
    if height is not None:
        kwargs.update(size_hint_y=None, height=height)
    label = Label(**kwargs)
    label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    return label


class BarChart(Widget):
    """Simple offline chart drawn with Kivy canvas (no browser required)."""
    def __init__(self, income=0, expense=0, **kwargs):
        super().__init__(**kwargs)
        self.income = income
        self.expense = expense
        self.bind(size=self.redraw, pos=self.redraw)
        self.redraw()

    def set_values(self, income, expense):
        self.income, self.expense = income, expense
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        w, h = self.size
        if w <= 0 or h <= 0:
            return
        maximum = max(self.income, self.expense, 1)
        with self.canvas:
            # baseline
            Color(0.35, 0.38, 0.48, 1)
            Rectangle(pos=(self.x + dp(25), self.y + dp(28)),
                      size=(max(1, w - dp(50)), dp(1)))
            bar_w = max(dp(25), (w - dp(100)) / 4)
            usable_h = max(dp(10), h - dp(65))
            income_h = usable_h * self.income / maximum
            expense_h = usable_h * self.expense / maximum
            Color(*GREEN)
            Rectangle(pos=(self.x + w * 0.27, self.y + dp(29)),
                      size=(bar_w, max(dp(2), income_h)))
            Color(*RED)
            Rectangle(pos=(self.x + w * 0.63, self.y + dp(29)),
                      size=(bar_w, max(dp(2), expense_h)))


class ExpenseTrackerApp(App):
    def build(self):
        self.title = "My Expense Tracker"
        Window.clearcolor = BG
        self.data_file = os.path.join(self.user_data_dir, "expense_data.json")
        self.data = {"transactions": [], "pin_hash": self.hash_pin("1234")}
        self.load_data()
        self.root_box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        self.show_pin_screen()
        return self.root_box

    def hash_pin(self, pin):
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.data.update(loaded)
        except Exception:
            pass
        self.data.setdefault("transactions", [])
        self.data.setdefault("pin_hash", self.hash_pin("1234"))

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            temp = self.data_file + ".tmp"
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            os.replace(temp, self.data_file)
        except Exception as e:
            self.message("Save error", str(e))

    def clear_root(self):
        self.root_box.clear_widgets()

    def message(self, title, text):
        Popup(title=title, content=make_label(text, 15),
              size_hint=(0.85, 0.35)).open()

    def show_pin_screen(self):
        self.clear_root()
        self.root_box.add_widget(Widget(size_hint_y=0.5))
        self.root_box.add_widget(make_label("MY EXPENSE TRACKER", 27, CYAN, dp(65), True))
        self.root_box.add_widget(make_label("Enter your 4-digit PIN", 18, WHITE, dp(45)))
        pin = TextInput(password=True, multiline=False, input_filter="int",
                        hint_text="PIN", font_size="24sp", size_hint_y=None,
                        height=dp(55), halign="center")
        self.root_box.add_widget(pin)
        btn = make_button("UNLOCK", GREEN)
        self.root_box.add_widget(btn)

        def unlock(*_):
            if self.hash_pin(pin.text) == self.data.get("pin_hash"):
                self.show_home()
            else:
                pin.text = ""
                self.message("Wrong PIN", "Please try again.")
        btn.bind(on_release=unlock)
        pin.bind(on_text_validate=unlock)
        self.root_box.add_widget(make_label("First-time PIN: 1234\nChange it after opening the app.",
                                            13, MUTED, dp(55)))
        self.root_box.add_widget(Widget(size_hint_y=0.6))

    def totals(self, transactions=None):
        txs = transactions if transactions is not None else self.data["transactions"]
        inc = sum(float(t["amount"]) for t in txs if t["type"] == "income")
        exp = sum(float(t["amount"]) for t in txs if t["type"] == "expense")
        return inc, exp, inc - exp

    def show_home(self):
        self.clear_root()
        self.root_box.add_widget(make_label("MY EXPENSE TRACKER", 25, CYAN, dp(48), True))
        inc, exp, balance = self.totals()
        self.root_box.add_widget(make_label("TOTAL BALANCE", 17, WHITE, dp(30)))
        self.root_box.add_widget(make_label(money(balance), 32, GREEN, dp(65), True))

        row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(10))
        income_btn = make_button("+ INCOME", GREEN)
        expense_btn = make_button("- EXPENSE", RED)
        income_btn.bind(on_release=lambda *_: self.transaction_popup("income"))
        expense_btn.bind(on_release=lambda *_: self.transaction_popup("expense"))
        row.add_widget(income_btn)
        row.add_widget(expense_btn)
        self.root_box.add_widget(row)

        header = BoxLayout(size_hint_y=None, height=dp(45))
        header.add_widget(make_label("TRANSACTION HISTORY", 17, WHITE, bold=True))
        report_btn = make_button("REPORTS", PANEL, dp(42))
        report_btn.size_hint_x = 0.42
        report_btn.bind(on_release=lambda *_: self.report_popup())
        header.add_widget(report_btn)
        self.root_box.add_widget(header)

        scroll = ScrollView()
        history = GridLayout(cols=1, spacing=dp(7), size_hint_y=None, padding=(0, dp(5)))
        history.bind(minimum_height=history.setter("height"))
        txs = sorted(self.data["transactions"], key=lambda t: t.get("timestamp", ""), reverse=True)
        if not txs:
            history.add_widget(make_label("No transactions yet.", 16, MUTED, dp(60)))
        for tx in txs:
            line = BoxLayout(size_hint_y=None, height=dp(62), spacing=dp(5))
            sign = "+" if tx["type"] == "income" else "-"
            col = GREEN if tx["type"] == "income" else RED
            info = make_label(
                "{}  |  {}\\n{}  •  {}".format(
                    sign + money(tx["amount"]), tx.get("category", "Other"),
                    tx.get("date", ""), tx.get("note", "")
                ), 13, col
            )
            line.add_widget(info)
            delete_btn = make_button("DELETE", RED, dp(42))
            delete_btn.size_hint_x = 0.27
            delete_btn.bind(on_release=lambda btn, item=tx: self.confirm_delete(item))
            line.add_widget(delete_btn)
            history.add_widget(line)
        scroll.add_widget(history)
        self.root_box.add_widget(scroll)

        bottom = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        pin_btn = make_button("CHANGE PIN", PANEL, dp(45))
        export_btn = make_button("EXPORT EXCEL", PANEL, dp(45))
        pin_btn.bind(on_release=lambda *_: self.change_pin_popup())
        export_btn.bind(on_release=lambda *_: self.export_excel())
        bottom.add_widget(pin_btn)
        bottom.add_widget(export_btn)
        self.root_box.add_widget(bottom)

    def transaction_popup(self, kind):
        title = "Add Income" if kind == "income" else "Add Expense"
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        amount = TextInput(hint_text="Amount (₹)", multiline=False, input_filter="float",
                           size_hint_y=None, height=dp(48), font_size="18sp")
        category = TextInput(hint_text="Category (e.g. Food, Salary)", multiline=False,
                             size_hint_y=None, height=dp(48))
        note = TextInput(hint_text="Note (optional)", multiline=False,
                         size_hint_y=None, height=dp(48))
        box.add_widget(amount)
        box.add_widget(category)
        box.add_widget(note)
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        save = make_button("SAVE", GREEN)
        cancel = make_button("CANCEL", RED)
        buttons.add_widget(save)
        buttons.add_widget(cancel)
        box.add_widget(buttons)
        popup = Popup(title=title, content=box, size_hint=(0.9, 0.55))
        cancel.bind(on_release=popup.dismiss)

        def add(*_):
            try:
                value = float(amount.text)
                if value <= 0:
                    raise ValueError()
            except Exception:
                self.message("Invalid amount", "Enter an amount greater than zero.")
                return
            now = datetime.now()
            self.data["transactions"].append({
                "id": now.strftime("%Y%m%d%H%M%S%f"),
                "type": kind, "amount": value,
                "category": category.text.strip() or "Other",
                "note": note.text.strip(),
                "date": now.strftime("%Y-%m-%d"),
                "timestamp": now.isoformat(timespec="seconds")
            })
            self.save_data()
            popup.dismiss()
            self.show_home()
        save.bind(on_release=add)
        popup.open()

    def confirm_delete(self, transaction):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        box.add_widget(make_label("Delete this transaction?", 16))
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        yes, no = make_button("DELETE", RED), make_button("CANCEL", PANEL)
        row.add_widget(yes)
        row.add_widget(no)
        box.add_widget(row)
        popup = Popup(title="Confirm delete", content=box, size_hint=(0.82, 0.32))
        no.bind(on_release=popup.dismiss)

        def remove(*_):
            self.data["transactions"] = [
                t for t in self.data["transactions"] if t.get("id") != transaction.get("id")
            ]
            self.save_data()
            popup.dismiss()
            self.show_home()
        yes.bind(on_release=remove)
        popup.open()

    def period_transactions(self, period):
        today = date.today()
        if period == "Daily":
            start = today
            label = today.strftime("%d %b %Y")
        elif period == "Weekly":
            start = today - timedelta(days=today.weekday())
            label = "{} to {}".format(start.strftime("%d %b"), today.strftime("%d %b %Y"))
        else:
            start = today.replace(day=1)
            label = today.strftime("%B %Y")
        selected = []
        for tx in self.data["transactions"]:
            try:
                tx_date = date.fromisoformat(tx["date"])
                if start <= tx_date <= today:
                    selected.append(tx)
            except Exception:
                continue
        return selected, label

    def report_popup(self):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        content = BoxLayout(orientation="vertical", spacing=dp(5))
        chart = BarChart(size_hint_y=None, height=dp(190))
        content.add_widget(chart)
        summary = make_label("", 15, WHITE, dp(90))
        content.add_widget(summary)
        box.add_widget(buttons)
        box.add_widget(content)
        close = make_button("CLOSE", PANEL, dp(44))
        box.add_widget(close)
        popup = Popup(title="Income & Expense Reports", content=box,
                      size_hint=(0.94, 0.72))
        close.bind(on_release=popup.dismiss)

        def show(period):
            selected, label = self.period_transactions(period)
            income, expense, balance = self.totals(selected)
            summary.text = (
                "{}\\nIncome: {}\\nExpenses: {}\\nNet: {}".format(
                    label, money(income), money(expense), money(balance)
                )
            )
            chart.set_values(income, expense)

        for period in ("Daily", "Weekly", "Monthly"):
            b = make_button(period, PANEL, dp(44))
            b.font_size = "13sp"
            buttons.add_widget(b)
            b.bind(on_release=lambda btn, p=period: show(p))
        show("Monthly")
        popup.open()

    def change_pin_popup(self):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        old_pin = TextInput(password=True, multiline=False, input_filter="int",
                            hint_text="Current PIN", size_hint_y=None, height=dp(48))
        new_pin = TextInput(password=True, multiline=False, input_filter="int",
                            hint_text="New 4-digit PIN", size_hint_y=None, height=dp(48))
        box.add_widget(old_pin)
        box.add_widget(new_pin)
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        save, cancel = make_button("SAVE PIN", GREEN), make_button("CANCEL", RED)
        row.add_widget(save)
        row.add_widget(cancel)
        box.add_widget(row)
        popup = Popup(title="Change PIN", content=box, size_hint=(0.88, 0.43))
        cancel.bind(on_release=popup.dismiss)

        def update(*_):
            if self.hash_pin(old_pin.text) != self.data.get("pin_hash"):
                self.message("Incorrect PIN", "Your current PIN is not correct.")
                return
            if len(new_pin.text) != 4:
                self.message("Invalid PIN", "Choose exactly 4 digits.")
                return
            self.data["pin_hash"] = self.hash_pin(new_pin.text)
            self.save_data()
            popup.dismiss()
            self.message("PIN changed", "Your new PIN has been saved.")
        save.bind(on_release=update)
        popup.open()

    def export_excel(self):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError:
            self.message("Excel package missing",
                         "Open Pydroid 3 Pip and install: openpyxl")
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Transactions"
            headers = ["Date", "Type", "Category", "Note", "Amount (INR)"]
            ws.append(headers)
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="167D68")
                cell.alignment = Alignment(horizontal="center")
            for tx in sorted(self.data["transactions"], key=lambda t: t.get("timestamp", "")):
                ws.append([tx.get("date", ""), tx.get("type", ""),
                           tx.get("category", ""), tx.get("note", ""),
                           float(tx.get("amount", 0))])
            for col, width in enumerate([15, 14, 22, 30, 18], start=1):
                ws.column_dimensions[get_column_letter(col)].width = width
            ws.freeze_panes = "A2"
            folder = os.path.join(os.path.expanduser("~"), "Download")
            if not os.path.isdir(folder):
                folder = self.user_data_dir
            filename = "Expense_Tracker_{}.xlsx".format(datetime.now().strftime("%Y%m%d_%H%M"))
            path = os.path.join(folder, filename)
            wb.save(path)
            self.message("Excel exported", "Saved file to:\\n" + path)
        except Exception as e:
            self.message("Export failed", str(e))


if __name__ == "__main__":
    ExpenseTrackerApp().run()
