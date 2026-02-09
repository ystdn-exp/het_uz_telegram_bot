DEV_COMPOSE_FILE=docker-compose.dev.yaml
PROD_COMPOSE_FILE=docker-compose.prod.yaml
POLLING_COMPOSE_FILE=docker-compose.polling.yaml

.PHONY: dev-up dev-down dev-restart prod-up prod-down prod-restart polling-up polling-down polling-restart

# Run the containers using development and production mode approach
polling-up:
	docker-compose -f $(POLLING_COMPOSE_FILE) up -d
dev-up:
	docker-compose -f $(DEV_COMPOSE_FILE) up -d

prod-up:
	docker-compose -f $(PROD_COMPOSE_FILE) up -d

# Stop the existing containers
polling-down:
	docker-compose -f $(POLLING_COMPOSE_FILE) down
dev-down:
	docker-compose -f $(DEV_COMPOSE_FILE) down
prod-down:
	docker-compose -f $(PROD_COMPOSE_FILE) down

# Restart the containers
polling-restart: polling-down polling-up

dev-restart: dev-down dev-up

prod-restart: prod-down prod-up
