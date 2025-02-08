import requests
import json
from typing import Dict, Optional, Union
from http import HTTPStatus


class RapidLinkedInAPIClient:
    """A client for interacting with the LinkedIn Data API."""

    BASE_URL = "https://linkedin-data-api.p.rapidapi.com/"

    def __init__(self, rapid_api_key: str) -> None:

        self.headers = {
            "x-rapidapi-key": rapid_api_key,
            "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
        }

    def get_profile(self, username: str) -> Union[Dict, None]:
        """
        Fetch LinkedIn profile data for a given username.

        Args:
            username (str): LinkedIn username to fetch data for

        Returns:
            Dict: Formatted profile data

        Raises:
            requests.exceptions.RequestException: If the API request fails
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        try:
            print("Fetching LinkedIn profile data for {}".format(username))
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params={"username": username},
                timeout=10
            )

            response.raise_for_status()

            # Parse and format the response data
            data = response.json()
            print("Fetched LinkedIn profile data for {}".format(username))
            parsed_data = self._format_profile_data(data)

            if parsed_data["basic_info"]["username"] is not None:
                return parsed_data

            return None

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")

    def _format_profile_data(self, data: Dict) -> Dict:
        """
        Format and structure the raw profile data.

        Args:
            data (Dict): Raw profile data from the API

        Returns:
            Dict: Formatted profile data
        """
        return {
            "basic_info": {
                "id": data.get("id"),
                "username": data.get("username"),
                "full_name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                "headline": data.get("headline"),
                "location": data.get("geo", {}).get("full"),
                "summary": data.get("summary")
            },
            "education": [
                {
                    "school": edu.get("schoolName"),
                    "degree": edu.get("degree"),
                    "field": edu.get("fieldOfStudy"),
                    "years": f"{edu.get('start', {}).get('year', 'N/A')} - {edu.get('end', {}).get('year', 'Present')}"
                }
                for edu in data.get("educations", [])
            ],
            "experience": [
                {
                    "company": pos.get("companyName"),
                    "title": pos.get("title"),
                    "location": pos.get("location"),
                    "duration": f"{pos.get('start', {}).get('year', 'N/A')} - {pos.get('end', {}).get('year', 'Present')}",
                    "description": pos.get("description")
                }
                for pos in data.get("fullPositions", [])
            ],
            "skills": [skill.get("name") for skill in data.get("skills", [])]
        }