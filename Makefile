sphinx:
	sphinx-build -b gettext ./docs docs/_build/locale/
	sphinx-build -b html ./docs docs/_build

gettext:
	find ./ehforwarderbot -iname "*.py" | xargs xgettext --add-comments=TRANSLATORS -o ./ehforwarderbot/locale/ehforwarderbot.pot

crowdin: sphinx gettext
	find "$(CURDIR)" -iname '*.po' -exec bash -c 'msgfmt "$$0" -o "$${0%.po}.mo"' {} \;
	crowdin push

unittest:
	python -m unittest

crowdin-pull:
	crowdin pull
	find "$(CURDIR)" -iname '*.po' -exec bash -c 'msgfmt "$$0" -o "$${0%.po}.mo"' {} \;

publish:
	python setup.py sdist bdist_wheel upload --sign --show-response

pre-release: crowdin crowdin-pull
	git add \*.po
	git commit -S -m 'Sync localization files from Crowdin'
