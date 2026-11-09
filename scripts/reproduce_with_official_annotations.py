"""CPU only, original mechanism scripts + pinned already-used public benchmarks."""
from pathlib import Path
import argparse,subprocess,sys
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--official-cache',type=Path,required=True);ap.add_argument('--accept-upstream-terms',action='store_true');a=ap.parse_args();G=Path(__file__).resolve().parents[1]
if not a.accept_upstream_terms:ap.error('Read Biomedical noncommercial/share-alike and Economics/original-source terms first; explicit acknowledgment required')
if a.output.resolve().is_relative_to(G) or a.official_cache.resolve().is_relative_to(G):ap.error('Outputs and raw official annotations must stay outside Git')
# Only Biomedical/Economics locks are admitted by the original extension.
raise SystemExit(subprocess.call([sys.executable,str(G/'planb014_full/reproduce_full.py'),'--output',str(a.output.resolve()),'--official-cache',str(a.official_cache.resolve()),'--skip-parent'],cwd=G))
