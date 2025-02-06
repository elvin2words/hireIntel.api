
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, List
import json

from lxml.etree import indent

from src.Helpers.LLMService import LLMService
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.TextExtractionData.TextExtractionService import TextExtractionDataService
from src.PipeLines.Profiling.DataScraping.GitHubScrap.GithubScraper import GitHubScraper
from src.PipeLines.Profiling.DataScraping.LinkedInScrap.RapidLinkedInScrapper import RapidLinkedInAPIClient

class HandleProfileVerification:
    def __init__(self):
        self.github_scraper = GitHubScraper()
        self.linkedin_scraper = RapidLinkedInAPIClient()
        self.candidate_service = CandidateService()
        self.llm_service = LLMService()
        self.textExtractionDataService = TextExtractionDataService()

    def __create_verification_prompt(self, context) -> str:
        return f"""Analyze and compare the following profile information to determine if they represent the same person.

        {context}

        ANALYSIS GUIDELINES:
        1. Name Comparison:
           - Consider exact matches, common nicknames, and name variations 
           - Account for middle names or initials

        2. Location Analysis:
           - Check for exact matches or nearby locations
           - Consider recent relocations if timeline suggests it

        3. Professional Details: 
           - Compare current and past employment
           - Look for matching educational background
           - Examine career progression timeline

        4. Contextual Clues:
           - Look for consistent narrative across both profiles
           - Check for matching skills, industries, or expertise 
           - Consider timeline consistency

        Provide your analysis in JSON format with:
        - "is_match": boolean
        - "confidence_score": 0-100 
        - "reasoning": match analysis with specific elements
        - "matching_elements": list of matching elements
        - "discrepancies": list of mismatching/concerning elements

        Focus on concrete evidence. Note insufficient data where relevant.
        """

    def __create_linkedin_verification_prompt(self, scraped_data: dict, candidate_data: dict,
                                              resume_data: dict) -> str:
        return f"""Analyze the LinkedIn profile and resume data to determine if they represent the same person.
        LinkedIn Profile:
        - Name: {scraped_data["basic_info"]["full_name"]}
        - Headline: {scraped_data["basic_info"]["headline"]} 
        - Location: {scraped_data["basic_info"]["location"]}
        - Summary: {scraped_data["basic_info"]["summary"]}
        - Education: {scraped_data["education"]}
        - Experience: {scraped_data["experience"]}

        Resume Data:  
        - Name: {candidate_data['firstName']} {candidate_data['lastName']}
        - Location: {candidate_data.get('location', 'N/A')}
        - Education: {resume_data.get('education', 'N/A')}
        - Work Experience: {resume_data.get('workExperience', 'N/A')}

        Respond in JSON format with:
        {{
            "is_match": boolean,
            "confidence_score": 0-100,
            "reasoning": analysis with matching/mismatching elements,
            "matching_elements": [list of matching elements],
            "discrepancies": [list of mismatching elements] 
        }}
        """

    def __create_github_verification_prompt(self, scraped_data: dict, candidate_data: dict) -> str:
        return f"""Analyze the GitHub profile and candidate data to determine if they represent the same person.  
        GitHub Profile:
        - Name: {scraped_data["basic_info"]["name"]}
        - Bio: {scraped_data["basic_info"]["bio"]} 
        - Location: {scraped_data["basic_info"]["location"]}
        - Company: {scraped_data["basic_info"]["company"]}

        Candidate Data:
        - Name: {candidate_data['firstName']} {candidate_data['lastName']}  
        - Email: {candidate_data['email']}
        - Location: {candidate_data.get('location', 'N/A')}
        - Current/Last Company: {candidate_data.get('current_company', 'N/A')}

        Respond in JSON format with:
        {{
            "is_match": boolean, 
            "confidence_score": 0-100,
            "reasoning": analysis with matching/mismatching elements,
            "matching_elements": [list of matching elements],
            "discrepancies": [list of mismatching elements]
        }}
        """

    def verify_profile(self, scraped_data: dict, candidate_id: str, profile_type: str) -> dict:
        try:
            candidate_data = self.candidate_service.fetch_by_id(candidate_id)
            resume_data = self.textExtractionDataService.get_resume_by_candidate_id(candidate_id)

            if profile_type.lower() == "linkedin":
                context = self.__create_linkedin_verification_prompt(scraped_data, candidate_data, resume_data)
            elif profile_type.lower() == "github":
                context = self.__create_github_verification_prompt(scraped_data, candidate_data)
            else:
                raise ValueError(f"Invalid profile type: {profile_type}")

            prompt = self.__create_verification_prompt(context)
            json_res = self.llm_service.verify_profile(prompt)
            print("Verification response:", json.dumps(json_res, indent=2))

            confidence_score = json_res.get('confidence_score', 0)
            if not isinstance(confidence_score, (int, float)) or not 0 <= confidence_score <= 100:
                raise ValueError("Invalid confidence score")

            return json_res

        except Exception as e:
            print(f"Error during profile verification: {e}")
            return {}
