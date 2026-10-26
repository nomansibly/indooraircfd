from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--output',default='site-dist');a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=Path(a.output).resolve();(out/'assets').mkdir(parents=True,exist_ok=True)
for f in (root/'web').iterdir():
    if f.suffix in ['.html','.mjs']:shutil.copyfile(f,out/f.name)
for f in (root/'results').glob('*.png'):shutil.copyfile(f,out/'assets'/f.name)
for f in (root/'results/rans').glob('*.png'):shutil.copyfile(f,out/'assets'/('rans-'+f.name))
shutil.copyfile(root/'results/transient/workday.png',out/'assets/workday.png')
shutil.copyfile(root/'results/comparison.csv',out/'assets/comparison.csv')
shutil.copyfile(root/'geometry/layouts.svg',out/'assets/layouts.svg')
print(out)
