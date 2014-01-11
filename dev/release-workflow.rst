Release HOWTO
=============

* Update CHANGELOG
* Bump version
* pyroma .
* check-manifest
* `python setup.py egg_info sdist bdist_wheel bdist_egg register upload` (should test before upload ...)
* `python3 setup.py egg_info bdist_egg register upload`
* Check PyPI release page for obvious errors
* `git commit`
* `git tag -a v{version} -m 'Version {version}'`
* `git push --tags && git push`

