# How to make a new release

Steps to make a new release.

1. Review versions of all dependencies.
2. Go to the minor version branch, or create a minor version branch.
3. Check release notes describe what's new in this release.
4. Increase version number to new release version number.
5. Check copyright year in LICENSE file.
6. Run 'make prepush'.
7. Run 'make prepare-distribution'.
8. Fix any errors, until built distribution is working.
9. Push changes to GitHub and wait for CI to pass.
10. Set date of release in release notes.
11. Fix the links at the top of the README file (branch should point to branch, main to most recent release branch).
12. Commit these changes to the docs.
13. Create a Git tag with the number of the version, prefixed with 'v' and set the message to the same thing.
14. Push doc changes and tag to GitHub, and wait for docs to build in readthedocs.
15. In readthedocs, adjust default version to point to new release version of the docs (tagged version).
16. Run 'make prepare-distribution' again.
17. Run 'twine upload ./dist/eventsourcing-VERSION.tar.gz'.
18. Run './dev/test-released-distribution' script (from project root directory).
19. Check documentation has been built and installed.
20. Check PyPI shows new release.
21. Checkout main branch.
22. Merge changes into main branch.
23. Check version number on main branch is next minor version + '.0dev0'.
