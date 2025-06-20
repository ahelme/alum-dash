# AlumDash: an Alumni Achievement Tracking System

A web application for tracking and monitoring film and television achievements of alumni.

## Features

- **Alumni Management**: Track graduate information including contact details and social media profiles
- **Achievement Tracking**: Monitor awards, film credits, festival selections, and industry recognition
- **Project Database**: Catalog of films, TV shows, and other productions
- **Data Source Monitoring**: Track API and web scraping sources
- **Interactive Dashboard**: Real-time statistics and visualizations
- **Confidence Scoring**: AI-powered verification of achievements

## Project Structure

```
vca-alumni-tracker/
├── main.py              # FastAPI application and API endpoints
├── models.py            # Pydantic data models and validation
├── database.py          # Mock database and helper functions
├── index.html           # Web interface
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Create a project directory and download all files:**
   ```bash
   mkdir vca-alumni-tracker
   cd vca-alumni-tracker
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative API Docs: http://localhost:8000/redoc

## Usage

### Web Interface

1. **Dashboard**: View overall statistics and recent achievements
2. **Alumni**: Browse and add alumni records
3. **Achievements**: Track all achievements with confidence scores
4. **Projects**: View film and TV productions
5. **Data Sources**: Monitor API and scraping sources
6. **Add Alumni**: Form to add new graduates

### API Endpoints

- `GET /api/alumni` - List all alumni
- `POST /api/alumni` - Create new alumni record
- `GET /api/achievements` - List all achievements
- `POST /api/achievements` - Create new achievement
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/data-sources` - List data sources
- `GET /api/projects` - List all projects

## Data Models

### Alumni
- Name, graduation year, degree program
- Contact information (email, LinkedIn, IMDb, website)
- Privacy settings

### Achievement
- Type (Award, Production Credit, Festival Selection, etc.)
- Title, date, description
- Confidence score (0-1)
- Verification status
- Source information

### Project
- Film/TV production details
- Release date, runtime
- Streaming platforms
- External IDs (IMDb, TMDb)

## Mock Data

The application includes sample data for demonstration:
- 5 alumni profiles
- 7 achievements
- 4 projects
- 5 data sources

## Development

### Adding New Features

1. **Models**: Define new Pydantic models in `models.py`
2. **Database**: Add mock data and helper functions in `database.py`
3. **API**: Create endpoints in `main.py`
4. **UI**: Update the interface in `index.html`

### Extending to Production

To deploy this application in production:

1. Replace mock database with PostgreSQL
2. Implement actual API integrations (TMDb, OMDb)
3. Add authentication and authorization
4. Set up n8n workflows for automated data collection
5. Deploy using Docker or cloud services

## Security Considerations

- Add authentication before deployment
- Implement rate limiting for API endpoints
- Secure API keys and credentials
- Follow GDPR/privacy regulations for alumni data

## Support

For questions or issues related to Alum Dash, please contact A Helme here: http://annahelme.com/contact

## License

This project is copyright A Helme and is a private application at this time.

---

**Note**: This is a prototype application with mock data. For production use, implement proper database connections and API integrations as outlined in the system design document.
