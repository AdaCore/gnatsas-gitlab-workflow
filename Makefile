.PHONY: ALWAYS

all: codepeer-agent gnat-worker

codepeer-agent: images/codepeer-agent images ALWAYS
	docker build $< -t $@

gnat-worker: images/gnat-worker images ALWAYS
	docker build $< -t $@

images: manifest.json ALWAYS
	python3 build.py --manifest=$<
