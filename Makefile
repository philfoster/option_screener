PIP=pip3

all:
	@echo "Targets:"
	@echo "    init      - install the requirements"

init:
	${PIP} install -r requirements.txt
