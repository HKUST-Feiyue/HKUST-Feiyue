"""Build browser fixtures through the production pipeline, independent of site stories."""
from contextlib import contextmanager
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml


@contextmanager
def browser_site(source):
    with tempfile.TemporaryDirectory(prefix='hkust-browser-') as directory:
        root = Path(directory)
        for name in ('assets', 'data', 'scripts'):
            shutil.copytree(source / name, root / name)
        for name in ('index.html', 'submit.html', 'community.html', 'preview.py', 'PUBLISHED_README.md'):
            shutil.copy2(source / name, root / name)
        (root / 'content').mkdir()
        categories = ('further-studies', 'research', 'career', 'exchange', 'entrepreneurship')
        for i, (category, degree) in enumerate(zip(categories, ('BSc', 'MPhil', 'MSc', 'BEng', 'MBA')), 1):
            meta = dict(author=f'Fixture author {i}', destination=f'Fixture destination {i}',
                        campus='hk' if i % 2 else 'gz', year=str(2019+i),
                        term='spring' if i == 3 else 'fall', degree=degree,
                        field=f'Fixture field {i}', category=category,
                        published_at=f'2026-11-{19+i}T00:00:00Z',
                        contact=[dict(type='QA', value='contactexcluded7x9')])
            body = '## Preparation\n\nbodytokenqa test content.\n\n## Reflection\n\n' + ('Independent browser fixture paragraph.\n\n' * 12)
            (root / f'content/fixture-{category}.md').write_text('---\n'+yaml.safe_dump(meta)+'---\n'+body, encoding='utf-8')
        subprocess.run([sys.executable, 'preview.py', '--build-only'], cwd=root, check=True)
        yield root
