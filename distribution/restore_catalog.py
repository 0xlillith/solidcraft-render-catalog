#!/usr/bin/env python3
"""Download, verify and restore the private catalog without overwriting different files.
Requires Python 3.10+ and an authenticated GitHub CLI for downloads.
Run: python distribution/restore_catalog.py --destination ./restored
Use --offline after downloading all release ZIPs into --archive-dir.
This does not run authoring scripts, install dependencies or modify SolidCraft.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import zipfile


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(4 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def safe_relative(name: str) -> Path:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '\\' in name or ':' in name or any(x in ('..', '.') for x in p.parts):
        raise ValueError('Unsafe catalog path: ' + name)
    return Path(*p.parts)


def restore(manifest_dir: Path, archive_dir: Path, destination: Path,
            offline: bool = False, verify_only: bool = False) -> dict:
    release = json.loads((manifest_dir / 'RELEASE-ARTIFACTS.json').read_text(encoding='utf-8'))
    full_path = manifest_dir / 'CATALOG-FILES.json'
    full_receipt = next(x for x in release['additional_assets'] if x['name'] == full_path.name)
    if sha256(full_path) != full_receipt['sha256']:
        raise ValueError('File manifest checksum mismatch')
    full = json.loads(full_path.read_text(encoding='utf-8'))
    root_name = release['root_name']
    if safe_relative(root_name).name != root_name:
        raise ValueError('Invalid root directory')
    expected = {root_name + '/' + row['path']: row for row in full['files']}
    if len(expected) != full['count']:
        raise ValueError('Duplicate file manifest entries')
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = destination.resolve()
    verified = restored = unchanged = 0
    for asset in release['archives']:
        name = asset['name']
        if safe_relative(name).name != name:
            raise ValueError('Invalid archive name')
        archive_path = archive_dir / name
        if not archive_path.is_file():
            if offline or not shutil.which('gh'):
                raise FileNotFoundError('Missing archive; use authenticated gh or download it first: ' + str(archive_path))
            subprocess.run(['gh', 'release', 'download', release['tag'], '--repo', release['repository'],
                            '--pattern', name, '--dir', str(archive_dir)], check=True)
        if archive_path.stat().st_size != asset['bytes'] or sha256(archive_path) != asset['sha256']:
            raise ValueError('Archive checksum mismatch: ' + name)
        members_expected = {p: row for p, row in expected.items() if row['archive'] == name}
        with zipfile.ZipFile(archive_path) as z:
            infos = z.infolist()
            if len(infos) != len(members_expected) or {i.filename for i in infos} != set(members_expected):
                raise ValueError('Unexpected, missing or duplicate archive members: ' + name)
            for info in infos:
                row = members_expected[info.filename]
                if stat.S_ISLNK(info.external_attr >> 16) or info.file_size != row['bytes']:
                    raise ValueError('Invalid archive member: ' + info.filename)
                target = destination / safe_relative(info.filename)
                if not target.resolve().is_relative_to(destination):
                    raise ValueError('Destination escapes the restoration directory')
                if target.exists():
                    if not target.is_file() or sha256(target) != row['sha256']:
                        raise FileExistsError('Refusing to overwrite different local content: ' + str(target))
                    unchanged += 1
                    verified += 1
                    continue
                output = None
                temporary = target.with_name(target.name + '.restore-partial')
                try:
                    if not verify_only:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        output = temporary.open('xb')
                    h = hashlib.sha256()
                    count = 0
                    with z.open(info) as source:
                        while block := source.read(1024 * 1024):
                            count += len(block)
                            if count > row['bytes']:
                                raise ValueError('Expanded size exceeds manifest')
                            h.update(block)
                            if output is not None:
                                output.write(block)
                    if output is not None:
                        output.close()
                        output = None
                    if count != row['bytes'] or h.hexdigest() != row['sha256']:
                        raise ValueError('File checksum mismatch: ' + info.filename)
                    if not verify_only:
                        if target.exists():
                            raise FileExistsError('Destination appeared during restoration: ' + str(target))
                        temporary.rename(target)
                        restored += 1
                    verified += 1
                finally:
                    if output is not None:
                        output.close()
        print(f'Verified {name}: {len(infos)} files', flush=True)
    if verified != full['count']:
        raise ValueError('Incomplete restoration')
    return {'verified_files': verified, 'restored_files': restored, 'unchanged_files': unchanged,
            'bytes': full['bytes'], 'destination': str(destination / root_name), 'verify_only': verify_only}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path('restored'))
    parser.add_argument('--archive-dir', type=Path, default=Path('downloads'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    try:
        result = restore(Path(__file__).resolve().parent, args.archive_dir, args.destination,
                         args.offline, args.verify_only)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print('Restoration refused: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
