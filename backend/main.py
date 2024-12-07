from fastapi import FastAPI
from backend.app.routes import blogs, comments, visitors

app = FastAPI(
    title="Blog API",
    description="API for managing blogs, comments, and visitors",
    version="1.0.0"
)

# Register routes
app.include_router(blogs.router, prefix="/blogs", tags=["Blogs"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])
app.include_router(visitors.router, prefix="/visitors", tags=["Visitors"])

@app.get("/")
def root():
    return {"message": "Welcome to the Blog API"}
