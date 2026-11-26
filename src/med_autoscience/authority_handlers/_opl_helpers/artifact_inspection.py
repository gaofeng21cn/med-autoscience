"""Read-only contained-file fingerprinting primitives."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat


class ContainedFileReadError(RuntimeError):
    """A file could not be read through the declared safe-root boundary."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def fingerprint_contained_regular_file(
    root_value: str | Path,
    ref_value: str | Path,
) -> tuple[int, str]:
    """Hash a stable regular file in bounded memory through a physical root."""

    _, _, _, size_bytes, digest = _inspect_contained_regular_file(
        root_value, ref_value, max_bytes=None, collect_bytes=False, resolve_root=False,
    )
    return size_bytes, digest


def _inspect_contained_regular_file(
    root_value: str | Path,
    ref_value: str | Path,
    *,
    max_bytes: int | None,
    collect_bytes: bool,
    resolve_root: bool,
) -> tuple[Path, Path, bytes, int, str]:
    root_input = Path(root_value)
    if not root_input.is_absolute():
        raise ContainedFileReadError("root_not_absolute", "root must be an absolute path")
    try:
        root = root_input.resolve(strict=True) if resolve_root else root_input
    except OSError as error:
        raise ContainedFileReadError("root_unavailable", str(error)) from error
    if not root.is_dir():
        raise ContainedFileReadError("root_not_directory", f"root is not a directory: {root}")

    ref_text = os.fspath(ref_value)
    ref = Path(ref_text)
    if (
        ref.is_absolute()
        or not ref.parts
        or ref.as_posix() != ref_text
        or any(part in {"", ".", ".."} for part in ref.parts)
    ):
        raise ContainedFileReadError(
            "ref_not_contained",
            "ref must be a normalized root-relative path",
        )

    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or os.open not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
        or os.stat not in os.supports_follow_symlinks
    ):
        raise ContainedFileReadError(
            "safe_open_unsupported",
            "host Python does not support directory-relative no-follow reads",
        )

    directory_descriptors: list[int] = []
    descriptor: int | None = None
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        root_before = root.lstat()
        if not stat.S_ISDIR(root_before.st_mode):
            raise ContainedFileReadError("root_not_directory", "root must be a physical directory")
        directory_descriptors.append(os.open(root, directory_flags))
        root_opened = os.fstat(directory_descriptors[-1])
        if (root_opened.st_dev, root_opened.st_ino) != (root_before.st_dev, root_before.st_ino):
            raise ContainedFileReadError("identity_changed", "root changed while opening")
        for part in ref.parts[:-1]:
            before_directory = os.stat(
                part,
                dir_fd=directory_descriptors[-1],
                follow_symlinks=False,
            )
            if stat.S_ISLNK(before_directory.st_mode):
                raise ContainedFileReadError(
                    "ref_symlink",
                    f"ref traverses a symlink: {ref_text}",
                )
            if not stat.S_ISDIR(before_directory.st_mode):
                raise ContainedFileReadError(
                    "ref_not_directory",
                    f"ref traverses a non-directory: {ref_text}",
                )
            next_directory = os.open(
                part,
                directory_flags,
                dir_fd=directory_descriptors[-1],
            )
            opened_directory = os.fstat(next_directory)
            if (opened_directory.st_dev, opened_directory.st_ino) != (
                before_directory.st_dev,
                before_directory.st_ino,
            ):
                os.close(next_directory)
                raise ContainedFileReadError(
                    "identity_changed",
                    f"ref changed while opening: {ref_text}",
                )
            directory_descriptors.append(next_directory)

        filename = ref.parts[-1]
        before = os.stat(
            filename,
            dir_fd=directory_descriptors[-1],
            follow_symlinks=False,
        )
        if stat.S_ISLNK(before.st_mode):
            raise ContainedFileReadError("ref_symlink", f"ref traverses a symlink: {ref_text}")
        if not stat.S_ISREG(before.st_mode):
            raise ContainedFileReadError("not_regular_file", f"ref is not a regular file: {ref_text}")
        if max_bytes is not None and before.st_size > max_bytes:
            raise ContainedFileReadError(
                "file_too_large",
                f"ref exceeds the {max_bytes}-byte read limit: {before.st_size}",
            )
        descriptor = os.open(
            filename,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=directory_descriptors[-1],
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ContainedFileReadError("not_regular_file", f"ref is not a regular file: {ref_text}")
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ContainedFileReadError("identity_changed", f"ref changed while opening: {ref_text}")
        digest = hashlib.sha256()
        size_bytes = 0
        chunks: list[bytes] = []
        while chunk := os.read(
            descriptor,
            1024 * 1024 if max_bytes is None else min(1024 * 1024, max_bytes - size_bytes + 1),
        ):
            size_bytes += len(chunk)
            if max_bytes is not None and size_bytes > max_bytes:
                raise ContainedFileReadError(
                    "file_too_large", f"ref exceeds the {max_bytes}-byte read limit while reading",
                )
            digest.update(chunk)
            if collect_bytes:
                chunks.append(chunk)
        after_descriptor = os.fstat(descriptor)
        after = os.stat(
            filename,
            dir_fd=directory_descriptors[-1],
            follow_symlinks=False,
        )

        def identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
            return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns

        if (
            not stat.S_ISREG(after_descriptor.st_mode)
            or stat.S_ISLNK(after.st_mode)
            or identity(opened) != identity(after_descriptor)
            or identity(opened) != identity(after)
            or size_bytes != opened.st_size
        ):
            raise ContainedFileReadError("identity_changed", f"ref changed while reading: {ref_text}")
    except ContainedFileReadError:
        raise
    except OSError as error:
        raise ContainedFileReadError("file_unavailable", str(error)) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)
    return root, root / ref, b"".join(chunks), size_bytes, f"sha256:{digest.hexdigest()}"


__all__ = [
    "ContainedFileReadError",
    "fingerprint_contained_regular_file",
]
