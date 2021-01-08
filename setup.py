from setuptools import setup


def readme():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="bhiggins-backup-archiver",
    version="0.1.0",
    description="Archive directories with 7z to prepare them for backup",
    py_modules=["backup-archiver"],
    package_dir={"": "src"},
    url="https://github.com/bhigginsuk/backup-archiver/",
    author="Benjamin Higgins",
    author_email="contact@brhiggins.com",
    license="The Unlicense",
    long_description=readme(),
    readme=readme(),
    install_requires=["PyYAML"],
)
