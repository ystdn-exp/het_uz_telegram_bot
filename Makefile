DEV_COMPOSE_FILE=docker-compose.dev.yaml
PROD_COMPOSE_FILE=docker-compose.prod.yaml

.PHONY: dev-up dev-down dev-restart prod-up prod-down prod-restart

# Run the containers using development and production mode approach
dev-up:
	docker-compose -f $(DEV_COMPOSE_FILE) up -d

prod-up:
	docker-compose -f $(PROD_COMPOSE_FILE) up -d

# Stop the existing containers
dev-down:
	docker-compose -f $(DEV_COMPOSE_FILE) down
prod-down:
	docker-compose -f $(PROD_COMPOSE_FILE) down

# Restart the containers
dev-restart: dev-down dev-up

prod-restart: prod-down prod-up
