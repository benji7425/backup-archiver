# Maintainer: Benjamin Higgins <bhigginsuk@protonmail.com>
pkgname=bhiggins-backup-archiver-git
pkgver=r44.da9bbe0
pkgrel=1
pkgdesc="Archive directories based on the differences since the last run"
arch=("any")
url="https://github.com/bhigginsuk/backup-archiver"
license=('Unlicense')
depends=("python-yaml")
makedepends=('git') # 'bzr', 'git', 'mercurial' or 'subversion'
provides=("${pkgname%-git}")
conflicts=("${pkgname%-git}")
source=("bhiggins-backup-archiver::git+$url")
md5sums=('SKIP')

# Please refer to the 'USING git SOURCES' section of the PKGBUILD man page for
# a description of each element in the source array.

pkgver() {
	cd "$srcdir/${pkgname%-git}"

	printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

prepare() {
	cd "$srcdir/${pkgname%-git}"
	patch -p1 -i "$srcdir/${pkgname%-git}/linux.patch"
}

build() {
	cd "$srcdir/${pkgname%-git}"
    echo "Building..."
    python setup.py build
}

package() {
	cd "$srcdir/${pkgname%-git}"
    python setup.py install --root="$pkgdir"
}
