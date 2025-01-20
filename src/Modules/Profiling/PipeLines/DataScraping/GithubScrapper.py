import requests
import json
from datetime import datetime, timedelta


class GitHubDataFetcher:
    def __init__(self, token):
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'

    def get_user_stats(self, identifier):
        """Fetch formatted user statistics by username or email"""
        # Try to get user by email first if identifier contains '@'
        if '@' in identifier:
            user_info = self._search_user_by_email(identifier)
            if not user_info:
                raise Exception(f"No user found with email: {identifier}")
        else:
            user_info = self._get_user_info(identifier)

        username = user_info['login']
        user_repos = self._get_user_repos(username)
        contributions = self._get_yearly_contributions(username)

        # Calculate total stars
        total_stars = sum(repo['stargazers_count'] for repo in user_repos)

        # Calculate user rating
        rating = self._calculate_user_rating(user_info, total_stars, contributions)

        # Format user stats
        user_stats = {
            "user_info": {
                "username": user_info['login'],
                "name": user_info['name'],
                "email": user_info.get('email', 'Not public'),
                "bio": user_info['bio'],
                "followers": user_info['followers'],
                "following": user_info['following'],
                "public_repos": user_info['public_repos'],
                "total_stars_earned": total_stars,
                "contributions_last_year": contributions,
                "rating": rating
            },
            "repositories": []
        }

        # Get detailed repo information
        for repo in user_repos:
            languages = self._get_repo_languages(username, repo['name'])
            repo_info = {
                "name": repo['name'],
                "description": repo['description'],
                "stars": repo['stargazers_count'],
                "forks": repo['forks_count'],
                "languages": languages,
                "created_at": repo['created_at'],
                "last_updated": repo['updated_at'],
                "size": repo['size']
            }
            user_stats["repositories"].append(repo_info)

        return user_stats

    def _search_user_by_email(self, email):
        """Search for a user by email"""
        url = f'{self.base_url}/search/users?q={email}+in:email'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to search user by email: {response.json()}")

        results = response.json()
        if results['total_count'] == 0:
            return None

        # Get detailed user info for the first match
        return self._get_user_info(results['items'][0]['login'])

    def _get_yearly_contributions(self, username):
        """Get user's contributions for the last year"""
        # Note: This is a simplified version as the actual contributions
        # would require scraping the contributions graph or using GraphQL API
        url = f'{self.base_url}/users/{username}/events'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user events: {response.json()}")

        # Count events from the last year
        events = response.json()
        one_year_ago = datetime.now() - timedelta(days=365)
        contribution_count = sum(1 for event in events
                                 if datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') > one_year_ago)

        return contribution_count

    def _calculate_user_rating(self, user_info, total_stars, contributions):
        """Calculate user rating based on various metrics"""
        # Point system:
        # - 1 point per follower
        # - 2 points per public repo
        # - 5 points per 100 contributions
        # - 10 points per star
        score = (
                user_info['followers'] +
                (user_info['public_repos'] * 2) +
                (contributions // 100 * 5) +
                (total_stars * 10)
        )

        # Rating scale
        if score >= 1000:
            return "A+"
        elif score >= 750:
            return "A"
        elif score >= 500:
            return "A-"
        elif score >= 400:
            return "B+"
        elif score >= 300:
            return "B"
        elif score >= 200:
            return "B-"
        elif score >= 100:
            return "C+"
        elif score >= 50:
            return "C"
        else:
            return "C-"

    def _get_user_info(self, username):
        """Internal method to fetch user info"""
        url = f'{self.base_url}/users/{username}'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user info: {response.json()}")
        return response.json()

    def _get_user_repos(self, username):
        """Internal method to fetch user repos"""
        url = f'{self.base_url}/users/{username}/repos'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repos: {response.json()}")
        return response.json()

    def _get_repo_languages(self, owner, repo):
        """Internal method to fetch repo languages"""
        url = f'{self.base_url}/repos/{owner}/{repo}/languages'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch languages: {response.json()}")
        return response.json()

    def save_stats(self, stats, filename):
        """Save stats to a JSON file with nice formatting"""
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)


# def main():
#     # Replace with your token
#     token = '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'
#     github = GitHubDataFetcher(token)
#
#     try:
#         # Can now search by username or email
#         identifier = "kudzaiprichard"  # or "example@email.com"
#         stats = github.get_user_stats(identifier)
#
#         # Print formatted JSON to console
#         print(json.dumps(stats, indent=2, ensure_ascii=False))
#
#         # Save to file
#         github.save_stats(stats, f'{stats["user_info"]["username"]}_github_stats.json')
#
#     except Exception as e:
#         print(f"Error: {str(e)}")
#
#
# if __name__ == "__main__":
#     main()