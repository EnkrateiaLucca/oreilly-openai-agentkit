PYTHON ?= .venv/bin/python
UV ?= uv

.PHONY: all setup test rehearse preflight live-preflight backend app notebooks slides clean
all: setup

setup:
	$(UV) sync --frozen --extra class --extra app --extra dev

preflight:
	$(PYTHON) -m course preflight

live-preflight:
	$(PYTHON) -m course preflight --live

rehearse:
	$(PYTHON) -m course preflight
	$(PYTHON) -m course demo --runtime offline --follow-up
	$(PYTHON) -m course evaluate --runtime offline --output outputs/offline-evaluation
	$(PYTHON) -m course actions

test:
	$(PYTHON) -m pytest -q
	$(PYTHON) -m ruff check course tests scripts demos/research-report-app
	$(PYTHON) scripts/check_materials.py

backend:
	$(PYTHON) -m uvicorn course.backend:app --host 127.0.0.1 --port 8000

app:
	$(PYTHON) -m streamlit run demos/research-report-app/app.py --server.address 127.0.0.1

notebooks:
	$(PYTHON) -m jupyter lab

slides:
	$(PYTHON) scripts/build_materials.py
	npm ci --ignore-scripts
	npm run slides

clean:
	@echo 'Generated runs live in outputs/ and private runtime state in .runtime/.'
	@echo 'Before removing runtime state, run: python -m course cleanup'
