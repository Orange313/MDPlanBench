"""Current paper figures, through the complete audited CPU pipeline."""
from pathlib import Path
import subprocess,sys
raise SystemExit(subprocess.call([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/reproduce_submission.py'),*sys.argv[1:]]))
