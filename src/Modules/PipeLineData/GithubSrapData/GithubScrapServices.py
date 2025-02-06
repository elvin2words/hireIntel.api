from datetime import datetime
from typing import Optional
from src.Helpers.ErrorHandling import CustomError
from src.Modules.PipeLineData.GithubSrapData.GithubScrapDTOs import GitHubProfileDTO, GithubRepositoryDTO
from src.Modules.PipeLineData.GithubSrapData.GithubScrapModels import GitHubProfile, GithubRepository
from src.Modules.PipeLineData.GithubSrapData.GithubScrapRepository import GitHubProfileRepository, GithubRepositoryRepository

class GitHubScrapDataService:
    def __init__(self):
        self.__githubProfileRepository = GitHubProfileRepository()
        self.__githubRepositoryRepository = GithubRepositoryRepository()

    def save_profile(self,candidate_id, github_info):
        try:
            # Convert date strings to datetime objects
            created_at = datetime.strptime(github_info['dates']['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            updated_at = datetime.strptime(github_info['dates']['updated_at'], '%Y-%m-%dT%H:%M:%SZ')

            profile_data = {
                'candidate_id': candidate_id,
                'username': github_info['basic_info']['username'],
                'name': github_info['basic_info']['name'],
                'email': github_info['basic_info']['email'],
                'bio': github_info['basic_info']['bio'],
                'company': github_info['basic_info']['company'],
                'location': github_info['basic_info']['location'],
                'blog': github_info['basic_info']['blog'],
                'twitter_username': github_info['basic_info']['twitter_username'],
                'avatar_url': github_info['basic_info']['avatar_url'],
                'followers': github_info['stats']['followers'],
                'following': github_info['stats']['following'],
                'public_repos': github_info['stats']['public_repos'],
                'public_gists': github_info['stats']['public_gists'],
                'total_stars_earned': github_info['stats']['total_stars_earned'],
                'contributions_last_year': github_info['stats']['contributions_last_year'],
                'rating': github_info['stats']['rating'],
                'created_at': created_at,
                'updated_at': updated_at,
                'stats': github_info['stats'],
                'dates': github_info['dates'],
                'urls': github_info['urls'],
                'additional_info': github_info['additional_info']
            }
            profile = GitHubProfile(**profile_data)
            saved_profile = self.__githubProfileRepository.create(profile)

            for repo_data in github_info['repositories']:
                # Convert date strings to datetime objects for repository data
                created_at = datetime.strptime(repo_data['dates']['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                updated_at = datetime.strptime(repo_data['dates']['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                pushed_at = datetime.strptime(repo_data['dates']['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')

                repo = GithubRepository(
                    github_profile_id=saved_profile.id,
                    name=repo_data['name'],
                    full_name=repo_data['full_name'],
                    description=repo_data['description'],
                    homepage=repo_data['homepage'],
                    language=repo_data['language'],
                    stars=repo_data['stats']['stars'],
                    watchers=repo_data['stats']['watchers'],
                    forks=repo_data['stats']['forks'],
                    open_issues=repo_data['stats']['open_issues'],
                    size=repo_data['stats']['size'],
                    created_at=created_at,
                    updated_at=updated_at,
                    pushed_at=pushed_at,
                    is_fork=repo_data['features']['fork'],
                    languages_breakdown=repo_data['languages_breakdown'],
                    stats=repo_data['stats'],
                    dates=repo_data['dates'],
                    urls=repo_data['urls'],
                    features=repo_data['features'],
                    branch=repo_data['branch'],
                    license=repo_data['license'],
                    latest_commits=repo_data['latest_commits'],
                    top_contributors=repo_data['top_contributors']
                )
                self.__githubRepositoryRepository.create(repo)

            return GitHubProfileDTO().dump(saved_profile)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_profile_by_candidate_id(self, candidate_id: str) -> Optional[dict]:
        try:
            print("Inside get_profile_by_candidate_id github::", candidate_id)
            profile = self.__githubProfileRepository.get_by_candidate_id(candidate_id)
            print("My github profile id is: ", profile)
            if not profile:
                return None

            # Create the DTOs
            profile_dto = GitHubProfileDTO()

            # Dump the profile with all its relationships
            return profile_dto.dump(profile)

        except Exception as e:
            raise CustomError(str(e), 400)

    def update_profile(self, profile_id: str, updated_data: dict) -> Optional[dict]:
        try:
            profile = self.__githubProfileRepository.get_by_id(profile_id)
            if profile:
                for key, value in updated_data.items():
                    setattr(profile, key, value)
                profile.updated_at = datetime.utcnow()
                self.__githubProfileRepository.update(profile)
                return GitHubProfileDTO().dump(profile)
            return None
        except Exception as e:
            raise CustomError(str(e), 400)

    def delete_profile(self, profile_id: str) -> bool:
        try:
            profile = self.__githubProfileRepository.get_by_id(profile_id)
            if profile:
                self.__githubProfileRepository.delete(profile)
                return True
            return False
        except Exception as e:
            raise CustomError(str(e), 400)