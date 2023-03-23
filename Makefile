.PHONY: ALWAYS

all: codepeer-agent gnat-worker

gnat_manifest.json: ALWAYS
	python3 download_from_cathod.py --manifest=$@

gnat-gitlab-runner: ALWAYS
	docker build -t $@ $@ 

codepeer-agent: gnat_manifest.json gnat-gitlab-runner ALWAYS
	docker build $$(python3 manifest_to_docker_build_args.py $<) -t $@ $@

gnat-worker: gnat_manifest.json gnat-gitlab-runner ALWAYS
	docker build $$(python3 manifest_to_docker_build_args.py $<) -t $@ $@
