"""Package apex_agent into submission_v4.tar.gz for Kaggle submission."""
import os
import tarfile
import shutil

os.makedirs("temp_sub_v4", exist_ok=True)
shutil.copy("apex_agent.py", os.path.join("temp_sub_v4", "main.py"))

with tarfile.open("submission_v4.tar.gz", "w:gz") as tar:
    tar.add(os.path.join("temp_sub_v4", "main.py"), arcname="main.py")

print("Created submission_v4.tar.gz successfully!")
shutil.rmtree("temp_sub_v4")
