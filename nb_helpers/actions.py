# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_actions.ipynb.

# %% auto 0
__all__ = ['get_colab_url2md', 'create_comment_body', 'get_api', 'upload_modified_nbs', 'open_zip', 'upload_at', 'download',
           'post_colab_links', 'update_comment', 'create_issue_nb_fail']

# %% ../nbs/03_actions.ipynb 3
import json
from fastcore.all import *
from ghapi.all import *

from .utils import git_main_name, is_nb, git_origin_repo, git_local_repo

# %% ../nbs/03_actions.ipynb 5
def get_colab_url2md(fname: Path, branch="main", github_repo="nb_helpers", as_badge=False) -> str:
    "Create colab links in md"
    colab_url = f"https://colab.research.google.com/github/{github_repo}/blob/{branch}/{str(fname)}"
    if not as_badge:
        return f"[{fname}]({colab_url})"
    return f"[![badge](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url})"

# %% ../nbs/03_actions.ipynb 10
def create_comment_body(title, nb_files, branch, github_repo) -> str:
    "Creates a MD list of fnames with links to colab"
    colab_links = tuple(get_colab_url2md(f, branch, github_repo) for f in nb_files)
    body = tuplify(title) + colab_links
    return "\n -".join(body)

# %% ../nbs/03_actions.ipynb 12
def get_api(owner="wandb", repo="nb_helpers", token=None):
    api = GhApi(owner=owner, repo=repo, token=ifnone(token, github_token()))
    payload = context_github.event
    return api, payload

# %% ../nbs/03_actions.ipynb 14
def upload_modified_nbs(owner="wandb", repo="nb_helpers", token=None):
    "On PR post a comment with links to open in colab for each changed nb"
    api, payload = get_api(owner, repo, token)

    if "workflow" in payload:
        issue = 1
    else:
        issue = payload.number
    pr = payload.pull_request
    github_repo = pr.head.repo.full_name
    branch = pr.head.ref
    pr_files = [Path(f.filename) for f in api.pulls.list_files(issue)]
    print(f"pr_files: {pr_files}")

    # filter nbs
    nb_files = [f for f in pr_files if is_nb(f)]

    title = "The following colabs were changed"

    def _get_comment_id(issue):
        comments = api.issues.list_comments(issue)
        candidates = [c for c in comments if title in c.body]
        if len(candidates) == 1:
            comment_id = candidates[0].id
        else:
            comment_id = -1
        return comment_id

    if len(nb_files) > 0:
        body = create_comment_body(title, nb_files, branch, github_repo)
        comment_id = _get_comment_id(issue)
        json.dump( {"pr":issue, 
                    "comment_id":comment_id, 
                    "body": body}, open("modified_colabs.json", 'w' ))

# %% ../nbs/03_actions.ipynb 17
def open_zip(zf, file="reply.json"):
    from zipfile import ZipFile
    from io import BytesIO

    zip_file = ZipFile(BytesIO(zf))
    f = zip_file.open(file)
    return f

def upload_at(owner="wandb", repo="nb_helpers", token=None):
    api, payload = get_api(owner, repo, token)
    print("Uploading file to artifact\n=============")
    json.dump( {0: "My dummy issue reply"}, open("reply.json", 'w' ))
    
def download(owner="wandb", repo="nb_helpers", token=None):
    api, payload = get_api(owner, repo, token)
    print("HERE IS THE PAYLOAD\n=============")
    print(payload)
    print("=============\n\n")
    at = api.actions.list_workflow_run_artifacts(payload.workflow_run.id)["artifacts"][0]
    print("HERE IS THE Artifact\n=============")
    print(at)
    print("=============\n\n")
    at_id = at["id"]
    print("=============\n\n")
    print(f"Downloading AT {at_id}\n")
    zf = api.actions.download_artifact(at_id, "zip")
    print(f"Extracting reply.json\n")
    unzipped_file = open_zip(zf)
    print(unzipped_file, type(unzipped_file))
    print("Finished")

# %% ../nbs/03_actions.ipynb 19
def post_colab_links(owner="wandb", repo="nb_helpers", token=None):
    "Get artifact with text and create comment"
    api, payload = get_api(owner, repo, token)
    print("HERE IS THE PAYLOAD\n=============")
    print(payload)
    print("=============\n\n")
    at = api.actions.list_workflow_run_artifacts(payload.workflow_run.id)["artifacts"][0]
    print("HERE IS THE Artifact\n=============")
    print(at)
    print("=============\n\n")
    at_id = at["id"]
    print("=============\n\n")
    print(f"Downloading AT {at_id}\n")
    zf = api.actions.download_artifact(at_id, "zip")
    print(f"Extracting reply.json\n")
    f = open_zip(zf)
    message = json.loads(f.readline())
    pr, comment_id, body = message["pr"], message["comment_id"], message["body"]
    if comment_id > 0:
        print(f">> Updating comment on PR #{issue}\n{body}\n")
        api.issues.update_comment(comment_id, body)
    else:
        print(f">> Creating comment on PR #{issue}\n{body}\n")
        api.issues.create_comment(issue_number=issue, body=body)

# %% ../nbs/03_actions.ipynb 21
def update_comment(issue, body, comment_id, owner="wandb", repo="nb_helpers", token=None):
    api, payload = get_api(owner, repo, token)
    
    if "workflow" in payload:
        issue = 1
    else:
        issue = payload.number
        
    if comment_id > 0:
        print(f">> Updating comment on PR #{issue}\n{body}\n")
        api.issues.update_comment(comment_id, body)
    else:
        print(f">> Creating comment on PR #{issue}\n{body}\n")
        api.issues.create_comment(issue_number=issue, body=body)

# %% ../nbs/03_actions.ipynb 22
def create_issue_nb_fail(fname, traceback=None, owner="wandb", repo="nb_helpers", token=None):
    "Creates issue of failing nb"
    print("="*75)
    api, _ = get_api(owner, repo, token)
    fname = fname.resolve()
    github_repo = git_origin_repo(fname)
    title = f"Failed to run {fname}"
    branch = git_main_name(fname)
    fname = fname.relative_to(git_local_repo(fname))
    repo_url = f"[{str(fname)}](https://github.com/{github_repo}/blob/{branch}/{str(fname)})"
    colab_url = get_colab_url2md(fname, branch, github_repo, as_badge=True)
    traceback = ifnone(traceback, "")
    body = (
        "The following notebooks failed to run:\n\n"
        "|notebook name|               |\n"
        "|-------------|---------------|\n"
        f"| {repo_url}   | {colab_url} |\n\n"
        "------------------------------\n"
        "The recovered traceback is:\n\n"
        "```python\n"
        f"{traceback}\n"
        "```"
    )
    api.issues.create(title=title, body=body, labels=["bug"])
