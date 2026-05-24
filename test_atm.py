"""
ATM System - Automated Test Suite
Tests all core banking operations without a human at the terminal.
"""

import os
import sys
import json
import unittest

# ── Point tests at the project folder ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

TEST_DB = "test_atm_data.json"


class ATMTestSuite(unittest.TestCase):

    # ── Setup / Teardown ──────────────────────────────────────────────────────

    def setUp(self):
        """Use a separate test database file."""
        db.DB_FILE = TEST_DB
        # Wipe DB before each test
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def make_account(self, name="Test User", pin="1234", deposit=1000.0):
        return db.create_account(name, pin, deposit)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Account Creation
    # ─────────────────────────────────────────────────────────────────────────

    def test_create_account_basic(self):
        """New account should exist with correct name and balance."""
        acc = self.make_account("Alice", "1234", 500.0)
        self.assertEqual(acc["name"], "Alice")
        self.assertEqual(acc["balance"], 500.0)
        self.assertFalse(acc["is_locked"])
        self.assertEqual(len(acc["account_number"]), 10)
        self.assertEqual(len(acc["card_number"]), 16)

    def test_create_account_zero_balance(self):
        """Account with no initial deposit should have zero balance."""
        acc = db.create_account("Zero Balance", "0000", 0.0)
        self.assertEqual(acc["balance"], 0.0)

    def test_create_account_persists(self):
        """Account should be retrievable from DB after creation."""
        acc = self.make_account()
        loaded = db.get_account(acc["account_number"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], acc["name"])

    def test_get_account_by_card(self):
        """get_account_by_card should return the right account."""
        acc = self.make_account("Bob")
        found = db.get_account_by_card(acc["card_number"])
        self.assertIsNotNone(found)
        self.assertEqual(found["account_number"], acc["account_number"])

    def test_get_nonexistent_account(self):
        """Looking up a bogus account number should return None."""
        self.assertIsNone(db.get_account("0000000000"))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. PIN Authentication
    # ─────────────────────────────────────────────────────────────────────────

    def test_correct_pin_returns_account(self):
        """Correct PIN should return the account dict."""
        acc = self.make_account(pin="5678")
        result = db.verify_pin(acc["card_number"], "5678")
        self.assertIsInstance(result, dict)
        self.assertIn("account_number", result)

    def test_wrong_pin_returns_error(self):
        """Wrong PIN should return an error dict, not an account."""
        acc = self.make_account(pin="1111")
        result = db.verify_pin(acc["card_number"], "9999")
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("error"), "wrong_pin")
        self.assertEqual(result["remaining"], 2)

    def test_account_locks_after_3_failures(self):
        """Account should lock after exactly 3 wrong PINs."""
        acc = self.make_account(pin="1234")
        card = acc["card_number"]
        db.verify_pin(card, "0000")
        db.verify_pin(card, "0000")
        db.verify_pin(card, "0000")
        result = db.verify_pin(card, "1234")  # correct PIN, but locked
        self.assertEqual(result, "LOCKED")

    def test_locked_account_string(self):
        """verify_pin on a locked account should return the string 'LOCKED'."""
        acc = self.make_account(pin="1234")
        card = acc["card_number"]
        for _ in range(3):
            db.verify_pin(card, "wrong")
        self.assertEqual(db.verify_pin(card, "1234"), "LOCKED")

    def test_unlock_account(self):
        """Admin unlock should allow login again."""
        acc = self.make_account(pin="1234")
        card = acc["card_number"]
        for _ in range(3):
            db.verify_pin(card, "wrong")
        db.unlock_account(acc["account_number"])
        result = db.verify_pin(card, "1234")
        self.assertIn("account_number", result)

    def test_bad_card_returns_none(self):
        """Unknown card number should return None."""
        result = db.verify_pin("0000000000000000", "1234")
        self.assertIsNone(result)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Deposit
    # ─────────────────────────────────────────────────────────────────────────

    def test_deposit_increases_balance(self):
        acc = self.make_account(deposit=1000.0)
        db.deposit(acc["account_number"], 500.0)
        updated = db.get_account(acc["account_number"])
        self.assertAlmostEqual(updated["balance"], 1500.0)

    def test_deposit_creates_transaction(self):
        acc = self.make_account(deposit=0.0)
        db.deposit(acc["account_number"], 200.0)
        txns = db.get_transactions(acc["account_number"])
        self.assertEqual(txns[0]["type"], "Deposit")
        self.assertAlmostEqual(txns[0]["amount"], 200.0)

    def test_multiple_deposits(self):
        acc = self.make_account(deposit=0.0)
        for _ in range(5):
            db.deposit(acc["account_number"], 100.0)
        updated = db.get_account(acc["account_number"])
        self.assertAlmostEqual(updated["balance"], 500.0)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Withdrawal
    # ─────────────────────────────────────────────────────────────────────────

    def test_withdraw_decreases_balance(self):
        acc = self.make_account(deposit=1000.0)
        result = db.withdraw(acc["account_number"], 300.0)
        self.assertTrue(result["success"])
        updated = db.get_account(acc["account_number"])
        self.assertAlmostEqual(updated["balance"], 700.0)

    def test_withdraw_insufficient_funds(self):
        acc = self.make_account(deposit=100.0)
        result = db.withdraw(acc["account_number"], 500.0)
        self.assertFalse(result["success"])
        self.assertIn("Insufficient", result["error"])

    def test_withdraw_exact_balance(self):
        """Withdrawing exactly the balance should succeed."""
        acc = self.make_account(deposit=250.0)
        result = db.withdraw(acc["account_number"], 250.0)
        self.assertTrue(result["success"])
        updated = db.get_account(acc["account_number"])
        self.assertAlmostEqual(updated["balance"], 0.0)

    def test_withdraw_zero_rejected(self):
        acc = self.make_account(deposit=500.0)
        result = db.withdraw(acc["account_number"], 0.0)
        self.assertFalse(result["success"])

    def test_withdraw_negative_rejected(self):
        acc = self.make_account(deposit=500.0)
        result = db.withdraw(acc["account_number"], -100.0)
        self.assertFalse(result["success"])

    def test_withdraw_creates_transaction(self):
        acc = self.make_account(deposit=500.0)
        db.withdraw(acc["account_number"], 150.0)
        txns = db.get_transactions(acc["account_number"])
        self.assertEqual(txns[0]["type"], "Withdrawal")
        self.assertAlmostEqual(txns[0]["amount"], 150.0)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Transfer
    # ─────────────────────────────────────────────────────────────────────────

    def test_transfer_success(self):
        sender   = self.make_account("Sender",   deposit=1000.0)
        receiver = self.make_account("Receiver", deposit=500.0)
        result = db.transfer(sender["account_number"], receiver["card_number"], 200.0)
        self.assertTrue(result["success"])

        s = db.get_account(sender["account_number"])
        r = db.get_account(receiver["account_number"])
        self.assertAlmostEqual(s["balance"], 800.0)
        self.assertAlmostEqual(r["balance"], 700.0)

    def test_transfer_insufficient_funds(self):
        sender   = self.make_account("Poor",  deposit=50.0)
        receiver = self.make_account("Rich",  deposit=500.0)
        result = db.transfer(sender["account_number"], receiver["card_number"], 100.0)
        self.assertFalse(result["success"])
        self.assertIn("Insufficient", result["error"])

    def test_transfer_to_self_rejected(self):
        acc = self.make_account(deposit=500.0)
        result = db.transfer(acc["account_number"], acc["card_number"], 100.0)
        self.assertFalse(result["success"])

    def test_transfer_unknown_recipient(self):
        sender = self.make_account(deposit=1000.0)
        result = db.transfer(sender["account_number"], "0000000000000000", 100.0)
        self.assertFalse(result["success"])

    def test_transfer_records_both_sides(self):
        sender   = self.make_account("S", deposit=1000.0)
        receiver = self.make_account("R", deposit=0.0)
        db.transfer(sender["account_number"], receiver["card_number"], 300.0)

        s_txns = db.get_transactions(sender["account_number"])
        r_txns = db.get_transactions(receiver["account_number"])
        self.assertEqual(s_txns[0]["type"], "Transfer Out")
        self.assertEqual(r_txns[0]["type"], "Transfer In")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Change PIN
    # ─────────────────────────────────────────────────────────────────────────

    def test_change_pin_success(self):
        acc = self.make_account(pin="1111")
        db.change_pin(acc["account_number"], "9999")
        # Old PIN should fail
        old_result = db.verify_pin(acc["card_number"], "1111")
        self.assertIn("error", old_result)
        # New PIN should work
        new_result = db.verify_pin(acc["card_number"], "9999")
        self.assertIn("account_number", new_result)

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Transaction History
    # ─────────────────────────────────────────────────────────────────────────

    def test_transaction_history_order(self):
        """Most recent transactions should appear first."""
        acc = self.make_account(deposit=1000.0)
        db.deposit(acc["account_number"], 100.0)
        db.deposit(acc["account_number"], 200.0)
        txns = db.get_transactions(acc["account_number"], limit=10)
        # Most recent first
        self.assertAlmostEqual(txns[0]["amount"], 200.0)
        self.assertAlmostEqual(txns[1]["amount"], 100.0)

    def test_transaction_history_limit(self):
        acc = self.make_account(deposit=0.0)
        for i in range(15):
            db.deposit(acc["account_number"], float(i + 1))
        txns = db.get_transactions(acc["account_number"], limit=5)
        self.assertEqual(len(txns), 5)

    # ─────────────────────────────────────────────────────────────────────────
    # 8. PIN Hashing
    # ─────────────────────────────────────────────────────────────────────────

    def test_pin_is_hashed(self):
        """Raw PIN should never be stored in DB."""
        acc = self.make_account(pin="1234")
        raw = json.dumps(acc)
        self.assertNotIn("1234", raw)
        self.assertIn("pin_hash", acc)

    def test_different_pins_different_hashes(self):
        self.assertNotEqual(db.hash_pin("1234"), db.hash_pin("5678"))

    def test_same_pin_same_hash(self):
        self.assertEqual(db.hash_pin("1234"), db.hash_pin("1234"))


# ─────────────────────────────────────────────────────────────────────────────

def run_tests():
    print("\n" + "═" * 60)
    print("  ATM SYSTEM — AUTOMATED TEST SUITE")
    print("═" * 60)
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(ATMTestSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("═" * 60)
    if result.wasSuccessful():
        print(f"  ✅  All {result.testsRun} tests PASSED!\n")
    else:
        print(f"  ❌  {len(result.failures)} failure(s), {len(result.errors)} error(s)\n")
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
