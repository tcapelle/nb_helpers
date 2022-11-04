# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_actions.ipynb.

# %% auto 0
__all__ = ['get_colab_url2md', 'create_comment_body', 'get_api', 'update_comment', 'after_pr_colab_link', 'create_issue_nb_fail']

# %% ../nbs/03_actions.ipynb 3
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

# %% ../nbs/03_actions.ipynb 15
def after_pr_colab_link(owner="wandb", repo="nb_helpers", token=None):
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

    title = "The following colabs where changed"

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
        with open("modified_colabs.txt", "w") as f:
            f.write(f"{comment_id}\n")
            f.write(body)

# %% ../nbs/03_actions.ipynb 16
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
