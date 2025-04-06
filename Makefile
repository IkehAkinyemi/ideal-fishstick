.PHONY: venv install test run demo clean register discover

venv:
	@echo ">>> Creating virtual environment..."
	python3 -m venv .venv
	@echo "\n>>> Activate with: source .venv/bin/activate"

install:
	@echo ">>> Installing dependencies..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

clean:
	@echo ">>> Cleaning up..."
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f *.log *.json

run: install
	@echo ">>> Starting main pipeline..."
	.venv/bin/python -m sales_nurturer.main

register:
	@echo ">>> Registering with Agentverse..."
	.venv/bin/python -m sales_nurturer.agents.agentverse

discover:
	@echo ">>> Discovering agents..."
	curl -X GET "${AGENTVERSE_API}/discover?capability=lead_nurturing"

test:
	@echo ">>> Running tests..."
	.venv/bin/python -m pytest tests/