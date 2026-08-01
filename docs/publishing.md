# Publishing to PyPI

Project Mentor publishes with GitHub Actions Trusted Publishing. No long-lived
PyPI token is stored in GitHub or a local environment.

## Trusted Publisher identity

The PyPI publisher must match these values exactly:

| Field | Value |
| --- | --- |
| PyPI project | `project-mentor` |
| GitHub owner | `uczltw6` |
| Repository | `project-mentor` |
| Workflow | `release.yml` |
| Environment | `pypi` |

For the first upload, register this identity as a pending publisher under the
PyPI account's Publishing page. A pending publisher does not reserve the name;
the project is created when the first matching OIDC upload succeeds.

## Security boundary

The release workflow keeps `id-token: write` on the publish job only. That job
has two steps: download the previously validated artifact, then invoke the
pinned PyPA publishing action. The build job checks out the release tag,
creates wheel and source distributions with pinned tooling, validates their
metadata and exact contents, installs the wheel offline in a fresh virtual
environment, and passes the artifacts to the publish job.

The `pypi` GitHub Environment and protected `main` branch are part of the
publisher identity. The publishing action generates PyPI attestations by
default. There are no repository PyPI passwords or API-token secrets.

## First v0.3.0 publication

Because GitHub Release `v0.3.0` predates the publishing workflow, start the
workflow manually from `main` with `tag` set to `v0.3.0`. Do not enable
`skip-existing`: a duplicate version must fail visibly because PyPI files are
immutable.

After the first publication is independently verified, remove the temporary
manual trigger. Future releases publish from the `release: published` event.

## Future release sequence

1. Merge the version, changelog, and release-note update through protected
   `main` and wait for CI plus CodeQL.
2. Tag that exact `main` commit with `v<version>`.
3. Publish the matching GitHub Release.
4. Let `release.yml` build, validate, and publish through the `pypi`
   Environment.
5. Download from the public PyPI index into a fresh environment and verify the
   version, dependency metadata, project URLs, and attestations.
