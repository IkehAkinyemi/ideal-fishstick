.PHONY: venv install test run demo clean

venv:
	@echo ">>> Creating virtual environment..."
	python3 -m venv .venv
	@echo "\n>>> Activate with: source .venv/bin/activate"

install:
	@echo ">>> Installing dependencies..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

test:
	@echo ">>> Running tests..."
	.venv/bin/python -m pytest tests/ -v

run:
	@echo ">>> Starting sales nurturer..."
	.venv/bin/python src/main.py parse --source data/leads_sample.csv --type csv
	.venv/bin/python src/main.py nurture --leads parsed_leads.json --templates data/templates/

demo: install
	@echo ">>> Running full demo..."
	.venv/bin/python src/main.py register --name "SalesNurturer"
	.venv/bin/python src/main.py discover
	make run

clean:
	@echo ">>> Cleaning up..."
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f *.log *.json