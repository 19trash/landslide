## Debian Packaging Workflow

### Package version

        1:1.0.0-2xix1~1.gbp661d97

- `1:` → Epoch.  We are using a different versioning scheme other than the
  official Debian package.

- `1.0.0` → Upstream release.

- `2` → The Debian package version we based on.

- `xix1` → Distro (or community) version.

- `~1.gbp661d97` → Git snapshot (`1` is the snapshot number, `661d97` is the
  suffix derived from commit id).  Note that this field is omitted in a stable
  release.

### Update from upstream

        git checkout master
        git pull upstream master

### Start new release

- Create a new version by incrementing distro version.   For example
  `1:1.0.0-2xix1` becomes `1:1.0.0-2xix2`

- Release with the new version

        git dch -N 1:1.0.0-2xix2 -R
        git commit -m "Start a new package release"

### New snapshot

-  Update from upstream branch

        git dch -S -a
        git commit debian/changelog -m "New snapshot"

### Release snapshot

        git dch -R -a
        git commit debian/changelog -m "New release"

### Adapt Debian packaging changes

- Commit selected changes from the new Debian package

- Create a new version by setting the Debian package version.   For example for
  the Debian package version `1.0.0-3`, `1:1.0.0-2xix2` becomes `1:1.0.0-3xix2`

- Release with the new version

        git dch -N 1:1.0.0-3xix2 -R
        git commit -m "Start a new package release"


### Build package

        git buildpackage -sa

### Upload package

        dput 19 <.changes file>
