from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime




###################
# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite3"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()




###################
# SQLAlchemy Model - Ontologies
class CustomOntology(Base):
    __tablename__ = "custom_accounts_customontologyupload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    ontology_type = Column(String(150), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    edit_uid = Column(Integer, nullable=False)
    protection = Column(Integer, nullable=False)
    
# SQLAlchemy Model - Policies
class ODRLPolicy(Base):
    __tablename__ = "custom_accounts_odrlruleupload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    edit_uid = Column(Integer, nullable=False)
    protection = Column(Integer, nullable=False)
    
###################
# Pydantic Models - Ontologies
class OntologyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str
    ontology_type: str = Field(..., min_length=1, max_length=150)
    edit_uid: int
    protection: int


class OntologyCreate(OntologyBase):
    pass


class OntologyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = None
    ontology_type: Optional[str] = Field(None, min_length=1, max_length=150)
    edit_uid: Optional[int] = None


class OntologyResponse(OntologyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

###################        
# Pydantic Models - Policies
class PolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str
    edit_uid: int
    protection: int
    
class PolicyCreate(OntologyBase):
    pass


class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = None
    ontology_type: Optional[str] = Field(None, min_length=1, max_length=150)
    edit_uid: Optional[int] = None

    
class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

        
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)        


# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

root_path="/policy-ontology"
# FastAPI Application
app = FastAPI(title="UPCAST Policy Editor API",
root_path=root_path)

######################
#  Here to provide additional APIs if manual create/update required for 
#    the negotiation dialogue.
#  This is a naive an insecure approach and is only for demo use.
try:
    exec(open("./api_v2_NEG.py").read())
    print("<< RUNNING NEGOTIATION API VERSION")
except Exception as e:
    print("<< RUNNING PROFILE EDITOR API VERSION ")
    pass


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


######################
# Ontology APIs
@app.get("/ontologies/", response_model=List[OntologyResponse])
def list_ontologies(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Retrieve a list of ontologies with pagination.
    """
    ontologies = db.query(CustomOntology).filter((CustomOntology.protection == 0) ).offset(skip).limit(limit).all()
    return ontologies


@app.get("/ontologies/{ontology_id}", response_model=OntologyResponse)
def get_ontology(ontology_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific ontology by ID.
    """
    ontology = db.query(CustomOntology).filter((CustomOntology.id == ontology_id), (CustomOntology.protection == 0) ).first()
    if not ontology:
        raise HTTPException(status_code=404, detail="Ontology not found")
    return ontology

######################
# Policy APIs
@app.get("/policies/", response_model=List[PolicyResponse])
def list_policies(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Retrieve a list of policies with pagination.
    """
    policies = db.query(ODRLPolicy).filter((ODRLPolicy.protection == 0) ).offset(skip).limit(limit).all()
    return policies
    
@app.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific policy by ID.
    """
    policy = db.query(ODRLPolicy).filter((ODRLPolicy.id == policy_id), (ODRLPolicy.protection == 0) ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
    #uvicorn.run(app, host="127.0.0.1", port=8001)
    
    
