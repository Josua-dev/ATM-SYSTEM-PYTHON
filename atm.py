"""
Namibia EXPRESS ATM System - Main Application
Orchestrates all ATM screens, sessions, and user flows.
"""

import sys
from datetime import datetime
import database as db
import ui


# ─── Session ──────────────────────────────────────────────────────────────────

class Session:
    def __init__(self):
        self.account = None
        self.card_number = None

    def login(self, account: dict, card_number: str):
        self.account = account
        self.card_number = card_number

    def logout(self):
        self.account = None
        self.card_number = None

    def refresh(self):
        """Reload account from DB (after balance changes)."""
        if self.account:
            self.account = db.get_account(self.account["account_number"])

    @property
    def acc_num(self) -> str:
        return self.account["account_number"]

    @property
    def name(self) -> str:
        return self.account["name"]

    @property
    def balance(self) -> float:
        return self.account["balance"]


session = Session()


# ─── Welcome Screen ───────────────────────────────────────────────────────────

def screen_welcome():
    while True:
        ui.header("Welcome — Please Choose an Option")
        choice = ui.menu("Main Menu", [
            {"icon": "💳", "label": "Insert Card (Login)"},
            {"icon": "🆕", "label": "Open a New Account"},
            {"icon": "ℹ️ ", "label": "About this ATM"},
        ], back_label="Exit ATM")

        if choice == "1":
            screen_card_entry()
        elif choice == "2":
            screen_create_account()
        elif choice == "3":
            screen_about()
        elif choice == "0":
            ui.clear()
            print(ui.fmt("\n  Thank you for banking with Namibia EXPRESS! Goodbye! 👋\n", ui.Color.CYAN, ui.Color.BOLD))
            sys.exit(0)
        else:
            ui.error("Invalid option. Please try again.")
            ui.pause()


# ─── Card Entry & PIN ─────────────────────────────────────────────────────────

def screen_card_entry():
    ui.header("Insert Card")
    print(ui.fmt("  Demo Cards (copy & paste):", ui.Color.DIM))
    print(ui.fmt("  ┌───────────────────────────────────────────────────┐", ui.Color.DIM))
    print(ui.fmt("  │  1234567890123456  PIN: 1234  Josua Uuyuni        │", ui.Color.DIM))
    print(ui.fmt("  │  9876543210987654  PIN: 5678  Lydia Uuyuni        │", ui.Color.DIM))
    print(ui.fmt("  │  1111222233334444  PIN: 9999  Eva Uuyuni          │", ui.Color.DIM))
    print(ui.fmt("  │  5555666677778888  PIN: 4321  Pendu Uuyuni        │", ui.Color.DIM))
    print(ui.fmt("  │  9999000011112222  PIN: 7777  Betuel Uuyuni       │", ui.Color.DIM))
    print(ui.fmt("  └───────────────────────────────────────────────────┘", ui.Color.DIM))
    print()

    card_number = ui.get_input("Enter Card Number (or 0 to cancel)").replace(" ", "")
    if card_number == "0":
        return

    if len(card_number) < 8:
        ui.error("Invalid card number format.")
        ui.pause()
        return

    # PIN attempt loop
    for attempt in range(3):
        ui.header("PIN Entry")
        pin = ui.get_input("Enter your 4-digit PIN", secret=True)

        result = db.verify_pin(card_number, pin)

        if result == "LOCKED":
            ui.header("Account Locked")
            ui.error("This account has been LOCKED due to too many failed PIN attempts.")
            ui.info("Please visit a branch to unlock your account.")
            ui.press_enter()
            return

        if isinstance(result, dict) and "error" in result:
            remaining = result["remaining"]
            if remaining > 0:
                ui.error(f"Incorrect PIN. {remaining} attempt(s) remaining.")
                ui.pause()
            else:
                ui.header("Account Locked")
                ui.error("Account LOCKED — 3 failed PIN attempts.")
                ui.info("Please visit a branch to unlock your account.")
                ui.press_enter()
                return
        elif isinstance(result, dict) and "account_number" in result:
            session.login(result, card_number)
            ui.success(f"Welcome back, {session.name}!")
            ui.pause(1.0)
            screen_main_menu()
            return

    ui.error("Maximum PIN attempts reached.")
    ui.press_enter()


# ─── Main Authenticated Menu ──────────────────────────────────────────────────

def screen_main_menu():
    while session.account:
        session.refresh()
        ui.header(f"Welcome, {session.name}")
        print(ui.fmt(f"  Current Balance: ", ui.Color.DIM) +
              ui.format_currency(session.balance))
        print()

        choice = ui.menu("What would you like to do?", [
            {"icon": "💰", "label": "Check Balance"},
            {"icon": "📥", "label": "Deposit Cash"},
            {"icon": "📤", "label": "Withdraw Cash"},
            {"icon": "🔄", "label": "Transfer Funds"},
            {"icon": "📋", "label": "Transaction History"},
            {"icon": "🔑", "label": "Change PIN"},
        ], back_label="Logout")

        if choice == "1":
            screen_balance()
        elif choice == "2":
            screen_deposit()
        elif choice == "3":
            screen_withdraw()
        elif choice == "4":
            screen_transfer()
        elif choice == "5":
            screen_history()
        elif choice == "6":
            screen_change_pin()
        elif choice == "0":
            session.logout()
            ui.success("You have been logged out safely.")
            ui.pause()
            return
        else:
            ui.error("Invalid option. Please try again.")
            ui.pause()


# ─── Balance ─────────────────────────────────────────────────────────────────

def screen_balance():
    session.refresh()
    ui.header("Account Balance")
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    ui.print_receipt("  BALANCE ENQUIRY  ", [
        ("Account Holder",  session.name,               ui.Color.WHITE),
        ("Account Number",  session.acc_num,             ui.Color.CYAN),
        ("Card Number",     f"****{session.card_number[-4:]}", ui.Color.DIM),
        ("Available Balance", f"N$ {session.balance:,.2f}", ui.Color.GREEN),
        ("Date & Time",     now,                         ui.Color.DIM),
    ])
    ui.press_enter()


# ─── Deposit ─────────────────────────────────────────────────────────────────

def screen_deposit():
    ui.header("Deposit Cash")
    print(ui.fmt(f"  Current Balance: {ui.format_currency(session.balance)}\n", ui.Color.DIM))

    print(ui.fmt("  Quick amounts:", ui.Color.DIM))
    print("  [1] N$  100    [2] N$  200    [3] N$  500")
    print("  [4] N$ 1000    [5] N$ 2000    [6] Custom amount")
    print(ui.fmt("  [0] Cancel\n", ui.Color.DIM))

    quick = {"1": 100, "2": 200, "3": 500, "4": 1000, "5": 2000}
    choice = ui.get_input("Select option")

    if choice == "0":
        return
    elif choice in quick:
        amount = float(quick[choice])
    elif choice == "6":
        amount = ui.get_amount("Enter amount to deposit (N$)")
    else:
        ui.error("Invalid choice.")
        ui.pause()
        return

    result = db.deposit(session.acc_num, amount)
    session.refresh()

    ui.header("Deposit Successful")
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    ui.print_receipt("  DEPOSIT RECEIPT  ", [
        ("Account Holder",    session.name,             ui.Color.WHITE),
        ("Amount Deposited",  f"N$ {amount:,.2f}",     ui.Color.GREEN),
        ("New Balance",       f"N$ {session.balance:,.2f}", ui.Color.GREEN),
        ("Date & Time",       now,                      ui.Color.DIM),
        ("Ref ID",            result["transaction"]["id"][:12] + "...", ui.Color.DIM),
    ])
    ui.success("Deposit completed successfully!")
    ui.press_enter()


# ─── Withdraw ─────────────────────────────────────────────────────────────────

def screen_withdraw():
    ui.header("Withdraw Cash")
    session.refresh()
    print(ui.fmt(f"  Current Balance: {ui.format_currency(session.balance)}\n", ui.Color.DIM))

    print(ui.fmt("  Quick amounts:", ui.Color.DIM))
    print("  [1] N$  100    [2] N$  200    [3] N$  500")
    print("  [4] N$ 1000    [5] N$ 2000    [6] Custom amount")
    print(ui.fmt("  [0] Cancel\n", ui.Color.DIM))

    quick = {"1": 100, "2": 200, "3": 500, "4": 1000, "5": 2000}
    choice = ui.get_input("Select option")

    if choice == "0":
        return
    elif choice in quick:
        amount = float(quick[choice])
    elif choice == "6":
        amount = ui.get_amount("Enter amount to withdraw (N$)")
    else:
        ui.error("Invalid choice.")
        ui.pause()
        return

    if amount > session.balance:
        ui.header("Withdrawal Failed")
        ui.error(f"Insufficient funds. Available: N$ {session.balance:,.2f}")
        ui.press_enter()
        return

    # Confirm
    print()
    ui.warning(f"You are about to withdraw {ui.format_currency(amount)}")
    confirm = ui.get_input("Confirm? (yes / no)").lower()
    if confirm not in ("yes", "y"):
        ui.info("Withdrawal cancelled.")
        ui.pause()
        return

    result = db.withdraw(session.acc_num, amount)
    session.refresh()

    if not result["success"]:
        ui.error(result["error"])
        ui.press_enter()
        return

    ui.header("Withdrawal Successful")
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    ui.print_receipt("  WITHDRAWAL RECEIPT  ", [
        ("Account Holder",   session.name,             ui.Color.WHITE),
        ("Amount Withdrawn", f"N$ {amount:,.2f}",     ui.Color.RED),
        ("Remaining Balance",f"N$ {session.balance:,.2f}", ui.Color.GREEN),
        ("Date & Time",      now,                      ui.Color.DIM),
        ("Ref ID",           result["transaction"]["id"][:12] + "...", ui.Color.DIM),
    ])
    ui.success(f"Please collect your N$ {amount:,.2f} cash.")
    ui.press_enter()


# ─── Transfer ─────────────────────────────────────────────────────────────────

def screen_transfer():
    ui.header("Transfer Funds")
    session.refresh()
    print(ui.fmt(f"  Your Balance: {ui.format_currency(session.balance)}\n", ui.Color.DIM))

    recipient_card = ui.get_input("Enter recipient's Card Number (or 0 to cancel)").replace(" ", "")
    if recipient_card == "0":
        return

    recipient = db.get_account_by_card(recipient_card)
    if not recipient:
        ui.error("Card number not found in this system.")
        ui.press_enter()
        return
    if recipient["account_number"] == session.acc_num:
        ui.error("You cannot transfer to your own account.")
        ui.press_enter()
        return

    print()
    ui.info(f"Recipient: {ui.fmt(recipient['name'], ui.Color.WHITE, ui.Color.BOLD)}")
    print()
    amount = ui.get_amount(f"Enter amount to transfer (N$)")

    if amount > session.balance:
        ui.error(f"Insufficient funds. Available: N$ {session.balance:,.2f}")
        ui.press_enter()
        return

    print()
    ui.warning(f"Transfer {ui.format_currency(amount)} → {recipient['name']}")
    confirm = ui.get_input("Confirm? (yes / no)").lower()
    if confirm not in ("yes", "y"):
        ui.info("Transfer cancelled.")
        ui.pause()
        return

    result = db.transfer(session.acc_num, recipient_card, amount)
    session.refresh()

    if not result["success"]:
        ui.error(result["error"])
        ui.press_enter()
        return

    ui.header("Transfer Successful")
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    ui.print_receipt("  TRANSFER RECEIPT  ", [
        ("From",            session.name,              ui.Color.WHITE),
        ("To",              result["recipient_name"],  ui.Color.WHITE),
        ("Amount",          f"N$ {amount:,.2f}",      ui.Color.RED),
        ("Your Balance",    f"N$ {session.balance:,.2f}", ui.Color.GREEN),
        ("Date & Time",     now,                       ui.Color.DIM),
    ])
    ui.success("Transfer completed successfully!")
    ui.press_enter()


# ─── Transaction History ──────────────────────────────────────────────────────

def screen_history():
    ui.header("Transaction History")
    transactions = db.get_transactions(session.acc_num, limit=10)
    print(ui.fmt(f"  Last {min(len(transactions), 10)} transactions for {session.name}\n", ui.Color.DIM))
    ui.transaction_table(transactions)
    ui.press_enter()


# ─── Change PIN ───────────────────────────────────────────────────────────────

def screen_change_pin():
    ui.header("Change PIN")

    current_pin = ui.get_input("Enter your current PIN", secret=True)
    result = db.verify_pin(session.card_number, current_pin)

    if not isinstance(result, dict) or "account_number" not in result:
        ui.error("Incorrect current PIN. PIN change aborted.")
        ui.press_enter()
        return

    new_pin = ui.get_input("Enter your new 4-digit PIN", secret=True)
    if not new_pin.isdigit() or len(new_pin) != 4:
        ui.error("PIN must be exactly 4 digits (numbers only).")
        ui.press_enter()
        return

    confirm_pin = ui.get_input("Confirm your new PIN", secret=True)
    if new_pin != confirm_pin:
        ui.error("PINs do not match. PIN change aborted.")
        ui.press_enter()
        return

    db.change_pin(session.acc_num, new_pin)
    ui.success("Your PIN has been changed successfully!")
    ui.press_enter()


# ─── Create Account ───────────────────────────────────────────────────────────

def screen_create_account():
    ui.header("Open a New Account")

    name = ui.get_input("Full Name")
    if not name or len(name) < 2:
        ui.error("Name must be at least 2 characters.")
        ui.pause()
        return

    while True:
        pin = ui.get_input("Choose a 4-digit PIN", secret=True)
        if pin.isdigit() and len(pin) == 4:
            break
        ui.error("PIN must be exactly 4 digits.")

    confirm = ui.get_input("Confirm your PIN", secret=True)
    if pin != confirm:
        ui.error("PINs do not match. Please try again.")
        ui.pause()
        return

    deposit_choice = ui.get_input("Make an initial deposit? (yes / no)").lower()
    initial = 0.0
    if deposit_choice in ("yes", "y"):
        initial = ui.get_amount("Initial deposit amount (N$)")

    account = db.create_account(name, pin, initial)

    ui.header("Account Created! 🎉")
    ui.print_receipt("  YOUR NEW ACCOUNT  ", [
        ("Account Holder",  account["name"],            ui.Color.WHITE),
        ("Account Number",  account["account_number"],  ui.Color.CYAN),
        ("Card Number",     account["card_number"],     ui.Color.YELLOW),
        ("Opening Balance", f"N$ {account['balance']:,.2f}", ui.Color.GREEN),
        ("Status",          "ACTIVE",                   ui.Color.GREEN),
    ])
    ui.warning("IMPORTANT: Write down your card number — you need it to login!")
    ui.press_enter()


# ─── About ───────────────────────────────────────────────────────────────────

def screen_about():
    ui.header("About Namibia EXPRESS ATM")
    print(ui.fmt("  Namibia EXPRESS ATM System  v1.0", ui.Color.BOLD))
    print(ui.fmt("  Your trusted banking partner across Namibia\n", ui.Color.DIM))
    print(ui.fmt("  Built with Python 3 — No external dependencies\n", ui.Color.DIM))
    print(ui.fmt("  Features:", ui.Color.YELLOW))
    features = [
        "Secure PIN authentication with automatic lockout",
        "Deposit & Withdrawal with quick-select amounts",
        "Account-to-account fund transfers",
        "Full transaction history (last 10 transactions)",
        "Self-service PIN change",
        "New account registration at the machine",
        "Persistent storage — data saved between sessions",
    ]
    for f in features:
        print(ui.fmt(f"    ✓  {f}", ui.Color.DIM))
    print()
    print(ui.fmt("  📞 Namibia EXPRESS Helpline: 0800-EXPRESS", ui.Color.CYAN))
    print(ui.fmt("  🌐 www.namibiaexpress.com.na\n", ui.Color.CYAN))
    ui.press_enter()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    print(ui.fmt("\n  Starting Namibia EXPRESS ATM System...", ui.Color.DIM))
    db.seed_demo_accounts()
    ui.pause(0.5)
    screen_welcome()


if __name__ == "__main__":
    main()
