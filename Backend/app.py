from fastapi import FastAPI, HTTPException, status, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import os
import io
import re
from pypdf import PdfReader

app = FastAPI(
    title="Student Profile API",
    description="Backend API for the Student Profile Form",
    version="1.0.0",
)

# CORS middleware - enabled for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory where uploaded resumes are stored
UPLOAD_DIR = os.path.join("uploads", "resume")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_RESUME_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


class StudentProfileResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    dob: str
    gender: str
    major: str
    graduation_year: int
    roll_number: str
    portfolio_url: Optional[str] = None
    bio: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None


# In-memory storage for submitted students
students_db: List[StudentProfileResponse] = []


@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Profile API. Visit /docs for API documentation."}


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    extracted_text = ""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n"
    except Exception:
        extracted_text = ""

    return extracted_text.strip()


# Regex patterns used to detect resume section headers (case-insensitive, whole line match)
SECTION_PATTERNS = {
    "skills": re.compile(
        r"^\s*(technical\s+skills|core\s+skills|key\s+skills|skills)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^\s*(education|academic\s+background|educational\s+qualifications|academics)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^\s*(work\s+experience|professional\s+experience|employment\s+history|experience)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^\s*(personal\s+projects|academic\s+projects|projects)\s*:?\s*$",
        re.IGNORECASE,
    ),
}


def _parse_resume_sections(text: str) -> Dict[str, str]:
    sections = {
        "skills": "",
        "education": "",
        "experience": "",
        "projects": "",
    }

    if not text:
        return sections

    lines = text.split("\n")

    # Find the line index and section name for every header found in the text
    header_positions = []
    for idx, line in enumerate(lines):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        for section_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(cleaned_line):
                header_positions.append((idx, section_name))
                break

    if not header_positions:
        return sections

    header_positions.sort(key=lambda item: item[0])

    for i, (line_idx, section_name) in enumerate(header_positions):
        start = line_idx + 1
        end = header_positions[i + 1][0] if i + 1 < len(header_positions) else len(lines)

        content_lines = [l.strip() for l in lines[start:end] if l.strip()]
        content = "\n".join(content_lines)

        if sections[section_name]:
            sections[section_name] += "\n" + content
        else:
            sections[section_name] = content

    return sections


async def _save_resume(resume: Optional[UploadFile]):
    if resume is None or resume.filename == "":
        return None, None

    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")

    file_bytes = await resume.read()

    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Resume file size must be less than 2 MB.")

    saved_filename = f"{uuid.uuid4()}_{resume.filename}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    resume_text = _extract_text_from_pdf(file_bytes)

    return saved_filename, resume_text


async def _create_student(
    full_name: str,
    email: str,
    phone: str,
    dob: str,
    gender: str,
    major: str,
    graduation_year: int,
    roll_number: str,
    portfolio_url: Optional[str],
    bio: Optional[str],
    resume: Optional[UploadFile],
):
    resume_filename, resume_text = await _save_resume(resume)

    new_student = StudentProfileResponse(
        id=str(uuid.uuid4()),
        full_name=full_name,
        email=email,
        phone=phone,
        dob=dob,
        gender=gender,
        major=major,
        graduation_year=graduation_year,
        roll_number=roll_number,
        portfolio_url=portfolio_url if portfolio_url else None,
        bio=bio if bio else None,
        resume_filename=resume_filename,
        resume_text=resume_text,
    )

    students_db.append(new_student)

    return {
        "status": "success",
        "message": "Student profile created successfully.",
        "student": new_student,
    }


@app.post("/api/student", status_code=status.HTTP_201_CREATED)
async def create_student(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    major: str = Form(...),
    graduation_year: int = Form(...),
    roll_number: str = Form(...),
    portfolio_url: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    return await _create_student(
        full_name,
        email,
        phone,
        dob,
        gender,
        major,
        graduation_year,
        roll_number,
        portfolio_url,
        bio,
        resume,
    )


@app.post("/api/students", status_code=status.HTTP_201_CREATED)
async def create_student_alias(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    major: str = Form(...),
    graduation_year: int = Form(...),
    roll_number: str = Form(...),
    portfolio_url: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    return await _create_student(
        full_name,
        email,
        phone,
        dob,
        gender,
        major,
        graduation_year,
        roll_number,
        portfolio_url,
        bio,
        resume,
    )


@app.post("/api/resume/parse", status_code=status.HTTP_200_OK)
async def parse_resume(resume: UploadFile = File(...)):
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")

    file_bytes = await resume.read()

    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Resume file size must be less than 2 MB.")

    # Keep existing file-saving functionality intact
    saved_filename = f"{uuid.uuid4()}_{resume.filename}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    resume_text = _extract_text_from_pdf(file_bytes)
    extracted_data = _parse_resume_sections(resume_text)

    return {
        "status": "success",
        "filename": resume.filename,
        "extracted_data": extracted_data,
    }


@app.get("/api/students")
def get_all_students():
    return {
        "status": "success",
        "count": len(students_db),
        "students": students_db,
    }


@app.get("/api/students/{student_id}")
def get_student(student_id: str):
    for student in students_db:
        if student.id == student_id:
            return {"status": "success", "student": student}
    raise HTTPException(status_code=404, detail="Student not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)