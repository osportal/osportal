dependencies:requirements.txt
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@pip install --editable .

install:dependencies
	osportal install
