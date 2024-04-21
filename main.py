from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.testclient import TestClient
from typing import List
from pydantic import BaseModel
import sqlite3
import threading

# Connecting to SQLite database
conn = sqlite3.connect('book_review_system.db')
cursor = conn.cursor()

def get_db_connection():
    return sqlite3.connect('book_review_system.db')


app = FastAPI()

class Book(BaseModel):
    title: str
    author: str
    publication_year: int

class Review(BaseModel):
    text: str
    rating: int

books = []
reviews = []

@app.post("/books/")
def add_book(book: Book):
    cursor.execute("INSERT INTO books (title, author, publication_year) VALUES (?, ?, ?)",
                   (book.title, book.author, book.publication_year))
    conn.commit()
    return {"message": "Book added successfully"}

@app.post("/books/{book_id}/reviews/")
def submit_review(book_id: int, review: Review):
    if book_id >= len(books):
        raise HTTPException(status_code=404, detail="Book not found")
    cursor.execute("INSERT INTO reviews (book_id, text, rating) VALUES (?, ?, ?)",
                   (book_id, review.text, review.rating))
    conn.commit()
    return {"message": "Review submitted successfully"}

@app.get("/books/")
def get_books(author: str = None, publication_year: int = None):
    query = "SELECT * FROM books"
    if author:
        query += f" WHERE author = '{author}'"
    elif publication_year:
        query += f" WHERE publication_year = {publication_year}"
    cursor.execute(query)
    return cursor.fetchall()

@app.get("/books/{book_id}/reviews/")
def get_reviews(book_id: int):
    if book_id >= len(books):
        raise HTTPException(status_code=404, detail="Book not found")
    cursor.execute("SELECT * FROM reviews WHERE book_id = ?", (book_id,))
    return cursor.fetchall()

def send_confirmation_email(email: str, message: str):
    with get_db_connection() as conn:
        print(f"Sending confirmation email to {email}: {message}")

@app.post("/books/{book_id}/reviews/")
def submit_review(book_id: int, review: Review, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_confirmation_email, "praharsha.erri@gmail.com", "Review submitted successfully")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reviews (book_id, text, rating) VALUES (?, ?, ?)",
                       (book_id, review.text, review.rating))
        conn.commit()
    return {"message": "Review submitted successfully"}

client = TestClient(app)

def test_submit_review():
    response = client.post("/books/1/reviews/", json={"text": "Nice book!", "rating": 5})
    assert response.status_code == 200
    assert response.json() == {"message": "Review submitted successfully"}

def test_get_books():
    response = client.get("/books/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_reviews():
    response = client.get("/books/1/reviews/")
    assert response.status_code == 200
    assert len(response.json()) > 0

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)