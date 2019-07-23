Release HOWTO
=============

* Update CHANGELOG
* Bump version
* pyroma .
* check-manifest
* `rm dist/*`
* `python3 setup.py egg_info bdist_egg bdist_wheel`
* Test the packages in dist/
* Upload `twine upload dist/*`
* Check PyPI release page for obvious errors
* `git commit`
* `git tag -a v{version} -m 'Version {version}'`
* Set version to "{version+1}-dev"
* `git commit`
* `git push --tags && git push`
* Build documentation for the tag v{version} on rtfd.org
* Set the default rtfd version to {version}
* Bump again the version to <version+1>-indev
