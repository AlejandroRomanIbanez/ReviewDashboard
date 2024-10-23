# Reviewer Dashboard - Setup Guide

This guide walks you through setting up both the **backend** (Flask/Selenium) and **frontend** (React) of the Reviewer Dashboard project.


## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/AlejandroRomanIbanez/ReviewDashboard.git
cd repo
```

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:

   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file** in the backend directory with the following variables:
   ```plaintext
   CODIO_USERNAME=your_username
   CODIO_PASSWORD=your_password
   ```

6. **Run the Flask app**:
   ```bash
   python app.py
   ```

7. The backend will be available at `http://localhost:5000`.

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. The frontend will be available at `http://localhost:5173`.

### 4. Running Both Backend and Frontend

Once you have both the backend and frontend running:

- The **backend** runs on `http://localhost:5000`
- The **frontend** runs on `http://localhost:5173`

You can use the frontend interface to interact with the backend by fetching assignments, selecting reviewers, and viewing their details.

Feel free to change the ports as need it

---

## Project Structure

```
.
├── backend/               # Backend Flask API
│   ├── app.py             # Main Flask app
│   ├── requirements.txt   # Python dependencies
│   ├── .env               # Environment variables (add your own)
│   └── data/              # Contains scraped data files
├── frontend/              # Frontend React app
│   ├── src/               # React components and logic
│   ├── public/            # Static files
│   ├── package.json       # npm dependencies
│   └── README.md          # Frontend readme
└── README.md              # Project Setup Guide
```

