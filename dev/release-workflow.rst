Release HOWTO
=============

* Update CHANGELOG
* Bump version
* pyroma .
* check-manifest
* `python setup.py egg_info sdist bdist_wheel bdist_egg register`
* `python3 setup.py egg_info bdist_egg register`
* Test the package
* Upload `twine upload dist/*`
* Check PyPI release page for obvious errors
* `git commit`
* `git tag -a v{version} -m 'Version {version}'`
* Set version to "{version+1}-dev"
* `git commit`
* `git push --tags && git push`
* Build documentation for the tag v{version} on rtfd.org
* Set the default rtfd version to {version}
