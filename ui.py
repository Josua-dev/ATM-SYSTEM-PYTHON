"""
ATM System - UI Module
Handles all terminal display, formatting, and user input.
"""

import os
import time


# ─── ANSI Colours ─────────────────────────────────────────────────────────────

class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def fmt(text: str, *codes) -> str:
    return "".join(codes) + text + Color.RESET


def header(title: str = "") -> None:
    """Print the ATM header banner."""
    clear()
    width = 52
    print(fmt("═" * width, Color.CYAN, Color.BOLD))
    print(fmt("  ██╗  ██╗ █████╗ ████████╗ ██████╗ ██╗   ██╗", Color.CYAN, Color.BOLD))
    print(fmt("  ██║ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗╚██╗ ██╔╝", Color.CYAN, Color.BOLD))
    print(fmt("  █████╔╝ ███████║   ██║   ██║   ██║ ╚████╔╝ ", Color.CYAN, Color.BOLD))
    print(fmt("  ██╔═██╗ ██╔══██║   ██║   ██║   ██║  ╚██╔╝  ", Color.CYAN, Color.BOLD))
    print(fmt("  ██║  ██╗██║  ██║   ██║   ╚██████╔╝   ██║   ", Color.CYAN, Color.BOLD))
    print(fmt("  ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝    ╚═╝   ", Color.CYAN, Color.BOLD))
    print(fmt("         A T M   S y s t e m   v1.0           ", Color.DIM))
    print(fmt("═" * width, Color.CYAN, Color.BOLD))
    if title:
        print(fmt(f"  {title.center(width - 4)}", Color.YELLOW, Color.BOLD))
        print(fmt("─" * width, Color.DIM))
    print()


def divider(width: int = 52) -> None:
    print(fmt("─" * width, Color.DIM))


def success(msg: str) -> None:
    print(fmt(f"  ✅  {msg}", Color.GREEN, Color.BOLD))


def error(msg: str) -> None:
    print(fmt(f"  ❌  {msg}", Color.RED, Color.BOLD))


def warning(msg: str) -> None:
    print(fmt(f"  ⚠️   {msg}", Color.YELLOW, Color.BOLD))


def info(msg: str) -> None:
    print(fmt(f"  ℹ️   {msg}", Color.CYAN))


def pause(seconds: float = 1.5) -> None:
    time.sleep(seconds)


def press_enter() -> None:
    input(fmt("\n  Press ENTER to continue...", Color.DIM))


def format_currency(amount: float) -> str:
    return fmt(f"N$ {amount:,.2f}", Color.GREEN, Color.BOLD)


def menu(title: str, options: list, back_label: str = "Back") -> str:
    """Display a numbered menu and return the user's choice."""
    print(fmt(f"  {title}", Color.BOLD))
    divider()
    for i, opt in enumerate(options, 1):
        icon = opt.get("icon", "•")
        label = opt.get("label", "")
        print(fmt(f"  [{i}]", Color.YELLOW, Color.BOLD) + f" {icon}  {label}")
    print(fmt(f"  [0]", Color.RED) + f" ✖  {back_label}")
    divider()
    return input(fmt("  ➤  Your choice: ", Color.CYAN)).strip()


def get_input(prompt: str, secret: bool = False) -> str:
    """Get input from user, optionally masking it."""
    if secret:
        import getpass
        return getpass.getpass(fmt(f"  ➤  {prompt}: ", Color.CYAN))
    return input(fmt(f"  ➤  {prompt}: ", Color.CYAN)).strip()


def get_amount(prompt: str) -> float:
    """Prompt the user for a valid monetary amount."""
    while True:
        raw = get_input(prompt)
        try:
            amount = float(raw)
            if amount <= 0:
                error("Amount must be greater than zero.")
            else:
                return round(amount, 2)
        except ValueError:
            error("Please enter a valid number (e.g. 500 or 1250.50).")


def print_receipt(title: str, rows: list) -> None:
    """Print a formatted receipt-style block."""
    width = 52
    print()
    print(fmt("┌" + "─" * (width - 2) + "┐", Color.CYAN))
    print(fmt("│" + title.center(width - 2) + "│", Color.CYAN, Color.BOLD))
    print(fmt("├" + "─" * (width - 2) + "┤", Color.CYAN))
    for label, value, color in rows:
        line = f"  {label:<22}{value}"
        padded = line.ljust(width - 2)
        print(fmt("│", Color.CYAN) + fmt(padded[:22], Color.DIM) + fmt(padded[22:].rstrip().ljust(width - 24), color) + fmt("  │", Color.CYAN))
    print(fmt("└" + "─" * (width - 2) + "┘", Color.CYAN))
    print()


def transaction_table(transactions: list) -> None:
    """Print a table of recent transactions."""
    if not transactions:
        info("No transactions found.")
        return

    col_w = [20, 12, 12]
    head = f"  {'Date & Time':<{col_w[0]}}{'Type':<{col_w[1]}}{'Amount':>{col_w[2]}}"
    print(fmt(head, Color.BOLD))
    print(fmt("  " + "─" * (sum(col_w) + 2), Color.DIM))

    for txn in transactions:
        ttype = txn["type"]
        amount = txn["amount"]
        ts = txn["timestamp"][:16]

        color = Color.GREEN if "Deposit" in ttype or "In" in ttype else Color.RED
        sign  = "+" if "Deposit" in ttype or "In" in ttype else "-"

        row = f"  {ts:<{col_w[0]}}{ttype:<{col_w[1]}}"
        print(fmt(row, Color.DIM) + fmt(f"{sign}N${amount:,.2f}".rjust(col_w[2]), color))

    print(fmt("  " + "─" * (sum(col_w) + 2), Color.DIM))
    print()
