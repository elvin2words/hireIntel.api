
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Union, List, Optional, Callable
from pathlib import Path
import pdf2image
from PIL import Image
from docx2pdf import convert
import base64
import io
import google.generativeai as genai

from src.config.ConfigBase import Config


class LLMService:
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.getConfig()["llm"]["genai_token"] #
        self.__POPPLER_PATH = self.config.getConfig()["llm"]["poppler_path"] #
        self._model = None
        self._max_retries = 3
        self._retry_delay = 2  # seconds


    def _ensure_model_initialized(self) -> None:
        """Ensures model is initialized before use"""
        if not self._model:
            self._model = self.__init_gemini()

    def __init_gemini(self):
        try:
            print("Initializing Gemini Pro Vision model...")
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            print("Model initialized successfully")
            return model
        except Exception as e:
            print(f"Failed to initialize model: {e}")
            raise

    def _retry_with_delay(self, func: Callable, *args, **kwargs):
        """Retries function with exponential backoff"""
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise
                wait_time = self._retry_delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def complete_prompt(self, prompt: str) -> str:
        def _execute_prompt():
            self._ensure_model_initialized()
            response = self._model.generate_content(prompt)
            if not response or not response.text:
                raise ValueError("Empty response from model")
            return response.text.strip()

        try:
            return self._retry_with_delay(_execute_prompt)
        except Exception as e:
            raise Exception(f"Failed to complete prompt after {self._max_retries} attempts: {str(e)}")

    """
    *******************************************************************************************************************
    For Resume text extraction
    """
    @staticmethod
    def __genPromptToExtractDataFromResume() -> str:
        """Generate prompt for resume parsing with strict alignment to defined database models"""
        return """Please analyze this resume/CV text and extract only the values that satisfy the given database schema.
        Ensure that extracted data strictly follows the model structure, including required fields and data types.
        Return ONLY a JSON object in the following format, with no additional text or explanations:

        {
            "personalInformation": {
                "fullName": "",
                "email": "",
                "phoneNumbers": [],  // Array of phone numbers
                "address": "",
                "linkedinUrl": "",
                "githubUrl": "",
                "githubHandle" : "", // extracted from github url
                "linkedinHandle": "", // extracted from linkedin Url
                "portfolioUrl": ""
            },
            "education": [
                {
                    "institution": "",
                    "degree": "",
                    "fieldOfStudy": "",
                    "startDate": "YYYY-MM-DD",
                    "endDate": "YYYY-MM-DD",  // Nullable
                    "gpa": null,  // Nullable, float
                    "description": "",
                    "location": ""
                }
            ],
            "workExperience": [
                {
                    "company": "",
                    "position": "",
                    "employmentType": "",  // Must be one of ["full_time", "part_time", "contract", "freelance", "internship"]
                    "startDate": "YYYY-MM-DD",
                    "endDate": "YYYY-MM-DD",  // Nullable
                    "isCurrent": false,
                    "location": "",
                    "description": "",
                    "achievements": []
                }
            ],
            "technicalSkills": [
                {
                    "skillName": "",
                    "proficiencyLevel": "",  // Nullable, e.g., "Expert", "Intermediate"
                    "yearsExperience": null  // Nullable, integer
                }
            ],
            "softSkills": [
                {
                    "skillName": ""
                }
            ],
            "keywords": [
                {
                    "keyword": "",
                    "category": ""  // Nullable, e.g., "Technology", "Industry", "Role"
                }
            ]
        }

        Guidelines for extraction:
        1. Ensure that `employment_type` values match only the predefined enum options.
        2. Extract `phone_numbers` as an array.
        3. Use `null` for missing numerical values (e.g., `gpa`, `years_experience`).
        4. Ensure all date fields follow the format YYYY-MM-DD.
        5. Only extract fields that directly match the database schema, ignoring unrelated information.
        6. If an attribute is not found, return it as null (for numbers) or an empty string/array as appropriate.
        7. Do not include extra fields or descriptions outside the defined structure.
        
        URL and Handle Extraction Rules:
           LinkedIn Username Extraction:
           - From URL format: https://www.linkedin.com/in/username/ or linkedin.com/in/username etc
           - Extract username portion after "in/" and before next "/" or end of URL
           - Example: https://www.linkedin.com/in/johndoe/ or linkedin.com/in/johndoe → username: johndoe etc
           - Store full URL in linkedinUrl and extracted username in linkedinHandle
           
           GitHub Username Extraction:
           - From URL format: https://github.com/username or github.com/username etc
           - Extract username portion after "github.com/" and before next "/" or end of URL
           - Example: https://github.com/johndoe or github.com/johndoe → username: johndoe etc
           - Store full URL in githubUrl and extracted username in githubHandle
       
        Strict Rules when extracting
        1. Technical Skills Extraction with Proficiency Level:
        - Extract relevant technical skills from the resume, including programming languages, tools, certifications,
         and industry-specific competencies. Automatically determine and assign a proficiency level 
         (Beginner, Intermediate, Advanced) based on the candidate’s experience, such as frequency 
         of use in work history, projects, and certifications.

        2. Soft Skills Discovery and Extraction:
        - Analyze the resume to infer relevant soft skills based on job roles, responsibilities, and achievements. 
        Automatically identify key interpersonal, communication, leadership, and problem-solving 
        abilities that align with the candidate’s background.

        3. Comprehensive Keyword Discovery and Extraction:
        - Analyze the resume to discover and extract important keywords, including technical skills, soft skills, 
        industry-specific terminology, and certifications. Automatically generate a well-structured set of relevant 
        keywords based on the candidate’s experience and expertise.
        """

    @staticmethod
    def __validate_resume_data(data: Dict[str, Any]) -> None:
        """Validate the parsed resume data"""
        required_sections = [
            'personalInformation',
            'keywords',
            'workExperience',
            'education',
            'technicalSkills'
        ]

        missing_sections = [section for section in required_sections if section not in data]
        if missing_sections:
            raise ValueError(f"Missing required sections in parsed data: {missing_sections}")

        # Validate personal information
        personal_info = data['personalInformation']
        required_personal_fields = ['fullName', 'email']
        missing_personal_fields = [field for field in required_personal_fields if not personal_info.get(field)]
        if missing_personal_fields:
            raise ValueError(f"Missing required personal information fields: {missing_personal_fields}")


    def parse_resume_with_vision(self, resume_path: str) -> Dict[str, Any]:
        """
        Parse resume using Gemini Vision capabilities
        Returns structured data from the resume
        """
        try:
            file_extension = Path(resume_path).suffix.lower()
            if file_extension in ['.pdf', '.docx']:
                return self.parse_resume_document(resume_path)
            else:
                _resume_path = Path(resume_path)
                # Convert document to images
                print("Converting document to images...")
                document_images = self.__convert_document_to_images(_resume_path)

                if not document_images:
                    raise ValueError("No images could be extracted from the document")

                print(f"Successfully converted document to {len(document_images)} images")

                # Initialize model
                print("Initializing Gemini model...")
                model = self.__init_gemini()
                prompt = self.__genPromptToExtractDataFromResume()

                # Process each image with the model
                all_responses = []
                for img_data in document_images:
                    # Extract base64 data from the data URL
                    base64_data = img_data.split('base64,')[1]

                    # Create the image part in the correct format for Gemini
                    image_part = {
                        "mime_type": "image/png",
                        "data": base64_data
                    }

                    # Generate content with both prompt and image
                    response = model.generate_content([
                        prompt,
                        image_part
                    ])
                    all_responses.append(response.text)

                # Combine and parse responses
                combined_response = "\n".join(all_responses)
                parsed_data = self.__extract_json_from_response(combined_response)
                print("Successfully extracted JSON data from response")
                print(json.dumps(parsed_data, indent=4))
                self.__validate_resume_data(parsed_data)
                print("Data validation successful")

                return parsed_data

        except Exception as e:
            raise Exception(f"Error parsing resume with vision: {str(e)}")

    """
    *******************************************************************************************************
    For Profile creation
    """

    def create_profile(self, prompt: str) -> Dict[str, Any]:
        """
        Creates a profile analysis using the provided prompt
        Returns validated profile data
        """
        try:
            response_text = self.complete_prompt(prompt)
            parsed_data = self.__extract_json_from_response(response_text)

            required_fields = [
                "overallMatch", "technicalSkills",
                "softSkills", "experience", "education", "projectsAndAchievements",
                "socialPresence"
            ]

            missing_fields = [f for f in required_fields if f not in parsed_data]
            if missing_fields:
                raise ValueError(f"Missing required fields in profile data: {missing_fields}")

            required_scores = ["technicalSkills", "softSkills", "experience",
                               "education", "projectsAndAchievements", "socialPresence"]

            for field in required_scores:
                score = parsed_data[field].get("score")
                if not isinstance(score, (int, float)) or not 0 <= score <= 100:
                    raise ValueError(f"Invalid score in {field}")

            overall_score = parsed_data["overallMatch"].get("score")
            if not isinstance(overall_score, (int, float)) or not 0 <= overall_score <= 100:
                raise ValueError("Invalid overall match score")

            return parsed_data

        except Exception as e:
            raise Exception(f"Failed to create profile: {str(e)}")



    """
    *******************************************************************************************************
    Helper functions
    """
    @staticmethod
    def __extract_json_from_response(response_text: str) -> dict:
        """Extract JSON from response text"""
        try:
            # First attempt: Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Second attempt: Try to find JSON within markdown code blocks
            import re
            code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            matches = re.findall(code_block_pattern, response_text)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

            # Third attempt: Try to find JSON between curly braces
            json_pattern = r"\{[\s\S]*\}"
            matches = re.findall(json_pattern, response_text)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

            raise ValueError("No valid JSON found in the response")


    def __convert_document_to_images(self, file_path: Union[str, Path]) -> List[str]:
        """
        Convert PDF or DOCX document to a list of base64 encoded images
        Returns list of base64 strings ready for Gemini Vision
        """
        try:
            pdf_path = file_path

            # If document is DOCX, convert to PDF first
            if str(file_path).lower().endswith('.docx'):
                pdf_path = file_path.parent / f"{file_path.stem}_temp.pdf"
                convert(str(file_path), str(pdf_path))

            # Convert PDF to images with explicit poppler path
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,
                fmt="PNG",
                poppler_path=self.__POPPLER_PATH  # Explicitly specify poppler path
            )

            # Convert images to base64
            images_base64 = []
            for img in images:
                # Optimize image size if needed
                if img.size[0] > 2000:  # If width is greater than 2000px
                    ratio = 2000 / img.size[0]
                    new_size = (2000, int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                buffered = io.BytesIO()
                img.save(buffered, format="PNG", optimize=True)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                images_base64.append(f"data:image/png;base64,{img_base64}")

            # Clean up temporary PDF if converted from DOCX
            if str(file_path).lower().endswith('.docx') and Path(pdf_path).exists():
                Path(pdf_path).unlink()

            return images_base64

        except Exception as e:
            raise Exception(f"Error converting document to images: {str(e)}")

    """
    *******************************************************************************************************************
    Profile Verification
    """

    def verify_profile(self, prompt: str) -> Dict[str, Any]:
        try:
            print("Starting profile verification...")
            response_text = self.complete_prompt(prompt)

            if not response_text:
                raise ValueError("Empty response from LLM")

            parsed_data = self.__extract_json_from_response(response_text)

            required_fields = ['is_match', 'confidence_score', 'reasoning']
            missing_fields = [f for f in required_fields if f not in parsed_data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            if not isinstance(parsed_data['confidence_score'], (int, float)) or \
                    not 0 <= parsed_data['confidence_score'] <= 100:
                raise ValueError("Invalid confidence score")

            return parsed_data

        except Exception as e:
            raise Exception(f"Profile verification failed: {str(e)}")

    """
    1. To verify if the github and linkedIn profiles 
    belong to the correct person
    """
    @staticmethod
    def __genPromptToVerifyProfile(social_media_profile, resume_profile):
        prompt = ""
        return prompt

    """
    1. To verify if the github and linkedIn username 
    belong to the correct person
    """
    @staticmethod
    def __genPromptToVerifyCandidateProfessionalHandle(social_media_profile, resume_profile):
        # 1. get all the links we got on google search for linkedIn and github
        # 2. fetch the profiles for github and linkedin
        # 3. pass them to the llm verify if found return the username
        prompt = ""
        return prompt

    # To clean the scrapped linkedIn data before cleaning
    @staticmethod
    def __genPromptToCleanLinkedInScrapedData():
        prompt = ""
        return prompt

    # To generate profile
    @staticmethod
    def __genPromptToCreateCandidateProfile():
        prompt = ""
        return prompt

    # To generate candidate response
    @staticmethod
    def __genPromptToCreatePersonalizedEmail(context):
        prompt = ""
        return prompt

    @staticmethod
    def __genPromptToCreateInterviewSchedule(context):
        prompt = ""
        return prompt


    def create_interview_schedule(self, prompt: str) -> Dict[str, Any]:
        """
        Creates and validates an interview schedule response from the LLM

        Expected JSON format:
        {
            "interviews": [
                {
                    "candidate_id": str,
                    "interviewer_id": str,
                    "start_datetime": str,  # ISO format
                    "end_datetime": str,    # ISO format
                    "duration_minutes": int,
                    "location": {
                        "type": str,        # "virtual" or "in_person"
                        "details": str
                    },
                    "meeting_link": str,    # Optional, for virtual interviews
                    "requirements": List[str]
                }
            ],
            "constraints_satisfied": bool,
            "schedule_metadata": {
                "total_interviews": int,
                "total_duration_hours": float,
                "daily_distribution": Dict[str, int]  # Date -> number of interviews
            }
        }
        """
        try:
            print("Starting interview schedule creation...")
            response_text = self.complete_prompt(prompt)

            if not response_text:
                raise ValueError("Empty response from LLM")

            parsed_data = self.__extract_json_from_response(response_text)

            # Validate required top-level fields
            required_fields = ['interviews', 'constraints_satisfied', 'schedule_metadata']
            missing_fields = [f for f in required_fields if f not in parsed_data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # Validate interviews array
            if not isinstance(parsed_data['interviews'], list) or not parsed_data['interviews']:
                raise ValueError("Invalid or empty interviews array")

            # Validate each interview
            for interview in parsed_data['interviews']:
                interview_required_fields = [
                    'candidate_id', 'interviewer_id', 'start_datetime',
                    'end_datetime', 'duration_minutes', 'location'
                ]
                missing_interview_fields = [f for f in interview_required_fields if f not in interview]
                if missing_interview_fields:
                    raise ValueError(f"Missing required interview fields: {missing_interview_fields}")

                # Validate datetime formats
                try:
                    datetime.fromisoformat(interview['start_datetime'])
                    datetime.fromisoformat(interview['end_datetime'])
                except ValueError:
                    raise ValueError("Invalid datetime format in interview schedule")

                # Validate location
                if not isinstance(interview['location'], dict) or \
                        'type' not in interview['location'] or \
                        interview['location']['type'] not in ['virtual', 'in_person']:
                    raise ValueError("Invalid location data")

                # Validate duration is positive
                if not isinstance(interview['duration_minutes'], int) or interview['duration_minutes'] <= 0:
                    raise ValueError("Invalid duration_minutes")

            # Validate schedule metadata
            metadata_required_fields = ['total_interviews', 'total_duration_hours', 'daily_distribution']
            missing_metadata_fields = [f for f in metadata_required_fields if f not in parsed_data['schedule_metadata']]
            if missing_metadata_fields:
                raise ValueError(f"Missing required metadata fields: {missing_metadata_fields}")

            # Validate numerical fields in metadata
            if not isinstance(parsed_data['schedule_metadata']['total_interviews'], int) or \
                    not isinstance(parsed_data['schedule_metadata']['total_duration_hours'], (int, float)):
                raise ValueError("Invalid numerical values in schedule metadata")

            return parsed_data

        except Exception as e:
            raise Exception(f"Interview schedule creation failed: {str(e)}")


    def generate_notification_email(self, prompt: str) -> Dict[str, Any]:
        """
        Creates a notification email using the provided prompt
        Returns validated notification data structure
        """
        try:
            response_text = self.complete_prompt(prompt)
            parsed_data = self.__extract_json_from_response(response_text)

            # Validate required fields
            required_fields = ['subject', 'content', 'notification_type', 'personalization', 'metadata']
            missing_fields = [f for f in required_fields if f not in parsed_data]
            if missing_fields:
                raise ValueError(f"Missing required fields in notification data: {missing_fields}")

            return parsed_data

        except Exception as e:
            raise Exception(f"Failed to generate notification email: {str(e)}")

    def parse_resume_document(self, resume_path: str) -> Dict[str, Any]:
        """
        Parse resume document (PDF or DOCX) using Gemini Vision capabilities
        Returns structured data from the resume
        """
        try:
            print("Initializing Gemini model...")
            model = self.__init_gemini()
            prompt = self.__genPromptToExtractDataFromResume()

            print("Uploading resume document...")
            uploaded_file = genai.upload_file(path=resume_path)
            print(f"Uploaded file '{uploaded_file.display_name}' as: {uploaded_file.uri}")

            print("Sending document to Gemini Vision API...")
            response = model.generate_content(
                [uploaded_file, prompt]
            )

            print("Extracting JSON data from response...")
            parsed_data = self.__extract_json_from_response(response.text)

            self.__validate_resume_data(parsed_data)
            print("Data validation successful")

            print("data; ", json.dumps(parsed_data, indent=2))

            # Verify the uploaded file
            file = genai.get_file(name=uploaded_file.name)
            print(f"Retrieved file '{file.display_name}' as: {uploaded_file.uri}")

            return parsed_data

        except Exception as e:
            raise Exception(f"Error parsing resume document: {str(e)}")

    def extract_info_from_email(self, prompt: str) -> Dict[str, Any]:
        try:
            print("Starting email data extraction extraction...")
            response_text = self.complete_prompt(prompt)

            if not response_text:
                raise ValueError("Empty response from LLM")

            parsed_data = self.__extract_json_from_response(response_text)
            return parsed_data

        except Exception as e:
            raise Exception(f"Email infor extraction failed: {str(e)}")