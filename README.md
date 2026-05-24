ATM System — Python Project

A fully-featured, terminal-based ATM simulation built in pure Python 3.
No external libraries required.

 Project Structure

atm_system/
├── atm.py          # Main application (screens & flows)
├── database.py     # All data operations (accounts, transactions)
├── ui.py           # Terminal UI helpers (colors, menus, receipts)
├── test_atm.py     # Automated test suite (30 tests)
└── README.md       # This file

How to Run

1. Run the ATM (Interactive)

cd atm_system
python3 atm.py


2. Run the Test Suite

cd atm_system
python3 test_atm.py


Demo Accounts (pre-loaded)

 Features

| Feature                   | Description                                      |
|---------------------------|--------------------------------------------------|
| Secure PIN Auth           | SHA-256 hashed PINs, lockout after 3 failures    |
| Balance Enquiry           | Real-time balance with formatted receipt         |
| Deposit                   | Quick amounts (100–2000) or custom               |
| Withdrawal                | Insufficient-funds guard, confirmation step      |
| Transfer                  | Account-to-account by card number                |
| Transaction History       | Last 10 transactions, colour-coded               |
| Change PIN                | Requires current PIN to proceed                  |
| New Account               | Self-service account opening                     |
| Persistent Storage        | JSON file — data survives restarts               |
| Coloured Terminal UI      | ANSI colours, receipts, formatted tables         |

---

Test Coverage (30 tests)

- Account creation & persistence
- PIN authentication & lockout
- Deposit / Withdrawal edge cases
- Transfers (success, failure, self-transfer)
- PIN change & re-login
- Transaction history ordering & limits
- PIN hashing & security
