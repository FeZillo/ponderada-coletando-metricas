def test_lists_seed_books(client):
    response = client.get("/api/books")

    assert response.status_code == 200
    books = response.json()
    assert len(books) == 3
    assert books[0]["title"] == "Clean Code"


def test_toggle_book_status_updates_stats(client):
    toggled = client.post("/api/books/2/toggle")
    stats = client.get("/api/stats")

    assert toggled.status_code == 200
    assert toggled.json()["status"] == "reading"
    assert stats.status_code == 200
    assert stats.json()["reading"] == 2


def test_unknown_book_returns_404(client):
    response = client.post("/api/books/999/toggle")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

