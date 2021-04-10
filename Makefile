
.PHONY: build run test generate-requirements

build:
	- docker build --tag=dainst/glk21:dev $(CURDIR)

run:
	- docker run -it --rm \
		-p 8888:8888 \
		--name glk21 \
		--volume $(CURDIR):/app \
		dainst/glk21:dev

test:mos
	- docker run -t --rm \
		--volume $(CURDIR):/app \
		dainst/glk21:dev \
		python -m unittest test/*.py

generate-requirements:
	- docker run -t --rm \
		--volume $(CURDIR):/app \
		dainst/glk21:dev \
		pip-compile requirements.in
