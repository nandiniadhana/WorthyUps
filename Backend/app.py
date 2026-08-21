from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./students.db"

# check_same_thread=False is needed only for SQLite when used with FastAPI's
# threaded request handling.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


class StudentProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True, unique=True)
    phone: Optional[str] = None
    college_name: str
    degree: str
    graduation_year: int
    bio: Optional[str] = None


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Student Profile API (SQLModel + SQLite)")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Student Profile API"}


@app.post("/students/", response_model=StudentProfile)
def create_student(student: StudentProfile, session: Session = Depends(get_session)):
    existing = session.exec(
        select(StudentProfile).where(StudentProfile.email == student.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student with email '{student.email}' already exists.",
        )

    # Ensure we don't accidentally accept a client-supplied id.
    student.id = None

    session.add(student)
    session.commit()
    session.refresh(student)
    return student


@app.get("/students/{email}", response_model=StudentProfile)
def get_student(email: str, session: Session = Depends(get_session)):
    student = session.exec(
        select(StudentProfile).where(StudentProfile.email == email)
    ).first()
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with email '{email}' not found.",
        )
    return student


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)