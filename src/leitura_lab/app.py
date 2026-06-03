from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BookStatus = Literal["to_read", "reading", "done"]


class Book(BaseModel):
    id: int
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    status: BookStatus


class ReadingStats(BaseModel):
    total: int
    done: int
    reading: int
    to_read: int
    progress_percent: float


SEED_BOOKS: tuple[Book, ...] = (
    Book(id=1, title="Clean Code", author="Robert C. Martin", status="reading"),
    Book(id=2, title="The Pragmatic Programmer", author="Andrew Hunt", status="to_read"),
    Book(id=3, title="Refactoring", author="Martin Fowler", status="done"),
)


def _next_status(status: BookStatus) -> BookStatus:
    transitions: dict[BookStatus, BookStatus] = {
        "to_read": "reading",
        "reading": "done",
        "done": "to_read",
    }
    return transitions[status]


def _stats_for(books: dict[int, Book]) -> ReadingStats:
    total = len(books)
    done = sum(book.status == "done" for book in books.values())
    reading = sum(book.status == "reading" for book in books.values())
    to_read = sum(book.status == "to_read" for book in books.values())
    progress_percent = round((done / total) * 100, 2) if total else 0.0
    return ReadingStats(
        total=total,
        done=done,
        reading=reading,
        to_read=to_read,
        progress_percent=progress_percent,
    )


def create_app() -> FastAPI:
    books = {book.id: book.model_copy() for book in SEED_BOOKS}
    app = FastAPI(title="Leitura Lab API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/api/books", response_model=list[Book])
    def list_books() -> list[Book]:
        return list(books.values())

    @app.post("/api/books/{book_id}/toggle", response_model=Book)
    def toggle_book_status(book_id: int) -> Book:
        book = books.get(book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")

        updated = book.model_copy(update={"status": _next_status(book.status)})
        books[book_id] = updated
        return updated

    @app.get("/api/stats", response_model=ReadingStats)
    def get_stats() -> ReadingStats:
        return _stats_for(books)

    return app


app = create_app()

