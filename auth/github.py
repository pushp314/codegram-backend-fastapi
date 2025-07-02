import os
from httpx_oauth.clients.github import GitHubOAuth2

# Use environment variables or paste your credentials here (not recommended)
GITHUB_CLIENT_ID = "Ov23liGyvkKJuwNoaHRs"
GITHUB_CLIENT_SECRET = "b8547e77b269a8f381721a130445592517759722"

github_oauth_client = GitHubOAuth2(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
)

def get_github_oauth_router(fastapi_users, auth_backend):
    return fastapi_users.get_oauth_router(
        github_oauth_client,
        auth_backend,
        "SECRET",  # Replace with a random string for state encryption
        redirect_url="http://localhost:8000/auth/github/callback",
    )