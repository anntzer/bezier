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


import argparse
import os
import sys


def clean_file(c_source):
    """Strip trailing whitespace and clean up "local" names in C source.

    These source files are autogenerated from the ``cython`` CLI.

    Args:
        c_source (str): Path to a ``.c`` source file.
    """
    with open(c_source, 'r') as file_obj:
        contents = file_obj.read().rstrip()

    # Replace the path to the Cython include files.
    py_version = 'python{}.{}'.format(*sys.version_info[:2])
    for nox_env in ('update-true', 'update-false'):
        lib_path = os.path.join(
            '.nox', nox_env, 'lib',  py_version, 'site-packages', '')
        contents = contents.replace(lib_path, '')

    # Write the files back, but strip all trailing whitespace.
    lines = contents.split('\n')
    with open(c_source, 'w') as file_obj:
        for line in lines:
            file_obj.write(line.rstrip() + '\n')


def main():
    parser = argparse.ArgumentParser(
        description='Clean / strip from C source code.')
    parser.add_argument(
        'filename', metavar='filename', nargs=1,
        help='Filename for source to be cleaned.')

    args = parser.parse_args()
    # Assert that it is a singleton list.
    filename, = args.filename
    clean_file(filename)


if __name__ == '__main__':
    main()