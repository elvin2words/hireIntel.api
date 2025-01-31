from flask import Flask
from datetime import datetime
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.config.DBModelsConfig import db
from src.Helpers.ErrorHandling import CustomError
from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from typing import Optional


class LinkedInScrapingConfig(PipelineConfig):
    def __init__(self,
                 name: str = "linkedin_scraping",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 linkedin_email: str = "",
                 linkedin_password: str = "",
                 headless: bool = True):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.linkedin_email = linkedin_email
        self.linkedin_password = linkedin_password
        self.headless = headless


class LinkedInScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: LinkedInScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: LinkedInScrapingConfig = config
        self.driver: Optional[webdriver.Chrome] = None
        self._initialize_driver()
        self.__candidate_service =  CandidateService()

    def _initialize_driver(self):
        """Initialize and configure Chrome WebDriver"""
        options = ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=options)
        # Login to LinkedIn
        actions.login(self.driver, self.config.linkedin_email, self.config.linkedin_password)
        self.logger.info("Successfully initialized LinkedIn driver and logged in")

    def process_batch(self):
        """Process a batch of candidates for LinkedIn data scraping"""
        try:
            # Find candidates that need LinkedIn scraping
            candidates = (Candidate.query
                          .filter_by(pipeline_status=CandidatePipelineStatus.LINKEDIN_SCRAPE)
                          .limit(self.config.batch_size)
                          .all())

            if not candidates:
                self.logger.info("No candidates found for LinkedIn scraping")
                return

            self.logger.info(f"Processing {len(candidates)} candidates for LinkedIn scraping")

            for candidate in candidates:
                try:
                    self._process_candidate(candidate)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process LinkedIn data for candidate {candidate.id}: {str(e)}"
                    )

                    ## Update the pipeline status
                    self.__candidate_service.set_pipeline_status_to_github_scrape(candidate.id)

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            # Reinitialize driver on batch failure
            self._cleanup_driver()
            self._initialize_driver()
            raise

    def _process_candidate(self, candidate: Candidate) -> None:
        """Process LinkedIn data for a single candidate"""
        try:
            self.logger.info(f"Starting LinkedIn scraping for candidate ID: {candidate.id}")
            self.monitor.update_state(
                self.config.name,
                PipelineStatus.RUNNING,
                message=f"Scraping LinkedIn data for candidate {candidate.id}"
            )

            parsed_data = candidate.parsed_resume_data
            linkedin_url = parsed_data.get('personal_information', {}).get('linkedin', {}).get('profile_url')

            if not linkedin_url:
                self.logger.info(f"No LinkedIn URL found for candidate {candidate.id}")
                self._update_candidate_status(candidate)
                return

            # Extract username from LinkedIn URL
            profile_name = linkedin_url.split('/')[-1]
            if not profile_name:
                raise ValueError("Invalid LinkedIn URL format")

            # Fetch LinkedIn profile
            person = Person(linkedin_url, driver=self.driver)

            # Convert profile to structured data
            profile_data = {
                "name": person.name,
                "about": self._clean_text(person.about),
                "educations": [self._convert_education(edu) for edu in person.educations],
                "experiences": [self._convert_experience(exp) for exp in person.experiences]
            }

            # Update candidate data
            parsed_data['linkedin_profile'] = profile_data
            candidate.parsed_resume_data = parsed_data
            self._update_candidate_status(candidate)

            self.logger.info(f"Successfully updated LinkedIn data for candidate: {candidate.id}")

        except Exception as e:
            self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
            self._update_candidate_status(candidate, error=str(e))
            raise CustomError(f"Error processing candidate: {str(e)}", 400)

    def _update_candidate_status(self, candidate: Candidate, error: str = None) -> None:
        """Update candidate status and handle database transaction"""
        try:
            candidate.pipeline_status = CandidatePipelineStatus.GITHUB_SCRAPE # Move to next stage
            candidate.updated_at = datetime.utcnow()
            if error:
                if not candidate.parsing_errors:
                    candidate.parsing_errors = {}
                candidate.parsing_errors['linkedin_scraping'] = error

            db.session.commit()

        except Exception as e:
            self.logger.error(f"Failed to update candidate status: {str(e)}")
            db.session.rollback()
            raise

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text content"""
        if not text:
            return None
        return ' '.join(text.split())

    def _convert_education(self, edu) -> dict:
        """Convert education object to dictionary"""
        return {
            "institution_name": edu.institution_name,
            "degree": edu.degree,
            "from_date": edu.from_date,
            "to_date": edu.to_date,
            "description": self._clean_text(edu.description),
            "linkedin_url": edu.linkedin_url
        }

    def _convert_experience(self, exp) -> dict:
        """Convert experience object to dictionary"""
        return {
            "institution_name": exp.institution_name,
            "position_title": exp.position_title,
            "duration": exp.duration,
            "location": exp.location,
            "from_date": exp.from_date,
            "to_date": exp.to_date,
            "description": self._clean_text(exp.description),
            "linkedin_url": exp.linkedin_url
        }

    def _cleanup_driver(self):
        """Clean up Selenium WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error cleaning up driver: {str(e)}")
            finally:
                self.driver = None

    def stop(self):
        """Override stop method to cleanup driver"""
        self._cleanup_driver()
        super().stop()