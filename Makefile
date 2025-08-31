PROJECT=barcode_server

docker-image:
	docker build . --file Dockerfile --tag markusressel/barcode-server:latest --no-cache

docker-latest:
	docker build . --file Dockerfile --tag markusressel/barcode-server:latest

build:
	git stash
	python setup.py sdist
	- git stash pop

test:
	poetry run pytest
