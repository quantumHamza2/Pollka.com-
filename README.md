# Pollka.com

Pollka is a full-stack web application designed to manage and allocate resources efficiently. It provides an interactive interface for assigning, viewing, and clearing allocations with real-time updates.

---

## 🚀 Features

* 📊 Dynamic allocation system
* 🔄 Real-time updates via API
* 🧹 Clear all allocations functionality
* 🖥️ Interactive UI with modals and status indicators
* ⚡ Fast frontend powered by Vite + React
* 🗄️ Backend with Python and SQLite

---

## 🛠️ Tech Stack

### Frontend

* React (Vite)
* HTML, CSS, JavaScript

### Backend

* Python

### Database

* SQLite (`pollka.db`)

---

## 📁 Project Structure

```
SEPM PROJECT/
│
├── src/                # React frontend
├── public/             # Static assets
├── index.html          # Main HTML file
├── App.jsx             # Main React component
├── main.py             # Backend server
├── db_setup.py         # Database setup
├── seed_data.py        # Initial data population
├── pollka.db           # SQLite database
├── package.json        # Node dependencies
├── vite.config.js      # Vite configuration
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/quantumHamza2/Pollka.com-.git
cd Pollka.com-
```

---

### 2. Setup Backend

```bash
pip install -r requirements.txt
python db_setup.py
python seed_data.py
python main.py
```

---

### 3. Setup Frontend

```bash
npm install
npm run dev
```

---

### 4. Open in Browser

http://localhost:5173

---

## 🔌 API Endpoints

* `GET /allocations` → Fetch allocation data
* `POST /clear-allocations` → Clear all allocations

---

## 🧪 Future Enhancements

* 🔐 User authentication
* 📈 Data visualization (charts)
* 📤 Export data (CSV/PDF)
* 🌙 Dark mode
* 🔍 Filters and search

---

## 👨‍💻 Author

**Mohammad Hamza Khan**
CSE Student @ SRM IST KTR

---

## 📌 Notes

* Run backend before starting frontend
* Database (`pollka.db`) is created during setup
* Update API URLs if backend port changes

---

## ⭐ Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## 📄 License

This project is for academic use.
