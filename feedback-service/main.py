import os
from datetime import datetime
from typing import List, Optional

import uvicorn
from bson import ObjectId
# FastAPI and CORS Middleware imports
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware 
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# --- Configuration & Setup ---

app = FastAPI(
    title="Student Performance Feedback API",
    description="API for managing students, mentors, and feedback.",
    version="1.0.0"
)

# --- Add CORS Middleware ---
# Define the origins allowed to connect.
# Use ["*"] for development to allow all origins,
# or be more specific in production (e.g., ["http://localhost:3000", "https://yourdomain.com"])
origins = [
    "*" # Allows all origins - suitable for local development/testing
    # Add specific origins if needed, e.g.:
    # "http://localhost",
    # "http://127.0.0.1",
    # "null" # Needed if opening the HTML file directly via file:///
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# --- End of CORS Middleware Addition ---


# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017") # Use this when running inside docker-compose
client = MongoClient(MONGODB_URL)
db = client["student_performance_db"]


users_collection = db["users"]
students_collection = db["students"]
mentors_collection = db["mentors"]
feedbacks_collection = db["feedbacks"]


# Helper to serialize ObjectId to string
def serialize_doc(doc):
    if doc and "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]

# --- Pydantic Models ---

# Base User model (Stored in DB) - Password is hashed
class UserInDB(BaseModel):
    email: EmailStr
    name: str
    hashed_password: str
    role: str  # "student", "mentor", or "admin"
    department: Optional[str] = None
    # Consider linking User to Student/Mentor profiles via their IDs
    student_db_id: Optional[str] = None # Link to _id in students_collection
    mentor_db_id: Optional[str] = None # Link to _id in mentors_collection
    is_active: bool = True # Useful for disabling accounts

# Model for creating users (Receives plain password)
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str # Plain password from input
    role: str = Field(..., pattern="^(student|mentor|admin)$") # Enforce roles
    department: Optional[str] = None

# Model for user output (does not expose password)
class UserOut(BaseModel):
    id: str = Field(alias="_id") # Map _id to id
    email: EmailStr
    name: str
    role: str
    department: Optional[str] = None
    is_active: bool

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class StudentBase(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    name: str
    email: EmailStr
    department: str

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: str = Field(alias="_id") # Map _id to id

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class MentorBase(BaseModel):
    mentor_id: str = Field(..., description="Unique mentor identifier")
    name: str
    email: EmailStr
    department: str

class MentorCreate(MentorBase):
    pass

class MentorOut(MentorBase):
    id: str = Field(alias="_id") # Map _id to id

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class PerformanceFeedbackBase(BaseModel):
    student_id: str # Should correspond to Student.student_id
    mentor_id: str   # Should correspond to Mentor.mentor_id
    feedback: str
    highlights: List[str] = []

class PerformanceFeedbackCreate(PerformanceFeedbackBase):
    pass

class PerformanceFeedbackOut(PerformanceFeedbackBase):
    id: str = Field(alias="_id") # Map _id to id
    date: datetime
    # Include names fetched during creation for easier display
    student_name: Optional[str] = None
    mentor_name: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


# --- Utility Functions ---

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# --- API Routes ---

@app.get("/", tags=["General"])
async def root():
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to Student Performance Feedback Service"}



# --- Admin Routes ---
# TODO: Protect these routes with authentication (e.g., check if user is admin)

@app.post("/admin/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Admin"])
async def register_admin(user_in: UserCreate):
    """Registers a new admin user. Ensures email is unique."""
    if user_in.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' for this endpoint."
        )

    # Check if email already exists
    existing_user = users_collection.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user_in.email}' is already registered."
        )

    hashed_password = get_password_hash(user_in.password)
    user_db = UserInDB(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_password,
        role=user_in.role,
        department=user_in.department # Assuming admin might have a department
    )

    try:
        inserted_result = users_collection.insert_one(user_db.model_dump(exclude_none=True))
        # Fetch the created user to return it conforming to UserOut model
        created_user = users_collection.find_one({"_id": inserted_result.inserted_id})
        if created_user:
             # Manually add _id as 'id' for the response model
            created_user['id'] = str(created_user['_id'])
            return created_user
        else:
             # This case should ideally not happen if insert was successful
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created admin")

    except DuplicateKeyError: # Just in case find_one misses a race condition
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user_in.email}' is already registered (duplicate key)."
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register admin")


@app.post("/admin/student/create", response_model=StudentOut, status_code=status.HTTP_201_CREATED, tags=["Admin"])
async def create_student(student_in: StudentCreate):
    """Creates a new student profile. Ensures student_id and email are unique."""
    if students_collection.find_one({"student_id": student_in.student_id}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student ID '{student_in.student_id}' already exists."
        )
    if students_collection.find_one({"email": student_in.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{student_in.email}' is already registered for a student."
        )

    try:
        student_dict = student_in.model_dump()
        inserted_result = students_collection.insert_one(student_dict)
        created_student = students_collection.find_one({"_id": inserted_result.inserted_id})
        if created_student:
            created_student['id'] = str(created_student['_id'])
            return created_student
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created student")

    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate key error (Student ID or Email)."
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create student")


@app.post("/admin/mentor/create", response_model=MentorOut, status_code=status.HTTP_201_CREATED, tags=["Admin"])
async def create_mentor(mentor_in: MentorCreate):
    """Creates a new mentor profile. Ensures mentor_id and email are unique."""
    if mentors_collection.find_one({"mentor_id": mentor_in.mentor_id}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mentor ID '{mentor_in.mentor_id}' already exists."
        )
    if mentors_collection.find_one({"email": mentor_in.email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{mentor_in.email}' is already registered for a mentor."
        )

    try:
        mentor_dict = mentor_in.model_dump()
        inserted_result = mentors_collection.insert_one(mentor_dict)
        created_mentor = mentors_collection.find_one({"_id": inserted_result.inserted_id})
        if created_mentor:
             created_mentor['id'] = str(created_mentor['_id'])
             return created_mentor
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created mentor")

    except DuplicateKeyError:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate key error (Mentor ID or Email)."
        )
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create mentor")


@app.get("/admin/students", response_model=List[StudentOut], tags=["Admin"])
async def list_students():
    """Lists all student profiles."""
    students = students_collection.find()
    # Manually map _id to id for each document
    # Use serialize_docs helper for consistency
    return serialize_docs(list(students))


@app.get("/admin/mentors", response_model=List[MentorOut], tags=["Admin"])
async def list_mentors():
    """Lists all mentor profiles."""
    mentors = mentors_collection.find()
    # Manually map _id to id for each document
    # Use serialize_docs helper for consistency
    return serialize_docs(list(mentors))


# --- Mentor Routes ---
# TODO: Protect these routes (e.g., only allow logged-in mentors to create/view feedback)

@app.post("/mentor/feedback/create", response_model=PerformanceFeedbackOut, status_code=status.HTTP_201_CREATED, tags=["Mentor"])
async def create_feedback(feedback_in: PerformanceFeedbackCreate):
    """Creates performance feedback from a mentor for a student."""
    # Validate student exists
    student = students_collection.find_one({"student_id": feedback_in.student_id})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{feedback_in.student_id}' not found."
        )

    # Validate mentor exists
    mentor = mentors_collection.find_one({"mentor_id": feedback_in.mentor_id})
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with ID '{feedback_in.mentor_id}' not found."
        )

    feedback_dict = feedback_in.model_dump()
    feedback_dict["date"] = datetime.utcnow()
    # Store names at the time of creation for easy retrieval
    feedback_dict["student_name"] = student.get("name", "N/A")
    feedback_dict["mentor_name"] = mentor.get("name", "N/A")

    try:
        inserted_result = feedbacks_collection.insert_one(feedback_dict)
        created_feedback = feedbacks_collection.find_one({"_id": inserted_result.inserted_id})
        if created_feedback:
             # Use serialize_doc helper
             return serialize_doc(created_feedback)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created feedback")

    except Exception as e:
         # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create feedback")


@app.get("/mentor/{mentor_id}/feedbacks", response_model=List[PerformanceFeedbackOut], tags=["Mentor", "Feedback"])
async def list_mentor_feedbacks(mentor_id: str):
    """Lists all feedback provided by a specific mentor."""
    # Check if mentor exists (optional, but good practice)
    if not mentors_collection.find_one({"mentor_id": mentor_id}):
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor with ID '{mentor_id}' not found."
        )

    feedbacks = feedbacks_collection.find({"mentor_id": mentor_id})
    return serialize_docs(list(feedbacks))


# --- Student Routes ---
# TODO: Protect this route (e.g., only allow the specific student or an admin to view)

@app.get("/student/{student_id}/feedbacks", response_model=List[PerformanceFeedbackOut], tags=["Student", "Feedback"])
async def list_student_feedbacks(student_id: str):
    """Lists all feedback received by a specific student."""
     # Check if student exists (optional, but good practice)
    if not students_collection.find_one({"student_id": student_id}):
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found."
        )

    feedbacks = feedbacks_collection.find({"student_id": student_id})
    # Use serialize_docs helper for consistency
    return serialize_docs(list(feedbacks))


# --- Main Execution ---

if __name__ == "__main__":
    # The --reload flag is great for development but should generally be off in production
    # The Dockerfile CMD handles running this in the container
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)