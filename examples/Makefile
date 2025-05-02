PYTHON ?= python3
VENV ?= venv
REQ ?= requirements.txt

.PHONY: all venv install install-dev clean activate

all: install

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r $(REQ)

install-dev: venv
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r $(REQ) && pip install -e ../..

activate:
	@echo "Aby aktywować środowisko: source $(VENV)/bin/activate"

clean:
	rm -rf $(VENV)
