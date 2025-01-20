import json
from typing import Dict, Any, Union, List
from pathlib import Path
import google.generativeai as genai
import pdf2image
from PIL import Image
from docx2pdf import convert
import base64
import io


class ResumeVisionParser:
    def __init__(self, resume_path: Union[str, Path], output_dir: Union[str, Path] = None):
        self.api_key = "AIzaSyC3mzbjTwWyLKqgdpS-Z1iY5vcNhWl7mEc"
        self.resume_path = Path(resume_path)

        # Set output directory to parent of resume file if not specified
        if output_dir is None:
            self.output_dir = self.resume_path.parent
        else:
            self.output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def init_gemini(self):
        """Initialize Gemini Pro Vision model"""
        genai.configure(api_key=self.api_key)
        # Use gemini-pro-vision model for image processing
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model

    def generate_prompt(self) -> str:
        """Generate prompt for resume parsing with enhanced focus on software development"""
        return """Please analyze this resume/CV text and extract the information into a structured format.
        This parser is optimized for software developer/engineer resumes but should work with all resume types.
        Look for key sections like personal information, work experience, education, skills, and technical projects.
        Pay special attention to technical details, coding projects, and development experience.
        Return ONLY a JSON object with the following structure, no additional text or explanations:

        {
            "personal_information": {
                "full_name": "",
                "email": "",
                "phone": "",
                "location": "",
                "linkedin": "",
                "github": {
                    "url": "",
                    "username": ""  // Extract username from GitHub URL
                },
                "portfolio_website": "",
                "blog": ""
            },
            "professional_summary": "",
            "work_experience": [
                {
                    "company": "",
                    "position": "",
                    "location": "",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM",
                    "responsibilities": [],
                    "achievements": [],
                    "technologies_used": [],  // List of technologies, frameworks, languages used
                    "team_size": null,  // Optional: Size of team worked with
                    "development_methodologies": []  // e.g., Agile, Scrum, Kanban
                }
            ],
            "education": [
                {
                    "institution": "",
                    "degree": "",
                    "field_of_study": "",
                    "graduation_date": "YYYY-MM",
                    "gpa": null,
                    "relevant_coursework": [],
                    "academic_projects": [],
                    "honors_awards": []
                }
            ],
            "skills": {
                "programming_languages": [],  // e.g., Python, Java, JavaScript
                "frameworks_libraries": [],   // e.g., React, Django, Spring
                "databases": [],             // e.g., PostgreSQL, MongoDB
                "cloud_platforms": [],       // e.g., AWS, Azure, GCP
                "developer_tools": [],       // e.g., Git, Docker, Jenkins
                "testing_tools": [],         // e.g., Jest, PyTest
                "methodologies": [],         // e.g., Agile, TDD, CI/CD
                "soft_skills": [],
                "languages": [],             // Human languages
                "certifications": [
                    {
                        "name": "",
                        "issuer": "",
                        "date": "YYYY-MM",
                        "expiry_date": "YYYY-MM",  // Optional
                        "credential_id": ""        // Optional
                    }
                ]
            },
            "technical_projects": [
                {
                    "name": "",
                    "description": "",
                    "role": "",              // e.g., Lead Developer, Contributor
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM",   // Optional, for ongoing projects
                    "technologies": [],
                    "github_url": "",
                    "live_url": "",          // If project is deployed
                    "achievements": [],       // e.g., metrics, impact
                    "key_features": [],
                    "team_size": null        // Optional
                }
            ],
            "open_source_contributions": [
                {
                    "project_name": "",
                    "project_url": "",
                    "contribution_type": "",  // e.g., Bug fixes, Features, Documentation
                    "description": "",
                    "date": "YYYY-MM"
                }
            ],
            "publications_presentations": [   // Optional: for technical writing/speaking
                {
                    "title": "",
                    "type": "",              // e.g., Blog post, Conference talk, Paper
                    "date": "YYYY-MM",
                    "url": "",
                    "description": ""
                }
            ]
        }

        Guidelines for extraction:
        1. For GitHub links, extract both the full URL and the username (e.g., from 'https://github.com/username' extract 'username')
        2. In work experience, focus on technical achievements and specific technologies used
        3. For projects, prioritize those with code samples, deployments, or measurable impacts
        4. Categorize skills appropriately into the detailed technical categories
        5. Include relevant coursework and academic projects if the candidate is a recent graduate
        6. Extract any metrics or quantifiable achievements (e.g., 'reduced load time by 40%')
        7. Note any leadership or mentorship experiences in technical contexts
        8. If any field is not found in the resume, leave it as null for numbers or empty string/array as appropriate
        9. Convert all dates to YYYY-MM format"""


    @staticmethod
    def extract_json_from_response(response_text: str) -> dict:
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

    def _validate_resume_data(self, data: Dict[str, Any]) -> None:
        """Validate the parsed resume data"""
        required_sections = [
            'personal_information',
            'professional_summary',
            'work_experience',
            'education',
            'skills'
        ]

        missing_sections = [section for section in required_sections if section not in data]
        if missing_sections:
            raise ValueError(f"Missing required sections in parsed data: {missing_sections}")

        # Validate personal information
        personal_info = data['personal_information']
        required_personal_fields = ['full_name', 'email']
        missing_personal_fields = [field for field in required_personal_fields if not personal_info.get(field)]
        if missing_personal_fields:
            raise ValueError(f"Missing required personal information fields: {missing_personal_fields}")

    def convert_document_to_images(self, file_path: Union[str, Path]) -> List[str]:
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

            # Set poppler path - CHANGE THIS TO YOUR POPPLER PATH
            POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin"  # Adjust this path

            # Convert PDF to images with explicit poppler path
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=300,
                fmt="PNG",
                poppler_path=POPPLER_PATH  # Explicitly specify poppler path
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

        except Exception as e:
            raise Exception(f"Error converting document to images: {str(e)}")

    def parse_resume_with_vision(self) -> Dict[str, Any]:
        """
        Parse resume using Gemini Vision capabilities
        Returns structured data from the resume
        """
        try:
            # Convert document to images
            print("Converting document to images...")
            document_images = self.convert_document_to_images(self.resume_path)

            if not document_images:
                raise ValueError("No images could be extracted from the document")

            print(f"Successfully converted document to {len(document_images)} images")

            # Initialize model
            print("Initializing Gemini model...")
            model = self.init_gemini()
            prompt = self.generate_prompt()

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
            parsed_data = self.extract_json_from_response(combined_response)
            print("Successfully extracted JSON data from response")

            self._validate_resume_data(parsed_data)
            print("Data validation successful")

            # Save output
            output_file = self.output_dir / f"{self.resume_path.stem}_parsed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)

            print(f"Results saved to {output_file}")
            return parsed_data

        except Exception as e:
            raise Exception(f"Error parsing resume with vision: {str(e)}")


def main():
    """Main execution function"""
    resume = "./testt.docx"  #  ./test.pdf
    output_dir = "./output"

    try:
        print(f"Processing resume: {resume}")
        # Initialize parser with resume path and optional output directory
        parser = ResumeVisionParser(resume, output_dir)

        # Parse resume using vision capabilities
        result = parser.parse_resume_with_vision()

        # Print the path to the output file
        output_file = Path(output_dir) / f"{Path(resume).stem}_parsed.json"
        print(f"Results saved to {output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()