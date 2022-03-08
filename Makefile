PROJECT=barcode_server

current-version:
	set -ex
	@echo "Current version is `cat ${PROJECT}/__init__.py | grep '__version__' | cut -d ' ' -f3 | sed s/\\\"//g`"

build:
	git stash
	python setup.py sdist
	- git stash pop

test:
	pipenv run pytest

git-release:
	set -ex
	git add ${PROJECT}/__init__.py
	git commit -m "Bumped version to `cat ${PROJECT}/__init__.py | grep '__version__' | cut -d ' ' -f3 | sed s/\\\"//g`"
	git tag v`cat ${PROJECT}/__init__.py | grep '__version__' | cut -d ' ' -f3 | sed s/\"//g`
	git push
	git push --tags

_release-patch:
	@echo "__version__ = \"`cat ${PROJECT}/__init__.py | awk -F '("|")' '{ print($$2)}' | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g'`\"" > ${PROJECT}/__init__.py
release-patch: test _release-patch git-release current-version

_release-minor:
	@echo "__version__ = \"`cat ${PROJECT}/__init__.py | awk -F '("|")' '{ print($$2)}' | awk -F. '{$$(NF-1) = $$(NF-1) + 1;} 1' | sed 's/ /./g' | awk -F. '{$$(NF) = 0;} 1' | sed 's/ /./g' `\"" > ${PROJECT}/__init__.py
release-minor: test _release-minor git-release current-version

_release-major:
	@echo "__version__ = \"`cat ${PROJECT}/__init__.py | awk -F '("|")' '{ print($$2)}' | awk -F. '{$$(NF-2) = $$(NF-2) + 1;} 1' | sed 's/ /./g' | awk -F. '{$$(NF-1) = 0;} 1' | sed 's/ /./g' | awk -F. '{$$(NF) = 0;} 1' | sed 's/ /./g' `\"" > ${PROJECT}/__init__.py
release-major: test _release-major git-release current-version

release: release-patch
