import os
import shutil

import git

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
    repo = git.Repo("../6.2.7-stage/")
    if not repo.bare:
        print("Repository already exists.")
except git.exc.InvalidGitRepositoryError:
    # Clone the repository
    repo = git.Repo.clone_from(repo_url, branch_name)

    # Add two remote repositories
    lkml_url = (
        "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
    )
    drmtip_url = "https://anongit.freedesktop.org/git/drm-tip.git"

    lkml = repo.create_remote("lkml", lkml_url)
    drmtip = repo.create_remote("drmtip", drmtip_url)

    print("Repository cloned.")

"""
#change directory to the local Git repository
git_dir = "../6.0.2-stage"
repo = git.Repo(git_dir)
# define the branch name to checkout
branch_name = "6.2.7-stage"

# fetch and merge the latest changes from the remote branch
remote = repo.remotes.origin
remote.fetch()
remote.pull(branch_name)

# checkout to the branch
repo.git.checkout(branch_name)

repo = git.Repo("../6.0.2-stage/")
"""
# Fetch and initialize lkml and drmtip refs
repo.remotes["lkml"].fetch(refspec="master")
# repo.remotes["lkml"].update_tracking_branch()
repo.remotes["drmtip"].fetch(refspec="drm-tip")
# repo.remotes["drmtip"].update_tracking_branch()
# print("Done")

a = 0
b = 0
c = 0
d = 0
path = "drivers/gpu/drm/i915/"
# Loop through all commits in the branch and search for the message
for commit in repo.iter_commits(paths=path):
    commit_message = commit.message.splitlines()[0]
    if commit_message.startswith("INTERNAL"):
        message = commit_message.split(":", maxsplit=1)[1].strip()
        if message.startswith("BACKPORT"):
            message = message.split(":", maxsplit=1)[1].strip()
        if message.startswith("INTEL_DII"):
            message = message.split(":", maxsplit=1)[1].strip()
        # print(message)
        # message = "'"+message+"'"
        # Search for the message in lkml
        stage_commit = repo.git.log(
            "-F", "--grep", message, "--pretty=oneline", "origin/6.2.7-stage", "-1"
        )
        print("'" + message + "'")
        if stage_commit:
            f_out(f"In_6.2.7: {stage_commit.strip()} \n")
            a += 1
            continue
        lkml_commit = repo.git.log(
            "-F", "--grep", message, "--pretty=oneline", "lkml/master", "-1"
        )
        print("'" + message + "'")
        if lkml_commit:
            f_out(f"UPSTREAM: {lkml_commit.strip()} \n")
            b += 1
        else:
            # Search for the message in drmtip
            drmtip_commit = repo.git.log(
                "-F", "--grep", message, "--pretty=oneline", "drmtip/drm-tip", "-1"
            )
            print("'" + message + "'")
            if drmtip_commit:
                f_out(f"MAINT_GIT: {drmtip_commit.strip()} \n")
                c += 1
            else:
                f_out(f"NOT_OPENSOURCED: {commit} {commit_message} \n")
                d += 1


import pandas as pd

# open the text file and read its contents
with open("../patchstatus.txt", "r") as f:
    lines = f.readlines()

# create a list of dictionaries for each line of data
data = []
for line in lines:
    line = line.strip()
    status, commit_id, commit_msg = line.split(" ", 2)
    data.append(
        {"Status": status, "Commit ID": commit_id, "Commit Message": commit_msg}
    )

# create a Pandas DataFrame from the data
df = pd.DataFrame(data)

# reorder the columns to match the desired format
df = df[["Status", "Commit ID", "Commit Message"]]

# create an Excel writer object
writer = pd.ExcelWriter(
    "../patchstatus.xlsx", engine="xlsxwriter"
)

# write the DataFrame to the Excel sheet
df.to_csv("/var/www/html/patchstatus/patch.csv")
df.to_excel(writer, sheet_name="Commit Data", index=False)

# format the columns in the Excel sheet
workbook = writer.book
worksheet = writer.sheets["Commit Data"]
format1 = workbook.add_format({"text_wrap": True, "valign": "top"})
worksheet.set_column("A:A", 15, format1)
worksheet.set_column("B:B", 15, format1)
worksheet.set_column("C:C", 50, format1)

# save the Excel file
writer.save()


# read the Excel file into a Pandas DataFrame
df = pd.read_excel("../patchstatus.xlsx")

# set the background color for each row based on the 'Status' column
color_dict = {
    "UPSTREAM": "background-color: green;",
    "MAINT_GIT": "background-color: yellow;",
    "NOT_OPENSOURCED": "background-color: red;",
    "In_6.2.7": "background-color: blue;",
}
df = (
    df.style.applymap(
        lambda x: color_dict[x.rstrip(":")] if x.rstrip(":") in color_dict else "",
        subset=["Status"],
    )
    .set_properties(subset=["Status"], **{"text-align": "center"})
    .set_table_attributes('border="1" cellspacing="0" cellpadding="5"')
    .set_table_styles(
        [
            {
                "selector": "thead tr th",
                "props": [("background-color", "grey"), ("text-align", "center")],
            }
        ]
    )
)

# write the HTML string to a file
with open("../patchstatus.html", "w") as f:
    f.write(df.render())

import datetime
import os

# directory containing the HTML files
html_dir = ".."

# loop through each HTML file in the directory
for filename in os.listdir(html_dir):
    if filename.endswith(".html"):
        # open the file for reading and writing
        with open(os.path.join(html_dir, filename), "r+") as f:
            # read the contents of the file
            content = f.read()

            # get the date of generation
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

            # add the header with the date of generation and index values
            header = f"<h1>Generated on: {date_str} \n  In_6.2.7: {a} | UPSTREAM: {b} |  MAINT_GIT: {c} | NOT_OPENSOURCED: {d}</h1>"
            new_content = header + content

            # move the file pointer to the beginning of the file
            f.seek(0)

            # write the new content to the file
            f.write(new_content)

            # truncate the file to the new size
            f.truncate()


# Specify the path of the text file and the destination directory
file_path = "../patchstatus.txt"
dest_dir = "/var/www/html/patchstatus/"

# Use the shutil.copy() function to copy the file
shutil.copy(file_path, dest_dir)


# Use os.remove() function to delete the original file
os.remove(file_path)


# Specify the path of the xl file and the destination directory
file_path = "../patchstatus.xlsx"
dest_dir = "/var/www/html/patchstatus/"

# Use the shutil.copy() function to copy the file
shutil.copy(file_path, dest_dir)


# Use os.remove() function to delete the original file
os.remove(file_path)

# Specify the path of the html file and the destination directory
file_path = "../patchstatus.html"
dest_dir = "/var/www/html/patchstatus/"

# Use the shutil.copy() function to copy the file
shutil.copy(file_path, dest_dir)


# Use os.remove() function to delete the original file
os.remove(file_path)
