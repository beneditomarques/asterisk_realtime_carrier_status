up:
	docker-compose up -d --build

stop:
	docker-compose stop

restart:
	docker-compose restart

down:
	docker-compose down

logs:
	docker-compose logs -f

bash:
	docker-compose exec asterisk_realtime_carrier_status sh
