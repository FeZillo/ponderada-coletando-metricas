const API_BASE_URL = "http://127.0.0.1:8000";

const statusLabels = {
  to_read: "Nao lido",
  reading: "Lendo",
  done: "Concluido",
};

const bookList = document.querySelector("#bookList");
const totalBooks = document.querySelector("#totalBooks");
const doneBooks = document.querySelector("#doneBooks");
const progress = document.querySelector("#progress");
const refreshButton = document.querySelector("#refreshButton");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

function renderBooks(books) {
  bookList.innerHTML = "";
  books.forEach((book) => {
    const item = document.createElement("article");
    item.className = "book";
    item.innerHTML = `
      <div>
        <h3>${book.title}</h3>
        <p>${book.author}</p>
        <span class="status ${book.status}">${statusLabels[book.status]}</span>
      </div>
      <button type="button" data-book-id="${book.id}">Avancar</button>
    `;
    bookList.appendChild(item);
  });
}

function renderStats(stats) {
  totalBooks.textContent = stats.total;
  doneBooks.textContent = stats.done;
  progress.textContent = `${stats.progress_percent}%`;
}

async function loadDashboard() {
  const [books, stats] = await Promise.all([request("/api/books"), request("/api/stats")]);
  renderBooks(books);
  renderStats(stats);
}

bookList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-book-id]");
  if (!button) {
    return;
  }

  await request(`/api/books/${button.dataset.bookId}/toggle`, { method: "POST" });
  await loadDashboard();
});

refreshButton.addEventListener("click", loadDashboard);
loadDashboard().catch((error) => {
  bookList.innerHTML = `<p>${error.message}</p>`;
});

