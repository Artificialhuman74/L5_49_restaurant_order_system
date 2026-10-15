# Lab 5: Static Code Analysis — `restaurant_order_system.py`

**Name:** Chiranth R | **SRN:** PES1UG24AM354 | **Section:** F

Line numbers refer to the **original** file. Rows are ordered by severity (high first).

## Results: before vs after

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.00/10 (25 messages) | **10.00/10** |
| Bandit | 5 issues (2 High, 1 Medium, 2 Low) | **0 issues** |
| Flake8 | 8 warnings | **0 warnings** |

## Issue table

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| OS command injection via `os.system` | Security (Bandit B605, **High**) | 58 | `export_kitchen_orders` builds a shell command by concatenating `filename` into `"echo ... " + filename`. A filename such as `x; rm -rf ~` would run arbitrary commands. | Removed the shell call. The "Ticket sent to kitchen printer" message is now printed directly with `print()`, so no shell is involved. |
| Weak MD5 hash | Security (Bandit B324, **High**) | 47 | `hashlib.md5` is broken (collisions), so ticket hashes could be forged or collided. | Switched to `hashlib.sha256`. |
| Arbitrary code execution via `eval` | Security (Bandit B307, **Medium**; Pylint W0123) | 42 | `calculateDiscountedBill` runs `eval(promo_expr)`. Anyone who controls the promo string can execute any Python code. | Parse with `ast.parse(..., mode="eval")` and evaluate the tree with a whitelist: numbers, the name `base_bill`, and `+ - * /` only. Anything else raises `ValueError`. `"base_bill * 0.90"` still gives 40.5; `__import__('os')...` and `**` are rejected. |
| Mutable default argument | Bug (Pylint W0102) | 15 | `order_log=[]` is created once and shared by every call, so log entries leak between calls. | Default is now `None`; a fresh list is created inside the function. |
| Bare `except` + `pass` | Bug / Security (Bandit B110, Low; Flake8 E722; Pylint W0702) | 24-27 | Catches every exception (even `KeyboardInterrupt`) and silently ignores it, hiding real errors. | Replaced the try/except with `orders.pop(table_id, None)`. Voiding a missing table is still a no-op, with no exception handling needed. |
| Hardcoded secret that is also printed | Security (**not flagged by any tool**) | 71, 80 | `POS_TERMINAL_SECRET_TOKEN_2026` is committed in source and then printed to the console and logs. | Read it from the `POS_TERMINAL_KEY` environment variable and print only whether it is configured. |
| Insecure random for a PIN | Security (Bandit B311, Low) | 51 | `random.randint` is predictable and not meant for security values like a POS PIN. | Used `secrets.randbelow(9000) + 1000` (same 1000-9999 range). |
| File not closed safely, no encoding | Bug (Pylint R1732, W1514) | 55-57 | `open()` followed by a manual `close()`: if `write` fails, the file leaks. Also depends on the platform default encoding. | `with open(filename, "w", encoding="utf-8") as file:` |
| Unused import | Style (Flake8 F401; Pylint W0611) | 6 | `import math` is never used. | Removed. (`random` also dropped after switching to `secrets`.) |
| Dead / unused variables | Style (Flake8 F841; Pylint W0612) | 31, 41, 63 | `service_tax` is never used. `base_bill` is only used inside the `eval` string, so tools report it as unused. Loop variable `t` is unused. | Deleted `service_tax`. `base_bill` is now passed explicitly to the evaluator. Looped over `.values()` instead of `.items()`. |
| `== None` and redundant if/else | Style (Flake8 E711; Pylint C0121, R1703, R1705) | 32-37 | Comparison to `None` with `==`, and an if/else that just returns a boolean. | Rewrote `check_table_status` as `return order is not None and not order["is_settled"]`. |
| Lines over 79 characters | Style (Flake8 E501; Pylint C0301) | 18, 19, 75 | Long dict literal, log line and print call. | Wrapped the dict one key per line and split the print arguments. |
| Non-snake_case function names | Style (Pylint C0103) | 15, 23, 30, 40 | `placeTableOrder`, `voidTableOrder`, `checkTableStatus`, `calculateDiscountedBill` break PEP 8 naming. | Renamed to `place_table_order`, `void_table_order`, `check_table_status`, `calculate_discounted_bill`, and updated all calls. |
| Missing docstrings | Style (Pylint C0116) | 15, 23, 30, 40, 46, 50, 54, 61 | Eight functions have no docstring. | Added a one-line docstring to each function. |
| Shadowed global name | Style (Pylint W0621) | 61 | Parameter `orders` hides the module-level `orders`. | Renamed the parameter to `order_book`. |
| `%` string formatting | Style (Pylint C0209) | 19 | Old-style `%` formatting. | Switched to an f-string. |
| `main()` runs on import | Design | 83 | `main()` is called at module level, so importing the file creates `kitchen_orders.txt` and prints output. | Wrapped in `if __name__ == "__main__":`. |

## Notes

- **Tool blind spots:** Bandit did not flag the hardcoded secret (row 6), and Pylint/Flake8 reported `base_bill` as unused even though `eval` read it. Reading the code manually still matters.
- **Behaviour changes on purpose:** the ticket hash value is now SHA-256 (was MD5), the "POS Secret" line now prints `POS key configured: True/False` instead of the token, and the printer message is printed by Python instead of `echo`.
- **Verified:** ran all three tools again on the final file (scores above), and ran the program end to end: it still places T4, voids T2, prints the 40.5 discounted bill and the pending count, and writes `kitchen_orders.txt`.
