import os
import requests
import subprocess
import json
from typing import Optional, Tuple, Dict

def initialize_git() -> bool:
    """Initialize git repository if not already initialized"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], check=True, capture_output=True)
        print("Git repository already initialized")
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.run(['git', 'init'], check=True)
            print("Git repository initialized")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error initializing git repository: {str(e)}")
            return False

def get_github_username(token: str) -> Optional[str]:
    """Get the authenticated user's GitHub username"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        response.raise_for_status()
        return response.json().get('login')
    except requests.exceptions.RequestException as e:
        print(f"Error getting GitHub username: {str(e)}")
        return None

def handle_repository_creation(api_url: str, headers: Dict, data: Dict) -> Tuple[bool, Optional[Dict]]:
    """Handle repository creation with proper error handling"""
    try:
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 201:
            print("Repository created successfully")
            return True, response.json()
        elif response.status_code == 422:  # Repository exists
            print("Repository already exists, attempting to use existing repository")
            username = data.get('owner', {}).get('login')
            if not username:
                print("Error: Could not determine username for existing repository")
                return False, None
                
            existing_repo_url = f'https://api.github.com/repos/{username}/LeaseWise-Frontend'
            existing_response = requests.get(existing_repo_url, headers=headers)
            
            if existing_response.status_code == 200:
                print("Successfully retrieved existing repository information")
                return True, existing_response.json()
            else:
                print(f"Error accessing existing repository: {existing_response.status_code}")
                return False, None
        elif response.status_code == 403:
            print("Error: Insufficient permissions. Please ensure the token has the necessary scopes:")
            print("- repo (Full control of private repositories)")
            print("- workflow (Update GitHub Action workflows)")
            print("- admin:org (Full control of orgs and teams, recommended)")
            return False, None
        else:
            print(f"Error creating repository: {response.status_code}")
            print(f"Response: {response.json()}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error during repository creation: {str(e)}")
        return False, None

def create_github_repo() -> bool:
    """Create GitHub repository and push code"""
    try:
        # Initialize git if needed
        if not initialize_git():
            return False

        # Get and validate token
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("Error: GITHUB_TOKEN not found in environment")
            return False

        # Get GitHub username
        username = get_github_username(token)
        if not username:
            return False

        print(f"Authenticated as GitHub user: {username}")

        # Prepare repository creation request
        api_url = 'https://api.github.com/user/repos'
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        data = {
            'name': 'LeaseWise-Frontend',
            'description': 'Flask-based web application implementing a comprehensive onboarding system',
            'private': False,
            'has_issues': True,
            'has_projects': True,
            'has_wiki': True,
            'auto_init': False,
            'owner': {'login': username}
        }

        # Create or get repository
        success, repo_info = handle_repository_creation(api_url, headers, data)
        if not success or not repo_info:
            return False

        # Configure remote using token-based HTTPS URL
        repo_url = repo_info['clone_url'].replace('https://', f'https://{token}@')
        
        # Set up git remote
        try:
            subprocess.run(['git', 'remote', 'remove', 'origin'], capture_output=True)
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)
            print("Git remote configured successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error configuring git remote: {str(e)}")
            return False

        # Configure git user
        try:
            subprocess.run(['git', 'config', 'user.email', f"{username}@users.noreply.github.com"], check=True)
            subprocess.run(['git', 'config', 'user.name', username], check=True)
            print("Git user configured successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error configuring git user: {str(e)}")
            return False

        # Stage all files
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            print("Files staged successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error staging files: {str(e)}")
            return False
        
        # Create commit
        try:
            subprocess.run(['git', 'commit', '-m', "Initial commit: Setting up Flask application with VSCode configuration"], check=True)
            print("Changes committed successfully")
        except subprocess.CalledProcessError:
            print("No changes to commit, continuing with push")

        # Push to GitHub
        try:
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True)
            print("\nCode pushed successfully to main branch")
            print(f"\nRepository URL for VSCode cloning: {repo_info['clone_url']}")
            return True
        except subprocess.CalledProcessError:
            try:
                # Try pushing to master if main fails
                subprocess.run(['git', 'push', '-u', 'origin', 'master'], check=True)
                print("\nCode pushed successfully to master branch")
                print(f"\nRepository URL for VSCode cloning: {repo_info['clone_url']}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error pushing to repository: {str(e)}")
                return False

    except Exception as e:
        print(f"Unexpected error in create_github_repo: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_github_repo()
    exit(0 if success else 1)
