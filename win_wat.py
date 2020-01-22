import ctypes
import os
import site
import textwrap


def _sort_key(name):
    """Sorting helper for members of a directory."""
    return name.lower().lstrip("_")


def tree(directory, suffix=None):
    """Create string (recursively) containing a pretty-printed file tree."""
    names = sorted(os.listdir(directory), key=_sort_key)
    parts = []
    for name in names:
        path = os.path.join(directory, name)
        if os.path.isdir(path):
            sub_part = tree(path, suffix=suffix)
            if sub_part is not None:
                parts.append(name + os.path.sep)
                parts.append(textwrap.indent(sub_part, "  "))
        else:
            if suffix is None or name.endswith(suffix):
                if os.path.islink(path):
                    link_dst = os.readlink(path)
                    to_add = f"{name} -> {link_dst}"
                    parts.append(to_add)
                else:
                    parts.append(name)

    if parts:
        return "\n".join(parts)
    else:
        return None


def print_tree(directory, suffix=None):
    """Pretty print a file tree."""
    print(os.path.basename(directory) + os.path.sep)
    full_tree = tree(directory, suffix=suffix)
    print(textwrap.indent(full_tree, "  "))


def main():
    try:
        import bezier

        print(f"bezier = {bezier} ({bezier!r})")
    except ImportError as exc:
        print(f"exc = {exc} ({exc!r})")

    (sitepackages,) = site.getsitepackages()
    extra_dll = os.path.join(sitepackages, "bezier", "extra-dll")
    print(f"extra_dll = {extra_dll!r}")
    print_tree(extra_dll)
    (bezier_dll,) = os.listdir(extra_dll)
    print(f"bezier_dll = {bezier_dll!r}")
    name, post = bezier_dll.split(".dll")
    assert post == ""
    try:
        print(ctypes.cdll.LoadLibrary(name))
    except Exception as exc2:
        print(f"exc2 = {exc2} ({exc2!r})")
    os.add_dll_directory(extra_dll)
    try:
        print(ctypes.cdll.LoadLibrary(name))
    except Exception as exc3:
        print(f"exc3 = {exc3} ({exc3!r})")


if __name__ == "__main__":
    main()
