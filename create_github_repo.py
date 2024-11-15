import requests
import os
import subprocess

def create_github_repo():
    headers = {
        'Authorization': f'token {os.environ["GITHUB_TOKEN"]}',
        'Accept': 'application/vnd.github.v3+json'
    }

    data = {
        'name': 'LeaseWise-Frontend',
        'description': 'Flask-based web application implementing a comprehensive onboarding system',
        'private': False
    }

    response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
    if response.status_code == 201:
        repo_url = response.json()['clone_url']
        auth_url = repo_url.replace('https://', f'https://x-access-token:{os.environ["GITHUB_TOKEN"]}@')
        
        # Set up git remote
        subprocess.run(['git', 'remote', 'remove', 'origin'], stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'remote', 'add', 'origin', auth_url])
        
        # Push to GitHub
        subprocess.run(['git', 'push', '-u', 'origin', 'main'])
        return True
    else:
        print(f"Error creating repository: {response.status_code}")
        return False

if __name__ == "__main__":
    create_github_repo()
