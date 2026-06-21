# Pollka.com

Pollka.com is a full-stack polling and allocation platform. It features a general-purpose polling system supporting user registration, poll creation, single/multiple-choice voting, and live results visualization. Additionally, the platform integrates an academic elective subject allocation engine that assigns elective courses to students based on their ranked preferences and CGPA standings.

---

## Features

### Polling Engine
* **User Management**: Public registration and login system with roles for general users and administrators.
* **Poll Creation**: Dashboard to create custom single-choice or multiple-choice polls with dynamic option additions.
* **Dynamic Voting**: Real-time voting with duplicate vote prevention.
* **Live Visualizations**: Live-updating results charts displaying vote counts, percentage breakdowns, and winner highlights.
* **Poll Control**: Creators can close, reopen, or delete their polls dynamically.

### Elective Allocation Engine
* **Ranked Preferences**: Students can select and rank elective subjects using a drag-and-drop user interface.
* **CGPA-Based Allocation**: Executes a deterministic matching algorithm prioritizing students with higher CGPAs.
* **Admin Control Panel**: Administrators can toggle polling availability, execute the allocation algorithm, reset allocations, and monitor statistics.

---

## Technical Architecture

The platform uses a decoupled client-server architecture:

* **Frontend Client**: A single-page application built using HTML5, CSS3, and modern vanilla JavaScript. It uses native APIs for asynchronous requests (Fetch) and DOM manipulation, eliminating external framework overhead.
* **Backend Server**: Powered by Python and FastAPI, providing a high-performance, asynchronous REST API.
* **Database Layer**: SQLite relational database using the Python standard library `sqlite3` driver with foreign key constraints enabled.

---

## Database Schema

The database schema (`pollka.db`) is structured around the following relational tables:

### users
Stores user accounts for both students and administrators.
* `id` (INTEGER, Primary Key)
* `username` (TEXT, Unique, Not Null)
* `password` (TEXT, Not Null)
* `display_name` (TEXT, Not Null)
* `email` (TEXT)
* `role` (TEXT, Default 'user') - Controls access to administrative endpoints.
* `cgpa` (REAL) - Optional, used by the elective allocation engine.

### polls
Tracks user-created polls.
* `id` (INTEGER, Primary Key)
* `title` (TEXT, Not Null)
* `description` (TEXT)
* `poll_type` (TEXT, Default 'single') - Can be 'single' or 'multiple'.
* `created_by` (INTEGER, Foreign Key references users)
* `is_active` (INTEGER, Default 1) - Boolean flag representing open (1) or closed (0) status.

### poll_options
Stores individual options for each poll.
* `id` (INTEGER, Primary Key)
* `poll_id` (INTEGER, Foreign Key references polls on delete cascade)
* `option_text` (TEXT, Not Null)

### votes
Records votes cast by users on options.
* `id` (INTEGER, Primary Key)
* `poll_id` (INTEGER, Foreign Key references polls on delete cascade)
* `option_id` (INTEGER, Foreign Key references poll_options on delete cascade)
* `user_id` (INTEGER, Foreign Key references users on delete cascade)

### subjects
Academic subjects available for elective allocation.
* `id` (INTEGER, Primary Key)
* `name` (TEXT, Unique, Not Null)
* `total_seats` (INTEGER, Not Null)

### preferences
Students' ranked preferences for subjects.
* `id` (INTEGER, Primary Key)
* `student_id` (INTEGER, Foreign Key references users on delete cascade)
* `subject_id` (INTEGER, Foreign Key references subjects on delete cascade)
* `preference_order` (INTEGER, Not Null)

### allocations
Stores final subject assignments after the allocation algorithm runs.
* `student_id` (INTEGER, Primary Key, Foreign Key references users on delete cascade)
* `subject_id` (INTEGER, Foreign Key references subjects on delete cascade)

### settings
Stores global configurations.
* `key` (TEXT, Primary Key)
* `value` (TEXT, Not Null)

---

## API Reference

### Authentication Endpoints

#### POST /register
Creates a new user account.
* **Request Body**:
  ```json
  {
    "username": "johndoe",
    "password": "securepassword",
    "display_name": "John Doe",
    "email": "john@example.com"
  }
  ```

#### POST /login
Authenticates a user.
* **Request Body**:
  ```json
  {
    "username": "johndoe",
    "password": "securepassword"
  }
  ```
* **Response**:
  ```json
  {
    "status": "success",
    "id": 1,
    "name": "John Doe",
    "role": "user",
    "cgpa": null,
    "email": "john@example.com"
  }
  ```

### Polling Endpoints

#### GET /polls
Fetches a list of all active and closed polls along with total vote counts.

#### GET /polls/{id}
Retrieves detailed information about a specific poll including options and current vote statistics.

#### POST /polls
Creates a new poll.
* **Request Body**:
  ```json
  {
    "title": "Favorite Framework?",
    "description": "Select your primary backend framework.",
    "poll_type": "single",
    "options": ["FastAPI", "Express", "Django", "Spring Boot"]
  }
  ```

#### POST /polls/{id}/vote
Casts votes for one or more options in a poll.
* **Request Body**:
  ```json
  {
    "user_id": 1,
    "option_ids": [12]
  }
  ```

#### POST /polls/{id}/close
Closes a poll to stop accepting new votes. Authorized for the poll creator or administrators.

#### POST /polls/{id}/reopen
Reopens a closed poll. Authorized for the poll creator or administrators.

#### DELETE /polls/{id}
Deletes a poll. Authorized for the poll creator or administrators.

#### GET /polls/{id}/my-vote/{user_id}
Fetches option IDs that the specified user has voted for in the poll.

#### GET /my-polls/{user_id}
Fetches all polls created by a specific user.

### Elective Allocation Endpoints

#### GET /subjects
Returns all available subjects with total seats and remaining seats.

#### POST /subjects
Adds a new subject. (Admin only)

#### PUT /subjects/{id}
Edits a subject's name and capacity. (Admin only)

#### DELETE /subjects/{id}
Deletes a subject. (Admin only)

#### GET /preferences/{student_id}
Fetches the ranked preferences for a student.

#### POST /preferences
Saves a ranked list of subject IDs for a student.

#### GET /polling-status
Gets the current global availability status of the preference submission portal.

#### POST /polling-status
Toggles the global preference submission availability. (Admin only)

#### POST /allocate
Executes the CGPA-based elective allocation algorithm. (Admin only)

#### GET /results
Retrieves the list of students with their allocated subjects.

#### POST /clear-allocations
Clears all current allocations and resets seat metrics. (Admin only)

#### GET /stats
Retrieves statistical summaries of allocations. (Admin only)

---

## Installation & Local Setup

### Prerequisites
* Python 3.8 or higher installed on your system.

### 1. Configure the Backend Database
Navigate to the project root directory and run the initialization scripts to create the SQLite database file and seed initial mock data (users, preferences, sample polls, and sample votes):

```bash
# Create tables
python3 db_setup.py

# Seed mock data
python3 seed_data.py
```

### 2. Install Dependencies & Start Backend Server
Install FastAPI and Uvicorn packages, then start the development server:

```bash
# Install required packages
pip install fastapi uvicorn

# Start the uvicorn development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
The server will start listening on `http://127.0.0.1:8000`.

### 3. Open the Frontend Application
Since the frontend client is a vanilla single-page application, you do not need to run a Node server. Simply open `index.html` directly in any web browser:

```bash
# On macOS
open index.html

# On Windows
start index.html

# On Linux
xdg-open index.html
```

---

## Allocation Algorithm Detail

The elective allocation engine executes the following logic:
1. Gathers all student records that have submitted subject preferences.
2. Sorts the student queue in descending order of CGPA.
3. Iterates through the sorted queue:
   * Examines the student's preferences in rank order (first choice, second choice, etc.).
   * Checks if the preferred subject has available seats.
   * Allocates the subject if a seat is available and updates seat counts.
   * If all preferred subjects are full, the student remains unallocated.

This design ensures merit-based assignment of limited elective positions.
