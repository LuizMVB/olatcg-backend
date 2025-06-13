build:
	docker compose build

up:
	docker compose up

bash:
	docker compose exec app bash

migration:
	docker-compose run --rm app sh -c "python manage.py makemigrations"
	