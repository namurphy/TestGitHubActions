import os
import sys
import requests

try:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    PR_NUMBER = os.getenv("PR_NUMBER")
    REPO = os.getenv("GITHUB_REPOSITORY")
except Exception as exc:
    raise RuntimeError("Unable to get environment variables")    

EXCLUDED_USERS = ('dependabot', 'pre-commit-ci', 'sourcery-ai')

def get_pr_authors():
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/commits"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    authors = set(commit['author']['login'] for commit in response.json() if commit['author'])
    return authors - set(EXCLUDED_USERS)

def check_citation_file(authors):
    with open('CITATION.cff', 'r') as file:
        contents = file.read()
        for author in authors:
            if f"alias: {author}" not in contents:
                return False, author
    return True, None

def post_comment(message):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.post(url, json={"body": message}, headers=headers)
    response.raise_for_status()

def main():
    authors = get_pr_authors()
    check_passed, failed_author = check_citation_file(authors)
    if not check_passed:
        branch_name = os.getenv("GITHUB_HEAD_REF")
        primary_author = list(authors)[0]
        message = f"To ensure that you get credit for your contribution to PlasmaPy, please add yourself as an author to [CITATION.cff](https://github.com/{REPO}/edit/{branch_name}/CITATION.cff). The entry should be of the form:\n```- given-names: <add given names>\n  family-names: <family names>\n  affiliation: <affiliation>\n  orcid: https://orcid.org/<ORCiD>\n  alias: {failed_author}```All fields except `alias` are optional.\n\n[Sign up for ORCiD](https://orcid.org/register)"
        post_comment(message)
        print(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
