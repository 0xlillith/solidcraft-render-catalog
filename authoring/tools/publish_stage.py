"""Publish validated resources to the owner's private repository. No application CI or plugin installer."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, subprocess, tempfile, zipfile
REPOSITORY = '0xlillith/solidcraft-render-catalog'
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''): h.update(data)
    return h.hexdigest()
def gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout

def main():
    p = argparse.ArgumentParser(); p.add_argument('--stage', required=True); p.add_argument('--tag', required=True); a = p.parse_args()
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY: raise RuntimeError('Owner-only publication target')
    stage = pathlib.Path(a.stage).resolve(); workspace = pathlib.Path(os.environ['GITHUB_WORKSPACE']).resolve()
    if not (stage.is_relative_to(workspace / 'authoring') or stage.is_relative_to(workspace / 'quality')) or not stage.is_dir(): raise RuntimeError('Invalid approved resource directory')
    validation = json.loads((stage / 'reports/validation.json').read_text())
    if validation.get('status') != 'PASS': raise RuntimeError('Stage validation has not passed')
    source = os.environ['GITHUB_SHA']; target = workspace / 'publication-output'; target.mkdir()
    groups = {}; source_files = []
    for f in sorted(stage.rglob('*')):
        if not f.is_file() or '.git' in f.parts or '__pycache__' in f.parts: continue
        if f.is_symlink(): raise RuntimeError('Symlink not permitted')
        rel = f.relative_to(stage).as_posix()
        if rel.startswith('build/source-4k/'):
            bits = rel.split('/'); group = 'scanned-master-' + bits[2]
        elif rel.startswith('build/maps/'):
            bits = rel.split('/'); group = 'masters-' + bits[2] if '/master-2048/' in rel else 'runtime-maps'
        else: group = 'catalog-sources-previews'
        groups.setdefault(group, []).append((f, rel))
        source_files.append({'path': rel, 'bytes': f.stat().st_size, 'sha256': sha(f), 'archive': a.tag + '-' + group + '.zip'})
    artifacts = []
    for group, files in sorted(groups.items()):
        zpath = target / (a.tag + '-' + group + '.zip')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
            for f, rel in files: z.write(f, stage.name + '/' + rel)
        if zpath.stat().st_size >= 1900000000: raise RuntimeError('Archive too large')
        with zipfile.ZipFile(zpath) as z:
            if z.testzip() is not None: raise RuntimeError('Archive CRC failure')
        artifacts.append({'name': zpath.name, 'bytes': zpath.stat().st_size, 'sha256': sha(zpath), 'files': len(files)})
    manifest = {'repository': REPOSITORY, 'tag': a.tag, 'source_commit': source, 'stage': stage.name, 'files': source_files, 'artifacts': artifacts, 'plugin_standard': None, 'native_acceptance': 'not_run', 'premium_qualification': 'not_qualified'}
    mp = target / 'PUBLICATION-MANIFEST.json'; mp.write_text(json.dumps(manifest, indent=2) + '\n')
    sums = target / 'SHA256SUMS.txt'; sums.write_text(''.join(x['sha256'] + '  ' + x['name'] + '\n' for x in artifacts) + sha(mp) + '  ' + mp.name + '\n')
    body = target / 'RELEASE-NOTES.md'; body.write_text(f'# {stage.name}: authoring resource snapshot\n\nSource: `{source}`. All {len(source_files)} stage files are included. Extract all ZIPs into the same empty parent directory and open `{stage.name}/index.html`. No plugin or integration standard is defined. See the stage README for physical-source conditions and optical limitations. Native/premium qualification remains pending.\n')
    exists = subprocess.run(['gh', 'release', 'view', a.tag, '--repo', REPOSITORY], capture_output=True)
    if exists.returncode == 0: raise RuntimeError('Tag already exists; inspect rather than overwrite')
    gh('release', 'create', a.tag, '--repo', REPOSITORY, '--target', source, '--title', stage.name + ' — verified resource delivery', '--draft', '--prerelease', '--notes-file', str(body))
    verified = []
    try:
        for f in [*(target / x['name'] for x in artifacts), mp, sums]:
            gh('release', 'upload', a.tag, str(f), '--repo', REPOSITORY)
            with tempfile.TemporaryDirectory() as td:
                gh('release', 'download', a.tag, '--repo', REPOSITORY, '--pattern', f.name, '--dir', td)
                downloaded = pathlib.Path(td) / f.name
                if sha(downloaded) != sha(f): raise RuntimeError('Downloaded asset hash mismatch')
                if f.suffix == '.zip':
                    expected = [x for x in source_files if x['archive'] == f.name]
                    with zipfile.ZipFile(downloaded) as z:
                        if len(z.infolist()) != len(expected): raise RuntimeError('ZIP count mismatch')
                        for row in expected:
                            h = hashlib.sha256()
                            with z.open(stage.name + '/' + row['path']) as member:
                                for data in iter(lambda: member.read(1024 * 1024), b''): h.update(data)
                            if h.hexdigest() != row['sha256']: raise RuntimeError('ZIP member mismatch')
                verified.append(f.name)
            print('UPLOADED_AND_VERIFIED', f.name, flush=True)
        receipt = target / 'PUBLICATION-VERIFIED.json'; receipt.write_text(json.dumps({'status': 'VERIFIED', 'repository': REPOSITORY, 'tag': a.tag, 'source_commit': source, 'verified_assets': verified, 'verified_original_files': len(source_files), 'all_downloaded_members_sha256_checked': True, 'validation': validation}, indent=2) + '\n')
        gh('release', 'upload', a.tag, str(receipt), '--repo', REPOSITORY)
        gh('release', 'edit', a.tag, '--repo', REPOSITORY, '--draft=false', '--latest=false')
    except Exception:
        print('Publication left as draft; inspect completed assets before retry.', flush=True); raise
if __name__ == '__main__': main()
