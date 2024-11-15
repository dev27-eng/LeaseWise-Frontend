import os
import requests
import subprocess
import json

def initialize_git():
    """Initialize git repository if not already initialized"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'init'], check=True)
        print("Git repository initialized")

def get_github_username(token):
    """Get the authenticated user's GitHub username"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get('https://api.github.com/user', headers=headers)
    if response.status_code == 200:
        return response.json()['login']
    return None

def create_github_repo():
    """Create GitHub repository and push code"""
    try:
        # Initialize git if needed
        initialize_git()

        # Configure git credentials
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("Error: GITHUB_TOKEN not found in environment")
            return False

        # Get GitHub username
        username = get_github_username(token)
        if not username:
            print("Error: Could not get GitHub username")
            return False

        print(f"Authenticated as GitHub user: {username}")

        # Create repository via GitHub API
        api_url = f'https://api.github.com/user/repos'
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        data = {
            'name': 'LeaseWise-Frontend',
            'description': 'Flask-based web application implementing a comprehensive onboarding system',
            'private': False,
            'has_issues': True,
            'has_projects': True,
            'has_wiki': True,
            'auto_init': False
        }

        # Try to create repository
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 201:
            print("Repository created successfully")
            repo_info = response.json()
        elif response.status_code == 422:  # Repository exists
            print("Repository already exists, fetching existing repository")
            response = requests.get(f'https://api.github.com/repos/{username}/LeaseWise-Frontend', headers=headers)
            if response.status_code != 200:
                print(f"Error fetching existing repository: {response.status_code}")
                return False
            repo_info = response.json()
        else:
            print(f"Error creating repository: {response.status_code}")
            print(f"Response: {response.json()}")
            return False

        # Configure remote using HTTPS URL with token
        repo_url = repo_info['clone_url'].replace('https://', f'https://{token}@')
        
        # Remove existing origin if it exists
        subprocess.run(['git', 'remote', 'remove', 'origin'], capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)

        # Configure git user for commit
        subprocess.run(['git', 'config', 'user.email', f"{username}@users.noreply.github.com"], check=True)
        subprocess.run(['git', 'config', 'user.name', username], check=True)

        # Stage all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Create initial commit if needed
        try:
            subprocess.run(['git', 'commit', '-m', "Initial commit: Setting up Flask application"], check=True)
        except subprocess.CalledProcessError:
            print("No changes to commit, continuing with push")

        # Push to GitHub with error handling
        try:
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            print("Code pushed successfully")
        except subprocess.CalledProcessError:
            try:
                # Try pushing to master if main fails
                subprocess.run(['git', 'push', '-u', 'origin', 'master'], check=True)
                print("Code pushed successfully to master branch")
            except subprocess.CalledProcessError as e:
                print(f"Error pushing to repository: {str(e)}")
                return False

        print("Repository setup completed successfully")
        return True

    except Exception as e:
        print(f"Error in create_github_repo: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_github_repo()
    exit(0 if success else 1)
