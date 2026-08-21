import re
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional

app = FastAPI(title="Student Profile API")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Update allow_origins with your actual frontend URL(s) in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class Experience(BaseModel):
    company: str
    role: str
    duration: str
    description: Optional[str] = None


class StudentProfile(BaseModel):
    # 10 MVP fields
    name: str
    email: str
    phone: Optional[str] = None
    university: str
    major: str
    grad_year: int
    skills: List[str] = []
    experience: List[Experience] = []
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not EMAIL_REGEX.match(value):
            raise ValueError("Invalid email format.")
        return value.lower()

    @field_validator("grad_year")
    @classmethod
    def validate_grad_year(cls, value: int) -> int:
        current_year = datetime.now().year
        earliest = 1950
        latest = current_year + 10
        if value < earliest or value > latest:
            raise ValueError(
                f"grad_year must be between {earliest} and {latest}."
            )
        return value


# In-memory "database": keyed by email
students_db: dict[str, StudentProfile] = {}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Profile API"}


@app.post("/students/", response_model=StudentProfile)
def create_student(student: StudentProfile):
    if student.email in students_db:
        raise HTTPException(
            status_code=400,
            detail=f"Student with email '{student.email}' already exists.",
        )
    students_db[student.email] = student
    return student


@app.get("/students/{email}", response_model=StudentProfile)
def get_student(email: str):
    student = students_db.get(email)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with email '{email}' not found.",
        )
    return student


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)