# from dataclasses import dataclass, asdict
# from typing import List, Optional, Set
# from selenium import webdriver
# from selenium.webdriver import ChromeOptions
# from linkedin_scraper import Person, actions
# import json
# from hashlib import md5
#
# # Constants
# BASE_LINKEDIN_URL = "https://www.linkedin.com/in/"
#
#
# @dataclass
# class Education:
#     institution_name: str
#     degree: str
#     from_date: str
#     to_date: str
#     description: Optional[str] = None
#     linkedin_url: Optional[str] = None
#
#     def __hash__(self):
#         # Create a unique hash based on core attributes
#         return hash((
#             self.institution_name,
#             self.degree,
#             self.from_date,
#             self.to_date
#         ))
#
#     def __eq__(self, other):
#         if not isinstance(other, Education):
#             return False
#         return (
#                 self.institution_name == other.institution_name
#                 and self.degree == other.degree
#                 and self.from_date == other.from_date
#                 and self.to_date == other.to_date
#         )
#
#
# @dataclass
# class Experience:
#     institution_name: str
#     position_title: str
#     duration: str
#     location: str
#     from_date: str
#     to_date: str
#     description: Optional[str] = None
#     linkedin_url: Optional[str] = None
#
#     def __hash__(self):
#         # Create a unique hash based on core attributes
#         return hash((
#             self.institution_name,
#             self.position_title,
#             self.from_date,
#             self.to_date
#         ))
#
#     def __eq__(self, other):
#         if not isinstance(other, Experience):
#             return False
#         return (
#                 self.institution_name == other.institution_name
#                 and self.position_title == other.position_title
#                 and self.from_date == other.from_date
#                 and self.to_date == other.to_date
#         )
#
#
# @dataclass
# class LinkedInProfile:
#     name: str
#     about: str
#     educations: List[Education]
#     experiences: List[Experience]
#
#
# class LinkedInScraper:
#     def __init__(self, headless: bool = True):
#         self.options = self._configure_chrome_options(headless)
#         self.driver = None
#
#     def _configure_chrome_options(self, headless: bool) -> ChromeOptions:
#         options = ChromeOptions()
#         if headless:
#             options.add_argument("--headless=new")
#             options.add_argument("--disable-gpu")
#             options.add_argument("--no-sandbox")
#             options.add_argument("--window-size=1920,1080")
#         return options
#
#     def _initialize_driver(self):
#         if not self.driver:
#             self.driver = webdriver.Chrome(options=self.options)
#
#     def login(self, email: str, password: str):
#         """Login to LinkedIn with provided credentials"""
#         self._initialize_driver()
#         actions.login(self.driver, email, password)
#
#     def _clean_text(self, text: Optional[str]) -> Optional[str]:
#         """Clean text by removing duplicates and normalizing whitespace"""
#         if not text:
#             return None
#
#         # Split text into lines and remove duplicates while preserving order
#         lines = []
#         seen_lines: Set[str] = set()
#
#         for line in text.split('\n'):
#             line = line.strip()
#             if line and line not in seen_lines:
#                 lines.append(line)
#                 seen_lines.add(line)
#
#         # Handle bullet points
#         skills_prefix = "Skills:"
#         if any(line.startswith(skills_prefix) for line in lines):
#             skills_lines = [line for line in lines if line.startswith(skills_prefix)]
#             if skills_lines:
#                 # Keep only the first skills line and clean up duplicates within it
#                 skills_items = set()
#                 for item in skills_lines[0].replace(skills_prefix, '').split('·'):
#                     skills_items.add(item.strip())
#                 lines = [line for line in lines if not line.startswith(skills_prefix)]
#                 lines.append(f"{skills_prefix} {' · '.join(sorted(skills_items))}")
#
#         return '\n'.join(lines)
#
#     def _convert_education(self, edu) -> Education:
#         return Education(
#             institution_name=edu.institution_name,
#             degree=edu.degree,
#             from_date=edu.from_date,
#             to_date=edu.to_date,
#             description=self._clean_text(edu.description),
#             linkedin_url=edu.linkedin_url
#         )
#
#     def _convert_experience(self, exp) -> Experience:
#         return Experience(
#             institution_name=exp.institution_name,
#             position_title=exp.position_title,
#             duration=exp.duration,
#             location=exp.location,
#             from_date=exp.from_date,
#             to_date=exp.to_date,
#             description=self._clean_text(exp.description),
#             linkedin_url=exp.linkedin_url
#         )
#
#     def get_profile(self, profile_name: str) -> LinkedInProfile:
#         """Scrape LinkedIn profile and return structured data"""
#         profile_url = f"{BASE_LINKEDIN_URL}{profile_name}"
#         person = Person(profile_url, driver=self.driver)
#
#         # Convert and deduplicate education and experience objects
#         educations = list({self._convert_education(edu) for edu in person.educations})
#         experiences = list({self._convert_experience(exp) for exp in person.experiences})
#
#         return LinkedInProfile(
#             name=person.name,
#             about=self._clean_text(person.about),
#             educations=educations,
#             experiences=experiences
#         )
#
#     def to_json(self, profile: LinkedInProfile) -> str:
#         """Convert profile to JSON string"""
#         return json.dumps(asdict(profile), indent=2)
#
#     def close(self):
#         """Clean up resources"""
#         if self.driver:
#             self.driver.quit()
#             self.driver = None
#
#
