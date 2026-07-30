.PHONY: up down test logs

# Start the enterprise gateway in detached mode
up:
	docker-compose up -d

# Spin down the infrastructure
down:
	docker-compose down

# Run Zero-Trust PII unit tests locally
test:
	cd api && pytest test_main.py -v

# View logs for the FastAPI security layer
logs:
	docker logs -f clinical_pii_gateway
