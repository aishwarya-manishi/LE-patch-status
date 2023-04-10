import git
import shutil
import os
import subprocess
import csv
import re

# Set the repository URL and branch
repo_url = "https://github.com/intel-innersource/os.linux.bigbang.kernel-mtl.git"
branch_name = "6.2.7-stage"

# define output function
output_file = "../patchstatus.txt"


def f_out(line):
    with open(output_file, "a") as file:
        file.write(line)


# Check if the repository exists
try:
    repo = git.Repo("../6.0.2-stage/")
    if not repo.bare:
        print("Repository already exists.")
except git.exc.InvalidGitRepositoryError:
    # Clone the repository
    repo = git.Repo.clone_from(repo_url, branch_name)

    # Add two remote repositories
    lkml_url = "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
    drmtip_url = "https://anongit.freedesktop.org/git/drm-tip.git"

    lkml = repo.create_remote("lkml", lkml_url)
    drmtip = repo.create_remote("drmtip", drmtip_url)

    print("Repository cloned.")
    # shutil.copy("../mtl_beta_patchestatus.py", "/home/aishwarya/statuspatch/6.0.2-stage")

# Fetch and initialize origin branch of mtl:
repo.remotes["origin"].fetch(refspec="6.2.7-stage")
# Fetch and initialize lkml and drmtip refs
repo.remotes["lkml"].fetch(refspec="master")
# repo.remotes["lkml"].update_tracking_branch()
repo.remotes["drmtip"].fetch(refspec="drm-tip")
# repo.remotes["drmtip"].update_tracking_branch()
# print("Done")

# Loop through all commits in the branch and search for the message
for commit in repo.iter_commits():
    commit_message = commit.message.splitlines()[0]
    if commit_message.startswith(("INTERNAL", "MAINT_GIT", "UPSTREAM")):
        message = commit_message.split(":", maxsplit=1)[1].strip()
        if message.startswith("BACKPORT"):
            message = message.split(":", maxsplit=1)[1].strip()
        if message.startswith("INTEL_DII"):
            message = message.split(":", maxsplit=1)[1].strip()
        if message.startswith("FIXME"):
            message = message.split(":", maxsplit=1)[1].strip()

        # Search for the message in lkml
        lkml_commit = repo.git.log("-F", "--grep", message, "--pretty=oneline",
                                   "lkml/master", "-1")
        if lkml_commit:
            f_out(
                f"UPSTREAM: {lkml_commit.split(' ', maxsplit=1)[0].strip()} {commit_message} \n"
            )
        else:
            # Search for the message in drmtip
            drmtip_commit = repo.git.log("-F", "--grep", message,
                                         "--pretty=oneline", "drmtip/drm-tip",
                                         "-1")
            if drmtip_commit:
                f_out(
                    f"MAINT_GIT: {drmtip_commit.split(' ', maxsplit=1)[0].strip()} {commit_message} \n"
                )
            elif (subprocess.run(
                [
                    "pwclient", "search",
                    message.split(":", maxsplit=1)[1].strip()
                ],
                    stdout=subprocess.PIPE,
            ).stdout.decode().split("\n")[2]):
                f_out(f"MLIST: {commit} {commit_message} \n")
            else:
                f_out(f"NOT_OPENSOURCED: {commit} {commit_message} \n")
        if message == "drm/i915/dvo: Remove unused panel_wants_dither":
            break

# Read the contents of the text file into a list
with open("../patchstatus.txt", "r") as infile:
    lines = infile.readlines()
    # Open the CSV file for writing
    with open("../patch.csv", "w", newline="") as outfile:
        # Create a CSV writer object
        writer = csv.writer(outfile)

        # Write the header row
        writer.writerow(["Status", "Commit_ID", "Commit_Message"])

        # Loop through each line in the list
        for line in lines:
            # Split the line into fields
            fields = line.strip().split(" ", 2)

            # Write the fields to the CSV file
            writer.writerow(fields)

# Specify the path of the text file and the destination directory
file_path = "../patchstatus.txt"
dest_dir = "/var/www/html/patchstatus/"

# Use the shutil.copy() function to copy the file
shutil.copy(file_path, dest_dir)

# Use os.remove() function to delete the original file
os.remove(file_path)

# Specify the path of the xl file and the destination directory
file_path = "../patch.csv"
dest_dir = "/var/www/html/patchstatus/"

# Use the shutil.copy() function to copy the file
shutil.copy(file_path, dest_dir)

# Use os.remove() function to delete the original file
os.remove(file_path)
