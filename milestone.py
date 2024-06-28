
# import re
# import os
# import sys
# from github import Github, GithubException

# def get_github_token():
#     token = os.environ.get('GITHUB_TOKEN')
#     if not token:
#         raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
#     return token

# def verify_token(token):
#     try:
#         g = Github(token)
#         user = g.get_user()
#         print(f"Authenticated as: {user.login}")
#         return g
#     except GithubException as e:
#         raise ConnectionError(f"Error verifying token: {e}")

# def get_repo(g, repo_name):
#     try:
#         return g.get_repo(repo_name)
#     except GithubException as e:
#         raise ValueError(f"Error accessing repository: {e}")

# def get_milestones(repo):
#     try:
#         return repo.get_milestones(state='open')
#     except GithubException as e:
#         raise RuntimeError(f"Error fetching milestones: {e}")

# def get_pull_requests(repo):
#     try:
#         return repo.get_pulls(state='open')
#     except GithubException as e:
#         raise RuntimeError(f"Error fetching pull requests: {e}")

# def filter_milestones(milestones, patterns):
#     milestone_prs = {pattern: [] for pattern in patterns}
#     for milestone in milestones:
#         for pattern in patterns:
#             if re.match(pattern, milestone.title):
#                 milestone_prs[pattern].append(milestone)
#                 break  # Stop checking patterns for this milestone
#     return milestone_prs

# def filter_prs_by_milestones(prs, milestones):
#     result = {milestone.title: [] for milestone in milestones}
#     for pr in prs:
#         if pr.milestone and pr.milestone.title in result:
#             result[pr.milestone.title].append(pr)
#     return result

# def fetch_prs_for_patterns(repo, milestone_prs):
#     all_prs = get_pull_requests(repo)
#     result = {pattern: {} for pattern in milestone_prs}
#     for pattern, milestones in milestone_prs.items():
#         filtered_prs = filter_prs_by_milestones(all_prs, milestones)
#         for milestone_title, prs in filtered_prs.items():
#             result[pattern][milestone_title] = [
#                 {
#                     'number': pr.number,
#                     'title': pr.title,
#                     'url': pr.html_url,
#                     'user': pr.user.login,
#                     'created_at': pr.created_at
#                 }
#                 for pr in prs
#             ]
#     return result

# def display_results(milestone_prs):
#     for pattern, milestones in milestone_prs.items():
#         print(f"\nPRs for milestone pattern '{pattern}':")
#         if milestones:
#             for milestone, prs in milestones.items():
#                 print(f"  Milestone: {milestone}")
#                 if prs:
#                     for pr in prs:
#                         print(f"    - #{pr['number']}: {pr['title']}")
#                         print(f"      URL: {pr['url']}")
#                         print(f"      Created by: {pr['user']} on {pr['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
#                 else:
#                     print("    No PRs found")
#         else:
#             print("  No milestones found")

# def main():
#     repo_name = "KoBrane/jenkis-pytest"  # Replace with actual owner and repo name
#     milestone_patterns = [
#         r"Release/.* Approved",
#         r"CAB Approved"
#     ]
    
#     try:
#         token = get_github_token()
#         print(f"Token: {'*' * len(token)}")  # Print masked token for verification

#         g = verify_token(token)
        
#         repo = get_repo(g, repo_name)
        
#         milestones = get_milestones(repo)
        
#         milestone_prs = filter_milestones(milestones, milestone_patterns)
        
#         milestone_prs = fetch_prs_for_patterns(repo, milestone_prs)
        
#         display_results(milestone_prs)
        
#     except (ValueError, ConnectionError, RuntimeError) as e:
#         print(f"Error: {e}")
#         sys.exit(1)
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()

import re
import os
import sys
import subprocess

# Ensure the github module is installed
try:
    import github
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyGithub'])
    import github

from github import Github, GithubException

def get_github_token():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    return token

def verify_token(token):
    try:
        g = Github(token)
        user = g.get_user()
        print(f"Authenticated as: {user.login}")
        return g
    except GithubException as e:
        raise ConnectionError(f"Error verifying token: {e}")

def get_repo(g, repo_name):
    try:
        return g.get_repo(repo_name)
    except GithubException as e:
        raise ValueError(f"Error accessing repository: {e}")

def get_milestones(repo):
    try:
        return repo.get_milestones(state='open')
    except GithubException as e:
        raise RuntimeError(f"Error fetching milestones: {e}")

def get_pull_requests(repo):
    try:
        return repo.get_pulls(state='open')
    except GithubException as e:
        raise RuntimeError(f"Error fetching pull requests: {e}")

def filter_milestones(milestones, patterns):
    milestone_prs = {pattern: [] for pattern in patterns}
    for milestone in milestones:
        for pattern in patterns:
            if re.match(pattern, milestone.title):
                milestone_prs[pattern].append(milestone)
                break  # Stop checking patterns for this milestone
    return milestone_prs

def filter_prs_by_milestones(prs, milestones):
    result = {milestone.title: [] for milestone in milestones}
    for pr in prs:
        if pr.milestone and pr.milestone.title in result:
            result[pr.milestone.title].append(pr)
    return result

def fetch_prs_for_patterns(repo, milestone_prs):
    all_prs = get_pull_requests(repo)
    result = {pattern: {} for pattern in milestone_prs}
    for pattern, milestones in milestone_prs.items():
        filtered_prs = filter_prs_by_milestones(all_prs, milestones)
        for milestone_title, prs in filtered_prs.items():
            result[pattern][milestone_title] = [
                {
                    'number': pr.number,
                    'title': pr.title,
                    'url': pr.html_url,
                    'user': pr.user.login,
                    'created_at': pr.created_at
                }
                for pr in prs
            ]
    return result

def display_results(milestone_prs):
    for pattern, milestones in milestone_prs.items():
        print(f"\nPRs for milestone pattern '{pattern}':")
        if milestones:
            for milestone, prs in milestones.items():
                print(f"  Milestone: {milestone}")
                if prs:
                    for pr in prs:
                        print(f"    - #{pr['number']}: {pr['title']}")
                        print(f"      URL: {pr['url']}")
                        print(f"      Created by: {pr['user']} on {pr['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print("    No PRs found")
        else:
            print("  No milestones found")

def main():
    repo_name = "KoBrane/jenkis-pytest"  # Replace with actual owner and repo name
    milestone_patterns = [
        r"Release/.* Approved",
        r"CAB Approved"
    ]
    
    try:
        token = get_github_token()
        print(f"Token: {'*' * len(token)}")  # Print masked token for verification

        g = verify_token(token)
        
        repo = get_repo(g, repo_name)
        
        milestones = get_milestones(repo)
        
        milestone_prs = filter_milestones(milestones, milestone_patterns)
        
        milestone_prs = fetch_prs_for_patterns(repo, milestone_prs)
        
        display_results(milestone_prs)
        
    except (ValueError, ConnectionError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
