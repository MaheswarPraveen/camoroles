import io
from typing import Dict, Any, List
import pypdf
from backend.llm_router import LLMRouter

CV_PARSE_PROMPT = """
You are an expert technical hiring evaluator analyzing engineering and technology candidate resumes across all disciplines (Robotics, Autonomous Systems, Embedded Firmware, Hardware, AI/ML, Software, Data, Cloud).
Extract key information and return ONLY a valid JSON object matching this schema:
{
  "headline": "Candidate professional headline, e.g. 'Robotics & Autonomous Systems Engineer (ROS2 / C++ / Motion Control)'",
  "domain": "One of: 'robotics', 'embedded', 'ai_ml', 'fullstack', 'backend', 'frontend', 'data', 'cloud_devops', 'mobile', or 'hardware'",
  "experience_years": 1.0, // numeric float, 0 if fresher or college student
  "skills": ["C++", "ROS2", "Kinematics", "Motion Planning", "Python", "Linux"], // top 5-10 technical skills
  "summary": "Concise 3-sentence summary of projects, education, and technical competencies."
}
Be realistic about experience. If they graduated recently or only have internships, experience_years should be between 0 and 1.
"""

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts raw text from an in-memory PDF stream. The raw bytes are never written to disk."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text_parts = []
    for page in reader.pages[:5]: # Cap at first 5 pages to prevent buffer overflow attacks
        extracted = page.extract_text()
        if extracted:
            text_parts.append(extracted)
    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("Could not extract readable text from PDF. The document may be scanned or empty.")
    return full_text

def parse_cv_in_memory(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Parses a CV entirely in-memory:
    1. Extracts text
    2. LLM extracts structured skills, years of experience, headline, and dense summary
    3. Returns parsed structure
    """
    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    # Truncate text to 4,000 characters to keep prompt tight and fast
    truncated_text = raw_text[:4000]

    messages = [
        {"role": "system", "content": CV_PARSE_PROMPT},
        {"role": "user", "content": f"Candidate CV text:\n{truncated_text}"}
    ]

    parsed = LLMRouter.chat_json(messages)
    return {
        "headline": parsed.get("headline", "Engineering Candidate"),
        "domain": parsed.get("domain", "general"),
        "experience_years": float(parsed.get("experience_years", 0)),
        "skills": list(parsed.get("skills", [])),
        "summary": parsed.get("summary", "")
    }
