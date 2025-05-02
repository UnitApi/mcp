#!/usr/bin/env python3
import os
import subprocess
import requests
import json

def find_git_projects(root):
    projects = []
    for org in os.listdir(root):
        org_path = os.path.join(root, org)
        if not os.path.isdir(org_path):
            continue
        for repo in os.listdir(org_path):
            repo_path = os.path.join(org_path, repo)
            git_dir = os.path.join(repo_path, '.git')
            if os.path.isdir(git_dir):
                projects.append((org, repo, repo_path))
    return projects

def get_git_status(repo_path):
    try:
        status = subprocess.check_output(['git', '-C', repo_path, 'status', '-sb'], stderr=subprocess.STDOUT, text=True)
        return status.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output.strip()}"

def get_git_diff_with_remote(repo_path):
    try:
        subprocess.check_output(['git', '-C', repo_path, 'fetch'], stderr=subprocess.STDOUT)
        diff = subprocess.check_output(['git', '-C', repo_path, 'diff', 'origin/HEAD'], stderr=subprocess.STDOUT, text=True)
        return diff.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output.strip()}"

def get_remote_url(repo_path):
    try:
        url = subprocess.check_output(['git', '-C', repo_path, 'config', '--get', 'remote.origin.url'], stderr=subprocess.STDOUT, text=True)
        return url.strip()
    except subprocess.CalledProcessError:
        return None

def check_remote_exists(url):
    if url is None:
        return False, None
    # Handle only github and gitlab
    if url.startswith('git@'):
        url = url.replace(':', '/').replace('git@', 'https://').replace('.git', '')
    elif url.startswith('https://'):
        url = url.replace('.git', '')
    if 'github.com' in url:
        api = url.replace('https://github.com/', 'https://api.github.com/repos/')
        resp = requests.get(api)
        return resp.status_code == 200, 'github'
    if 'gitlab.com' in url:
        parts = url.split('gitlab.com/')
        if len(parts) == 2:
            api = 'https://gitlab.com/api/v4/projects/' + requests.utils.quote(parts[1], safe='')
            resp = requests.get(api)
            return resp.status_code == 200, 'gitlab'
    return False, None

def compare_local_projects(projects):
    name_to_paths = {}
    hash_to_paths = {}
    for org, repo, path in projects:
        name_to_paths.setdefault(repo, []).append(path)
        # Compute a quick hash of all files in the repo (excluding .git)
        sha = subprocess.check_output(f"find '{path}' -type f -not -path '*/.git/*' -exec sha1sum {{}} + | sort | sha1sum", shell=True, text=True).split()[0]
        hash_to_paths.setdefault(sha, []).append(path)
    return name_to_paths, hash_to_paths

def main():
    root = input("Enter root path to search for git projects (org/repo): ").strip()
    projects = find_git_projects(root)
    print(f"Found {len(projects)} git projects.")
    # Limit to first 10 for testing
    projects = projects[:10]
    name_to_paths, hash_to_paths = compare_local_projects(projects)
    with open('git_equal.txt', 'w') as equal_file, open('git_missing_remote.txt', 'w') as missing_file:
        for org, repo, path in projects:
            print(f"\n=== {org}/{repo} ===")
            url = get_remote_url(path)
            print(f"Remote: {url}")
            exists, remote_type = check_remote_exists(url)
            if not exists:
                print(f"Remote repository does NOT exist on {remote_type or 'unknown service'}!")
                missing_file.write(f"{path}\n")
                # Check for local duplicates by name
                print("Checking for local projects with the same name:")
                for p in name_to_paths.get(repo, []):
                    if p != path:
                        print(f"  Duplicate name: {p}")
                # Check for local duplicates by content
                for sha, paths in hash_to_paths.items():
                    if path in paths and len(paths) > 1:
                        print(f"  Duplicate content: {paths}")
            else:
                status = get_git_status(path)
                print(f"Status:\n{status}")
                diff = get_git_diff_with_remote(path)
                if diff:
                    print("Diff with origin/HEAD:")
                    print(diff if len(diff) < 1000 else diff[:1000]+'...')
                else:
                    print("No diff with remote.")
                    equal_file.write(f"{org}/{repo} : {path}\n")

if __name__ == "__main__":
    main()
