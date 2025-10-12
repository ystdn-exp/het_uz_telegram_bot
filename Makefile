# Run the containers using development and production mode approach
dev-up:
	docker-compose -f docker-compose.dev.yaml -t het-telegram-bot-dev up -d

prod-up:
	docker-compose -f docker-compose.prod.yamll -t het-telegram-bot-prod up -d

# Stop the existing containers
dev-down:
	docker-compose -t het-telegram-bot-dev down
prod-down:
	docker-compose -t het-telegram-bot-prod down
