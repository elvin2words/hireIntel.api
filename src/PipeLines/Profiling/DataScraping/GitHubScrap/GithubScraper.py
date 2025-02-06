import re

import requests
import json
from datetime import datetime, timedelta


class GitHubScraper:
    def __init__(self, token = "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"):
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'


    def get_user_stats(self, identifier):
        """Fetch comprehensive user statistics by username"""
        print("fetching user info for by username:  '{}'".format(identifier))
        user_info = self._get_user_info(identifier)
        username = user_info['login']
        user_repos = self._get_user_repos(username)
        contributions = self._get_yearly_contributions(username)
        total_stars = sum(repo['stargazers_count'] for repo in user_repos)
        rating = self._calculate_user_rating(user_info, total_stars, contributions)
        print("User info fetched successfully. Processing user github stats:")
        # Comprehensive user profile and stats
        profile_data = {
            'basic_info': {
                'username': user_info['login'],
                'name': user_info['name'],
                'bio': user_info['bio'],
                'company': user_info['company'],
                'location': user_info['location'],
                'email': user_info.get('email', 'Not public'),
                'blog': user_info['blog'],
                'twitter_username': user_info.get('twitter_username'),
                'avatar_url': user_info['avatar_url']
            },
            'stats': {
                'public_repos': user_info['public_repos'],
                'public_gists': user_info['public_gists'],
                'followers': user_info['followers'],
                'following': user_info['following'],
                'total_stars_earned': total_stars,
                'contributions_last_year': contributions,
                'rating': rating
            },
            'dates': {
                'created_at': user_info['created_at'],
                'updated_at': user_info['updated_at']
            },
            'urls': {
                'github_url': user_info['html_url'],
                'repos_url': user_info['repos_url'],
                'gists_url': user_info['gists_url'].split('{')[0],
                'starred_url': user_info['starred_url'].split('{')[0],
                'followers_url': user_info['followers_url'],
                'following_url': user_info['following_url'].split('{')[0]
            },
            'additional_info': {
                'hireable': user_info['hireable'],
                'type': user_info['type'],
                'is_site_admin': user_info['site_admin']
            },
            'repositories': []
        }

        # Get detailed repository information
        for repo in user_repos:
            languages = self._get_repo_languages(username, repo['name'])
            commits = self._get_repo_commits(username, repo['name'])
            contributors = self._get_repo_contributors(username, repo['name'])
            repo_info = {
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo['description'],
                'homepage': repo['homepage'],
                'language': repo['language'],
                'languages_breakdown': languages,
                'stats': {
                    'stars': repo['stargazers_count'],
                    'watchers': repo['watchers_count'],
                    'forks': repo['forks_count'],
                    'open_issues': repo['open_issues_count'],
                    'size': repo['size'],
                    'commit_count': len(commits),
                    'contributor_count': len(contributors)
                },
                'dates': {
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'pushed_at': repo['pushed_at']
                },
                'urls': {
                    'html_url': repo['html_url'],
                    'clone_url': repo['clone_url'],
                    'ssh_url': repo['ssh_url'],
                    'api_url': repo['url']
                },
                'features': {
                    'has_wiki': repo['has_wiki'],
                    'has_pages': repo['has_pages'],
                    'has_projects': repo['has_projects'],
                    'has_downloads': repo['has_downloads'],
                    'archived': repo['archived'],
                    'disabled': repo['disabled'],
                    'private': repo['private'],
                    'fork': repo['fork']
                },
                'branch': {
                    'default_branch': repo['default_branch']
                },
                'license': repo['license'].get('name') if repo['license'] else None,
                'latest_commits': self._get_latest_commits(username, repo['name']),
                'top_contributors': self._get_top_contributors(contributors)
            }
            profile_data['repositories'].append(repo_info)
            print("Finished fetching repo info for '{}'".format(repo['name']))
        return profile_data

    def _search_user_by_email(self, email):
        """Search for a user by email"""
        url = f'{self.base_url}/search/users?q={email}+in:email'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to search user by email: {response.json()}")

        results = response.json()
        if results['total_count'] == 0:
            return None

        return self._get_user_info(results['items'][0]['login'])

    def _get_yearly_contributions(self, username):
        """Get user's contributions for the last year"""
        url = f'{self.base_url}/users/{username}/events'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user events: {response.json()}")

        events = response.json()
        one_year_ago = datetime.now() - timedelta(days=365)
        contribution_count = sum(1 for event in events
                                 if datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ') > one_year_ago)

        return contribution_count

    def _calculate_user_rating(self, user_info, total_stars, contributions):
        """Calculate user rating based on various metrics"""
        score = (
                user_info['followers'] +
                (user_info['public_repos'] * 2) +
                (contributions // 100 * 5) +
                (total_stars * 10)
        )

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
        """Fetch user info"""
        url = f'{self.base_url}/users/{username}'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user info: {response.json()}")
        return response.json()

    def _get_user_repos(self, username):
        """Fetch user repositories"""
        url = f'{self.base_url}/users/{username}/repos'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repos: {response.json()}")
        return response.json()

    def _get_repo_languages(self, owner, repo):
        """Fetch repository languages"""
        url = f'{self.base_url}/repos/{owner}/{repo}/languages'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch languages: {response.json()}")
        return response.json()

    def _get_repo_commits(self, owner, repo):
        """Fetch repository commits"""
        url = f'{self.base_url}/repos/{owner}/{repo}/commits'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            return []
        return response.json()

    def _get_repo_contributors(self, owner, repo):
        """Fetch repository contributors"""
        url = f'{self.base_url}/repos/{owner}/{repo}/contributors'
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            return []
        return response.json()

    def _get_latest_commits(self, owner, repo, limit=5):
        """Fetch latest commits for a repository"""
        commits = self._get_repo_commits(owner, repo)
        latest = []
        for commit in commits[:limit]:
            latest.append({
                'sha': commit['sha'],
                'message': commit['commit']['message'],
                'author': commit['commit']['author']['name'],
                'date': commit['commit']['author']['date']
            })
        return latest

    def _get_top_contributors(self, contributors, limit=5):
        """Get top contributors based on contributions"""
        top = sorted(contributors, key=lambda x: x['contributions'], reverse=True)[:limit]
        return [{
            'username': contributor['login'],
            'contributions': contributor['contributions'],
            'avatar_url': contributor['avatar_url'],
            'profile_url': contributor['html_url']
        } for contributor in top]

    def save_stats(self, stats, filename):
        """Save stats to a JSON file with nice formatting"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)