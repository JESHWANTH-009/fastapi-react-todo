from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import SessionLocal, engine, Base

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# ✅ First create the FastAPI app
app = FastAPI()

# ✅ Then add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 Allow your React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Mount static folder
#app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="fastapi-todo-frontend/build", html=True), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# ✅ Create DB tables
Base.metadata.create_all(bind=engine)

# ✅ DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Pydantic models
class ToDoCreate(BaseModel):
    task: str
    completed: bool = False

class ToDoRead(ToDoCreate):
    id: int
    class Config:
        orm_mode = True

# ✅ CRUD Endpoints
@app.post("/todos/", response_model=ToDoRead, status_code=status.HTTP_201_CREATED)
def create_todo(todo: ToDoCreate, db: Session = Depends(get_db)):
    db_todo = models.ToDo(task=todo.task, completed=todo.completed)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/", response_model=list[ToDoRead])
def get_all_todos(db: Session = Depends(get_db)):
    return db.query(models.ToDo).all()

@app.get("/todos/{todo_id}", response_model=ToDoRead)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=ToDoRead)
def update_todo(todo_id: int, updated: ToDoCreate, db: Session = Depends(get_db)):
    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    todo.task = updated.task
    todo.completed = updated.completed
    db.commit()
    db.refresh(todo)
    return todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(models.ToDo).filter(models.ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    db.delete(todo)
    db.commit()
    return
