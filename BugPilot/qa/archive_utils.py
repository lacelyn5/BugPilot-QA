"""Safe, non-executing import of source files from ZIP archives."""

import shutil
import stat
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from django.conf import settings


MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_EXTRACTED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_FILES = 5000
MAX_ARCHIVE_ENTRIES = 10000
CHUNK_SIZE = 1024 * 1024


class ProjectArchiveError(ValueError):
    """Raised when an uploaded ZIP is invalid or unsafe to extract."""


def _validated_members(archive):
    members = []
    seen_paths = set()
    declared_total = 0
    file_count = 0
    entries = archive.infolist()

    if len(entries) > MAX_ARCHIVE_ENTRIES:
        raise ProjectArchiveError(
            f"The ZIP contains too many entries (maximum {MAX_ARCHIVE_ENTRIES})."
        )

    for info in entries:
        raw_name = info.filename.replace("\\", "/")
        archive_path = PurePosixPath(raw_name)

        if (
            not raw_name
            or archive_path.is_absolute()
            or any(part in {"..", "."} for part in archive_path.parts)
        ):
            raise ProjectArchiveError("The ZIP contains an unsafe file path.")

        if any(":" in part for part in archive_path.parts):
            raise ProjectArchiveError("The ZIP contains an unsafe Windows file path.")

        if info.flag_bits & 0x1:
            raise ProjectArchiveError("Encrypted ZIP files are not supported.")

        mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(mode)
        if stat.S_ISLNK(mode):
            raise ProjectArchiveError(
                "The ZIP contains a symbolic link, which is not allowed."
            )
        if file_type and file_type not in {stat.S_IFREG, stat.S_IFDIR}:
            raise ProjectArchiveError(
                "The ZIP contains a special file type that is not allowed."
            )

        normalized_path = "/".join(archive_path.parts)
        duplicate_key = normalized_path.casefold()
        if duplicate_key in seen_paths:
            raise ProjectArchiveError("The ZIP contains duplicate file paths.")
        seen_paths.add(duplicate_key)

        if info.is_dir():
            continue

        file_count += 1
        declared_total += info.file_size
        if file_count > MAX_ARCHIVE_FILES:
            raise ProjectArchiveError(
                f"The ZIP contains too many files (maximum {MAX_ARCHIVE_FILES})."
            )
        if declared_total > MAX_EXTRACTED_BYTES:
            raise ProjectArchiveError(
                "The extracted project cannot be larger than 100 MB."
            )

        members.append((info, archive_path))

    if not members:
        raise ProjectArchiveError("The ZIP does not contain any files.")
    return members


def extract_project_archive(uploaded_file):
    """Extract validated ZIP contents under ``uploaded_projects``.

    File paths, special entries, declared sizes and actual decompressed bytes are
    checked. Imported source code is written as data and is never executed.
    """
    if uploaded_file.size > MAX_ARCHIVE_BYTES:
        raise ProjectArchiveError("The ZIP file must be 20 MB or smaller.")

    base_dir = Path(settings.BASE_DIR).resolve()
    upload_root = (base_dir / "uploaded_projects").resolve()
    upload_root.mkdir(parents=True, exist_ok=True)

    target_dir = upload_root / uuid.uuid4().hex
    target_dir.mkdir(parents=False, exist_ok=False)

    try:
        try:
            archive = zipfile.ZipFile(uploaded_file)
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise ProjectArchiveError("This file is not a valid ZIP archive.") from exc

        with archive:
            members = _validated_members(archive)
            extracted_total = 0

            for info, archive_path in members:
                destination = (target_dir / Path(*archive_path.parts)).resolve()
                if not destination.is_relative_to(target_dir.resolve()):
                    raise ProjectArchiveError("The ZIP contains a file outside the project folder.")

                destination.parent.mkdir(parents=True, exist_ok=True)
                written_for_file = 0
                with archive.open(info, "r") as source, destination.open("wb") as target_file:
                    while True:
                        chunk = source.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        written_for_file += len(chunk)
                        extracted_total += len(chunk)
                        if written_for_file > info.file_size:
                            raise ProjectArchiveError(
                                "A ZIP entry expanded beyond its declared size."
                            )
                        if extracted_total > MAX_EXTRACTED_BYTES:
                            raise ProjectArchiveError(
                                "The extracted project cannot be larger than 100 MB."
                            )
                        target_file.write(chunk)

                if written_for_file != info.file_size:
                    raise ProjectArchiveError(
                        "A ZIP entry size does not match its declared size."
                    )

        return str(target_dir.relative_to(base_dir))
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise


def remove_project_source(relative_directory):
    """Remove imported files only when their path is under ``uploaded_projects``."""
    if not relative_directory:
        return

    base_dir = Path(settings.BASE_DIR).resolve()
    upload_root = (base_dir / "uploaded_projects").resolve()
    target = (base_dir / relative_directory).resolve()

    if target != upload_root and target.is_relative_to(upload_root):
        shutil.rmtree(target, ignore_errors=True)
