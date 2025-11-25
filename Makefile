ENV_NAME ?= openai-agentkit
PYTHON_VERSION ?= 3.11
VENV_PATH = .venv

.PHONY: all venv-create env-setup repo-setup notebook-setup env-update clean freeze

all: venv-create env-setup repo-setup notebook-setup env-update

venv-create:
	uv venv $(VENV_PATH) --python $(PYTHON_VERSION)

env-setup: venv-create
	uv pip install --upgrade pip setuptools ipykernel

repo-setup:
	mkdir -p requirements
	echo "ipykernel" > requirements/requirements.in

notebook-setup:
	uv run ipython kernel install --user --env VIRTUAL_ENV $(PWD)/$(VENV_PATH) --name=$(ENV_NAME)

env-update:
	uv pip compile ./requirements/requirements.in -o ./requirements/requirements.txt
	uv pip sync ./requirements/requirements.txt

clean:
	rm -rf $(VENV_PATH)
	jupyter kernelspec uninstall $(ENV_NAME) -y 2>/dev/null || true

freeze:
	uv pip freeze > requirements/requirements.txt

# Helpers
install:
	uv pip install -r requirements/requirements.in

add:
	@$(eval PACKAGES := $(filter-out add,$(MAKECMDGOALS)))
	@if [ -z "$(PACKAGES)" ]; then \
		echo "Usage: make add <package_name> [package2==version ...]"; \
		echo "Examples:"; \
		echo "  make add requests"; \
		echo "  make add requests==2.28.0"; \
		echo "  make add pandas numpy"; \
		exit 1; \
	fi
	@for pkg in $(PACKAGES); do \
		echo "$$pkg" >> requirements/requirements.in; \
		echo "Added: $$pkg"; \
	done
	@$(MAKE) env-update

# Prevent make from treating package names as targets
%:
	@:

activate:
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_PATH)/bin/activate"
