"""Correct the copied renderer's bounds check to use its actual tight export box."""
import common as C
from pathlib import Path
import os
import shutil
import subprocess

base=C.ART/"EX7"
source=base/"paper_figure_source"
target=base/"paper_figure_source_exportbounds_001"
shutil.copytree(source,target,ignore=shutil.ignore_patterns("__pycache__"))
style=target/"style.py"
text=style.read_text()
assert text.count("bounds=fig.bbox")==1
old="if bb.x0<-.75 or bb.y0<-.75 or bb.x1>bounds.width+.75 or bb.y1>bounds.height+.75:outside.append(t.get_text())"
new="if bb.x0<bounds.x0-.75 or bb.y0<bounds.y0-.75 or bb.x1>bounds.x1+.75 or bb.y1>bounds.y1+.75:outside.append(t.get_text())"
assert old in text
text=text.replace("bounds=fig.bbox","bounds=fig.get_tightbbox(renderer).transformed(fig.dpi_scale_trans)")
text=text.replace(old,new)
style.write_text(text)
C.write(base/"export_bounds_repair_001.json",dict(
    before_sha256=C.sha(source/"style.py"),after_sha256=C.sha(style),
    change="pre-export check uses actual bbox_inches=tight extent",
    drawing_commands_changed=False,CSV_or_statistics_changed=False))
out=base/"private_figure_replay_exportbounds_001"
(out/"qa").mkdir(parents=True)
env=os.environ.copy()
env["MDROUTER_FIG_OUT"]=str(out)
python="${RUNTIME_DIR}/bin/python"
with (base/"private_figure_replay_exportbounds_001.log").open("x") as log:
    subprocess.run([python,str(target/"make_019.py")],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
bound=C.load(C.ART/"baseline/binding_and_revision_QA.json")
mapping={"fig1_overview.png":"fig1_industrial_ab_019.png",
         "fig2_testbed.png":"fig2_testbed_017_019.png",
         "fig3_frontier.png":"fig3_static_frontiers_018_019.png",
         "fig4_decision.png":"fig4_decision_information_019.png",
         "fig5_lifecycle.png":"fig5_lifecycle_017_019.png",
         "fig6_aa.png":"fig6_aa_equivalence_019.png"}
checks=[]
for asset in bound["figures"]["files"]:
    path=out/mapping[Path(asset["logicalPath"]).name]
    actual=C.sha(path)
    checks.append(dict(paper_path=asset["logicalPath"],expected=asset["contentHash"],
                       replay=actual,identical=actual==asset["contentHash"]))
C.table(C.REPORT/"EX7/paper_figure_hash_checks.csv",checks)
print(checks,flush=True)
