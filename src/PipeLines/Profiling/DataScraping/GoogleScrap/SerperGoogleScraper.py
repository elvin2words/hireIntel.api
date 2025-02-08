import requests
import time
from dataclasses import dataclass, field
from typing import Optional, List, Set
from urllib.parse import urlparse

from src.Helpers.HandleProfileVerification import HandleProfileVerification
from src.Modules.Candidate.CandidateModels import Candidate
from src.Modules.PipeLineData.TextExtractionData.TextExtractionService import TextExtractionDataService
from src.PipeLines.Profiling.DataScraping.GitHubScrap.GithubScraper import GitHubScraper
from src.PipeLines.Profiling.DataScraping.LinkedInScrap.RapidLinkedInScrapper import RapidLinkedInAPIClient


@dataclass
class GithubHandle:
    verified: bool = False
    github_username: Optional[str] = None
    github_url: Optional[str] = None

    def __str__(self):
        if self.verified:
            return f"Username: {self.github_username}, URL: {self.github_url}"
        return "No verified GitHub profile found"

@dataclass
class LinkedInHandle:
    verified: bool = False
    linkedin_username: Optional[str] = None
    linkedin_url: Optional[str] = None

    def __str__(self):
        if self.verified:
            return f"Username: {self.linkedin_username}, URL: {self.linkedin_url}"
        return "No verified LinkedIn profile found"

@dataclass
class Profile:
    fullName: str
    githubHandle: GithubHandle = field(default_factory=GithubHandle)
    linkedInHandle: LinkedInHandle = field(default_factory=LinkedInHandle)

    def __str__(self):
        return f"""
Profile for: {self.fullName}
LinkedIn: {self.linkedInHandle}
GitHub: {self.githubHandle}
"""

class ProfileScraper:
    """Scraper class specifically optimized for finding GitHub and LinkedIn profiles"""

    def __init__(self, githubToken, serperToken, serperBaseUrl, rapid_api_key):
        self.api_key = serperToken
        self.serperBaseUrl = serperBaseUrl
        self.verifier = HandleProfileVerification(gitHubToken=githubToken,rapidApiKey=rapid_api_key)
        self.githubScraper = GitHubScraper(githubToken)
        self.linkedInScraper = RapidLinkedInAPIClient(rapid_api_key)
        self.textExtractionDataService = TextExtractionDataService()
        self.search_delay = 1
        self.max_results = 10

    def _generate_profile_queries(self, name: str) -> List[str]:
        """Generate search queries specifically for finding professional profiles"""
        name_parts = name.split()

        # Create base variations focused on professional profiles
        variations = [
            f'"{name}"',  # Exact name match
            name,  # Regular name
        ]

        # If we have a multi-part name, add a variation without middle names/initials
        if len(name_parts) > 2:
            variations.append(f'{name_parts[0]} {name_parts[-1]}')

        return variations

    def _make_search_request(self, query: str, site: str) -> List[str]:
        """Make a search request using Serper API with profile-specific queries"""
        base_url = self.serperBaseUrl

        # Define profile-specific search patterns
        profile_patterns = {
            "linkedin.com/in": {
                "prefix": "linkedin.com/in/",
                "keywords": [""],  # Empty string to search without additional keywords
            },
            "github.com": {
                "prefix": "github.com/",
                "keywords": [""],  # Empty string to search without additional keywords
            }
        }

        all_urls = set()
        site_config = profile_patterns.get(site, {})

        # Generate search variations
        search_variations = self._generate_profile_queries(query)

        for variation in search_variations:
            # Build a profile-specific search query
            search_query = f"{variation} {site_config.get('prefix', '')}"

            payload = {
                "q": f"{search_query}",
                "num": self.max_results
            }
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if 'organic' in data:
                    for result in data['organic']:
                        if 'link' in result:
                            url = result['link']
                            # Only add URLs that match our profile patterns
                            if site in url.lower() and (
                                    ('/in/' in url.lower() if site == 'linkedin.com/in' else True) or
                                    (parsed_url := urlparse(url)).netloc.lower() == 'github.com'
                            ):
                                all_urls.add(url)

                time.sleep(self.search_delay)

            except requests.exceptions.RequestException as e:
                print(f"Search request failed for query '{search_query}': {e}")
                continue

        return list(all_urls)[:self.max_results]

    def _find_linkedin_profile(self, candidate: Candidate) -> LinkedInHandle:
        """Find LinkedIn profile for a given name"""
        full_name = candidate.first_name + " " + candidate.last_name
        resume = self.textExtractionDataService.get_resume_by_candidate_id(candidate.id)

        linkedInUrl = resume["personalInformation"]["linkedinUrl"]
        linkedInHandle = resume["personalInformation"]["linkedinHandle"]

        if linkedInUrl and linkedInHandle:
            print("Found the linkedin url in the resume :", linkedInUrl)
            print(f"{linkedInHandle} linkedin usernames found")
            return LinkedInHandle(
                verified=True,
                linkedin_username=linkedInHandle,
                linkedin_url=linkedInUrl
            )

        # Get LinkedIn URLs
        linkedin_urls = self._make_search_request(full_name, "linkedin.com/in")
        if not linkedin_urls:
            print("No LinkedIn URLs found")
            return LinkedInHandle()

        print(f"Found {len(linkedin_urls)} LinkedIn URLs")
        time.sleep(self.search_delay)

        # Extract and verify usernames
        usernames = self._extract_linkedin_usernames(linkedin_urls)
        print(f"Extracted {len(usernames)} unique LinkedIn usernames")

        # Find first verified username
        for username in usernames:
            print(f"Verifying LinkedIn username: {username}")
            linkedin_scrap = self.linkedInScraper.get_profile(username)
            print(f"processing: {linkedin_scrap}")
            res = self.verifier.verify_profile(
                scraped_data=linkedin_scrap,
                candidate_id=candidate.id,
                profile_type="LinkedIn"
            )

            if not res or len(res) < 0: return LinkedInHandle()

            if res["is_match"]:
                matching_url = next((url for url in linkedin_urls if f'/in/{username}' in url.lower()), None)
                return LinkedInHandle(
                    verified=True,
                    linkedin_username=username,
                    linkedin_url=matching_url
                )

        print("No verified LinkedIn profiles found")
        return LinkedInHandle()

    def _find_github_profile(self, candidate: Candidate) -> GithubHandle:
        """Find GitHub profile for a given name"""
        full_name = candidate.first_name + " " + candidate.last_name
        resume = self.textExtractionDataService.get_resume_by_candidate_id(candidate.id)

        githubUrl = resume["personalInformation"]["githubUrl"]
        githubHandle = resume["personalInformation"]["githubHandle"]

        if githubUrl and githubHandle:
            print("Found the GitHub url in the resume:", githubUrl)
            print(f"{githubHandle} GitHub usernames found")
            return GithubHandle(
                verified=True,
                github_username=githubHandle,
                github_url=githubUrl
            )

        # Get GitHub URLs
        github_urls = self._make_search_request(full_name, "github.com")
        if not github_urls:
            print("No GitHub URLs found")
            return GithubHandle()

        print(f"Found {len(github_urls)} GitHub URLs")
        time.sleep(self.search_delay)

        # Extract and verify usernames
        usernames = self._extract_github_usernames(github_urls)
        print(f"Extracted {len(usernames)} unique GitHub usernames")

        # Find first verified username
        for username in usernames:
            print(f"Verifying GitHub username: {username}")

            try:
                print(f"Inside try verify GitHub username: {username}")
                git_scrap = self.githubScraper.get_user_stats(username)

                res = self.verifier.verify_profile(
                    scraped_data=git_scrap,
                    candidate_id=candidate.id,
                    profile_type="github")

                if not res or len(res) < 0: return GithubHandle()
                print(res["is_match"], type(res["is_match"]))
                if bool(res["is_match"]):
                    matching_url = next((url for url in github_urls if f'/{username}' in url.lower()), None)
                    print(f"Found {len(matching_url)} GitHub URLs")
                    print(f"username: {username}, url : {matching_url}")
                    return GithubHandle(
                        verified=True,
                        github_username=username,
                        github_url=matching_url
                    )

            except requests.exceptions.RequestException as e:
                print(f"Search request failed for username: {username}: {e}")

        print("No verified GitHub profiles found")
        return GithubHandle()

    def _extract_linkedin_usernames(self, urls: List[str]) -> Set[str]:
        """Extract usernames from LinkedIn profile URLs"""
        usernames = set()
        for url in urls:
            try:
                if '/in/' in url.lower():
                    # Extract username from LinkedIn profile URL
                    username = url.split('/in/')[-1].strip('/')
                    username = username.split('/')[0]  # Get first part of path
                    username = username.split('?')[0]  # Remove query parameters

                    # Only add if it looks like a valid LinkedIn username
                    if username and len(username) >= 3 and not username.startswith(('company', 'school')):
                        usernames.add(username)
            except Exception as e:
                print(f"Failed to extract LinkedIn username from {url}: {e}")
        return usernames

    def _extract_github_usernames(self, urls: List[str]) -> Set[str]:
        """Extract usernames from GitHub profile URLs"""
        usernames = set()
        excluded_paths = {'search', 'explore', 'topics', 'trending', 'marketplace', 'pulls', 'issues', 'notifications'}

        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.netloc.lower() == 'github.com':
                    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
                    if path_parts:
                        username = path_parts[0].lower()
                        # Only add if it looks like a valid GitHub profile
                        if (username and
                                username not in excluded_paths and
                                '.' not in username and  # Avoid repository URLs
                                len(path_parts) == 1):  # Ensure it's a profile URL, not a repo
                            usernames.add(username)
            except Exception as e:
                print(f"Failed to extract GitHub username from {url}: {e}")
        return usernames

    def find_profiles(self,candidate : Candidate) -> Profile:
        """Main method to find profiles for a given name"""
        name = candidate.first_name + " " + candidate.last_name
        print(f"\nStarting profile search for: {name}")

        # Create profile with name
        _profile = Profile(fullName=name)

        # Then find GitHub profile
        _profile.githubHandle = self._find_github_profile(candidate)

        # Find LinkedIn profile first
        _profile.linkedInHandle = self._find_linkedin_profile(candidate)

        print(f"inside profile is : {_profile}")
        return _profile

