This repository contains a small Python package (bank_csv_normalizer) and CLI tool that converts bank/credit-card CSV exports (often messy, multi-section, and Hebrew) into a consistent canonical format that can be uploaded and imported into My Task Manager App.

Key features
	•	Automatic delimiter + encoding detection (including Hebrew exports)
	•	Header/preamble scanning to find the real table section
	•	Profile-based format detection (supports multiple bank export layouts)
	•	Normalizes:
	•	dates → YYYY-MM-DD
	•	amounts → numeric strings (no currency symbols)
	•	text/description cleanup
	•	Exports canonical UTF-8 CSV with columns:
	•	account_number, transaction_date, description, amount
	•	Produces a JSON report (rows in/out, dropped rows, warnings)


''python -m bank_csv_normalizer.cli detect path/to/input.csv''
''python -m bank_csv_normalizer.cli convert path/to/input.csv --out normalized.csv --report report.json''
