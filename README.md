# Dream11 Team Predictor

A machine learning-based application to predict the best possible Dream11 teams for IPL cricket matches.

## Project Structure

The project is divided into two main parts:

### Frontend (React.js)

Located in `/frontend/dream11-frontend/`, this is a React.js application that provides the user interface for the Dream11 Team Predictor.

- **Key Features:**
  - Team selection interface
  - Player statistics visualization
  - Dream11 team prediction results display
  - User authentication
  - History of previous predictions

- **Tech Stack:**
  - React.js with hooks
  - React Router for navigation
  - Chart.js for data visualization
  - Axios for API communication
  - TailwindCSS for styling

### Backend (Django)

Located in `/backend/`, this is a Django application that provides the API for the Dream11 Team Predictor.

- **Key Features:**
  - REST API for team prediction
  - Player statistics processing
  - User authentication
  - Prediction history storage

- **Tech Stack:**
  - Django for the web framework
  - Django REST Framework for API endpoints
  - JWT authentication for secure API access
  - pandas and numpy for data processing

## Data Pipeline

The data pipeline is responsible for collecting and processing IPL cricket data, which is then used to make predictions.

1. **Data Sources:**
   - IPL auction data (`ipl data - auction_2025.csv`)
   - IPL match results (`ipl data - match_results.csv`)
   - Player batting statistics (`ipl data - most_runs.csv`)
   - Player bowling statistics (`ipl data - most_wickets.csv`)
   - Fielding statistics (`ipl data - most_catches.csv`, `ipl data - most_dismissals.csv`)

2. **Data Processing:**
   - Clean and normalize data
   - Calculate player performance metrics
   - Identify player roles (batsman, bowler, all-rounder, wicket-keeper)
   - Assign points based on performance

3. **Prediction Algorithm:**
   - Uses a greedy approach with constraints
   - Considers player form, historical performance, and cost
   - Ensures team composition meets Dream11 rules
   - Maximizes expected points while staying within budget

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- PostgreSQL (optional, can use SQLite for development)

### Backend Setup

1. Clone the repository
```
git clone https://github.com/yourusername/dream11-team-predictor.git
cd dream11-team-predictor
```

2. Create and activate a virtual environment
```
cd backend
python -m venv env
source env/bin/activate  # On Windows, use: .\env\Scripts\Activate.ps1
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Run migrations
```
python manage.py migrate
```

5. Start the development server
```
python manage.py runserver
```

### Frontend Setup

1. Install dependencies
```
cd frontend/dream11-frontend
npm install
```

2. Start the development server
```
npm start
```

3. Build for production
```
npm run build
```

## Usage

1. Register a new account or login with existing credentials
2. Select two IPL teams from the dropdown
3. Set your budget (default is 100 credits)
4. Click "Predict Team" to get your Dream11 team prediction
5. View detailed statistics and breakdown of the predicted team
6. Save or share your prediction

## API Endpoints

- `GET /api/predictor/teams/`: Get all teams
- `GET /api/predictor/team_players/?team=<team_name>`: Get players for a team
- `POST /api/predictor/predict_team/`: Predict a Dream11 team
  - Required parameters: `team1`, `team2`
  - Optional parameters: `budget`, `team_size`
- `GET /api/predictor/player_details/?player=<player_name>`: Get detailed statistics for a player

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- IPL and Dream11 for the inspiration
- All contributors who have helped build this project
