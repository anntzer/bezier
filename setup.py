# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup file for ``bezier``."""

import hashlib
import os
import shutil
import sys
import tempfile

import pkg_resources
import setuptools
import setuptools.command.build_ext


VERSION = "2020.1.15.dev1"  # Also in ``codemeta.json`` and ``__init__.py``.
AUTHOR = "Danny Hermes"  # Also in ``__init__.py``.
README_FILENAME = os.path.join(os.path.dirname(__file__), "README.rst")
NUMPY_MESSAGE = """\
Error: NumPy needs to be installed first. It can be installed via:

$ python    -m pip install numpy
$ python3.8 -m pip install numpy
$ # OR
$ conda install numpy
"""
NO_EXTENSION_ENV = "BEZIER_NO_EXTENSION"
NO_SPEEDUPS_MESSAGE = """\
The {} environment variable has been used to explicitly disable the
building of the binary extension module.
""".format(
    NO_EXTENSION_ENV
)
READTHEDOCS_ENV = "READTHEDOCS"
ON_READTHEDOCS_MESSAGE = """\
The {} environment variable has been detected, the binary extension module
will not be built.
""".format(
    READTHEDOCS_ENV
)
INSTALL_PREFIX_ENV = "BEZIER_INSTALL_PREFIX"
NO_INSTALL_PREFIX_MESSAGE = (
    "The {} environment variable must be set."
).format(INSTALL_PREFIX_ENV)
REQUIREMENTS = ("numpy >= 1.18.1",)
EXTRAS_REQUIRE = {"full": ["scipy >= 1.4.1", "sympy >= 1.5.1"]}
DESCRIPTION = (
    u"Helper for B\u00e9zier Curves, Triangles, and Higher Order Objects"
)
_IS_WINDOWS = os.name == "nt"
_EXTRA_DLL = "extra-dll"


def is_installed(requirement):
    try:
        pkg_resources.require(requirement)
    except pkg_resources.ResolutionError:
        return False

    else:
        return True


def numpy_include_dir():
    if not is_installed("numpy >= 1.9.0"):
        print(NUMPY_MESSAGE, file=sys.stderr)
        sys.exit(1)

    import numpy as np

    return np.get_include()


def _sha256_hash(filename, blocksize=65536):
    """Hash the contents of an open file handle with SHA256"""
    hash_obj = hashlib.sha256()

    with open(filename, "rb") as file_obj:
        block = file_obj.read(blocksize)
        while block:
            hash_obj.update(block)
            block = file_obj.read(blocksize)

    return hash_obj.hexdigest()


def _sha256_short_hash(filename):
    full_hash = _sha256_hash(filename)
    return full_hash[:8]


def _installed_dll(install_prefix):
    return os.path.join(install_prefix, "bin", "bezier.dll")


def prepare_lib_directory():
    """Copy a (renamed) ``bezier.lib`` on Windows to a temporary directory.

    This depends on the SHA256 hash of the ``bezier.dll`` file.
    """
    if not _IS_WINDOWS:
        return None, None

    install_prefix = os.environ.get(INSTALL_PREFIX_ENV)
    if install_prefix is None:
        return None, None

    installed_dll = _installed_dll(install_prefix)
    short_hash = _sha256_short_hash(installed_dll)

    import_library = os.path.join(install_prefix, "lib", "bezier.lib")
    lib_directory_tmp = tempfile.mkdtemp()
    renamed_import_library = os.path.join(
        lib_directory_tmp, f"bezier-{short_hash}.lib"
    )
    shutil.copyfile(import_library, renamed_import_library)
    print(f"Copied {import_library!r} to {renamed_import_library!r}")
    print("*" * 60)
    with open(import_library, "r") as file_obj:
        contents = file_obj.read()
    print(contents)
    print("*" * 60)
    print(repr(contents))
    print("*" * 60)

    return lib_directory_tmp, short_hash


def extension_modules(lib_directory, short_hash):
    if os.environ.get(READTHEDOCS_ENV) == "True":
        print(ON_READTHEDOCS_MESSAGE, file=sys.stderr)
        return []

    if NO_EXTENSION_ENV in os.environ:
        print(NO_SPEEDUPS_MESSAGE, file=sys.stderr)
        return []

    install_prefix = os.environ.get(INSTALL_PREFIX_ENV)
    if install_prefix is None:
        print(NO_INSTALL_PREFIX_MESSAGE, file=sys.stderr)
        sys.exit(1)

    rpath = lib_directory
    if rpath is None:
        rpath = os.path.join(install_prefix, "lib")
    if not os.path.isdir(rpath):
        rpath = os.path.join(install_prefix, "lib64")

    extra_link_args = []
    if not _IS_WINDOWS:
        extra_link_args.append("-Wl,-rpath,{}".format(rpath))

    lib_name = "bezier"
    if short_hash is not None:
        lib_name = f"bezier-{short_hash}"
    print(f"Using lib_name = {lib_name!r}, rpath = {rpath!r}")

    extension = setuptools.Extension(
        "bezier._speedup",
        [os.path.join("src", "python", "bezier", "_speedup.c")],
        include_dirs=[
            numpy_include_dir(),
            os.path.join(install_prefix, "include"),
        ],
        libraries=[lib_name],
        library_dirs=[rpath],
        extra_link_args=extra_link_args,
    )
    return [extension]


def make_readme():
    with open(README_FILENAME, "r") as file_obj:
        return file_obj.read()


def copy_dll(build_lib):
    if not _IS_WINDOWS:
        return

    install_prefix = os.environ.get(INSTALL_PREFIX_ENV)
    if install_prefix is None:
        return

    # NOTE: ``bin`` is hardcoded here, expected to correspond to
    #       ``CMAKE_INSTALL_BINDIR`` on Windows.
    installed_dll = _installed_dll(install_prefix)
    # NOTE: This is re-computing something already done in
    #       ``prepare_lib_directory()``, however the coordination across
    #       these functions isn't worth it.
    short_hash = _sha256_short_hash(installed_dll)

    build_lib_extra_dll = os.path.join(build_lib, "bezier", _EXTRA_DLL)
    os.makedirs(build_lib_extra_dll, exist_ok=True)
    relocated_dll = os.path.join(
        build_lib_extra_dll, f"bezier-{short_hash}.dll"
    )
    shutil.copyfile(installed_dll, relocated_dll)
    print(f"Copied {installed_dll!r} to {relocated_dll!r}")


class BuildExtWithDLL(setuptools.command.build_ext.build_ext):
    def run(self):
        copy_dll(self.build_lib)
        return setuptools.command.build_ext.build_ext.run(self)


def setup():
    lib_directory, short_hash = prepare_lib_directory()
    setuptools.setup(
        name="bezier",
        version=VERSION,
        description=DESCRIPTION,
        author=AUTHOR,
        author_email="daniel.j.hermes@gmail.com",
        long_description=make_readme(),
        scripts=(),
        url="https://github.com/dhermes/bezier",
        project_urls={
            "Documentation": "https://bezier.readthedocs.io/",
            "Changelog": (
                "https://bezier.readthedocs.io/en/latest/releases/index.html"
            ),
            "Issue Tracker": "https://github.com/dhermes/bezier/issues",
        },
        keywords=["Geometry", "Curve", "Bezier", "Intersection", "Python"],
        packages=["bezier"],
        package_dir={"": os.path.join("src", "python")},
        license="Apache 2.0",
        platforms="Posix; macOS; Windows",
        package_data={
            "bezier": ["*.pxd", os.path.join("extra-dll", "*.dll"),]
        },
        zip_safe=True,
        install_requires=REQUIREMENTS,
        extras_require=EXTRAS_REQUIRE,
        ext_modules=extension_modules(lib_directory, short_hash),
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "Topic :: Scientific/Engineering :: Mathematics",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
        ],
        cmdclass={"build_ext": BuildExtWithDLL},
    )
    if lib_directory is not None:
        shutil.rmtree(lib_directory)


def main():
    setup()


if __name__ == "__main__":
    main()
