docs:
	sphinx-build -b gettext . _build/locale/
	sphinx-build -b html . _build

gettext:
	find ./ehforwarderbot -iname "*.py" | xargs xgettext -o ./ehforwarderbot/locale/ehforwarderbot.pot

crowdin: docs gettext
	find "$PWD" -iname '*.po' -exec zsh -c 'msgfmt "$0" -o "${0%.po}.mo"' {} \;
	crowdin push

unittest:
	python -m unittest

crowdin-pull:
	crowdin pull
	find "$PWD" -iname '*.po' -exec zsh -c 'msgfmt "$0" -o "${0%.po}.mo"' {} \;

publish:
	python setup.py sdist bdist_wheel upload --sign --show-response

pre-release: crowdin crowdin-pull
