# AlumDash 🎬

A modern, containerized web application for tracking and monitoring film and television achievements of alumni. Built with FastAPI, PostgreSQL, Docker, and featuring comprehensive CSV import capabilities.

![AlumDash](https://img.shields.io/badge/AlumDash-Alumni%20Achievement%20Tracker-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker)

## ✨ Features

- **🎓 Alumni Management**: Comprehensive tracking of graduate information including contact details and social media profiles
- **🏆 Achievement Tracking**: Monitor awards, film credits, festival selections, and industry recognition with AI-powered confidence scoring
- **🎥 Project Database**: Catalog of films, TV shows, and other productions with detailed metadata
- **📊 Interactive Dashboard**: Real-time statistics, visualizations, and analytics
- **📁 CSV Import System**: Robust bulk import with validation, error reporting, and detailed statistics
- **🔄 Data Source Monitoring**: Track API and web scraping sources for automated data collection
- **🐳 Docker Integration**: Fully containerized for consistent deployment across environments
- **📱 Responsive Design**: Modern web interface that works on desktop and mobile

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git for repository management

### Installation

1. **Clone the repository:**
   ```bash
   git clone [your-repository-url]
   cd alumdash
   ```

2. **Set up convenient Docker aliases (one-time setup):**
   ```bash
   echo -e "\n# AlumDash Docker Aliases\nalias alum-start='echo \"🚀 Starting AlumDash...\" && docker-compose up --build'\nalias alum-stop='echo \"🛑 Stopping AlumDash...\" && docker-compose down'\nalias alum-restart='echo \"🔄 Restarting...\" && docker-compose down && docker-compose up --build'\nalias alum-logs='echo \"📋 Showing logs...\" && docker-compose logs -f'" >> ~/.zshrc && source ~/.zshrc && echo "✅ AlumDash aliases ready!"
   ```

3. **Start AlumDash:**
   ```bash
   alum-start
   ```

4. **Access the application:**
   - 🌐 **Web Interface**: http://localhost:8000
   - 📚 **API Documentation**: http://localhost:8000/docs
   - 📖 **Alternative API Docs**: http://localhost:8000/redoc
   - ❤️ **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

### Technology Stack

- **Backend**: FastAPI (Python 3.11) with async/await support
- **Database**: PostgreSQL 15 with custom enums and constraints
- **Frontend**: Modern HTML5/CSS3/JavaScript with responsive design
- **Containerization**: Docker & Docker Compose for development and deployment
- **Data Processing**: Pandas for CSV import and validation
- **ORM**: SQLAlchemy with async support and automatic migrations

### Project Structure

```
alumdash/
├── 📄 main.py                    # FastAPI application and API endpoints
├── 📄 models.py                  # Pydantic data models (legacy compatibility)
├── 🌐 index.html                 # Modern web interface
├── 📋 requirements.txt           # Python dependencies
├── 🐳 Dockerfile                 # Container configuration
├── 🐳 docker-compose.yml         # Multi-service orchestration
├── 📊 database/
│   ├── 📄 __init__.py            # Package initialization
│   ├── 🔗 connection.py          # SQLAlchemy models and database connection
│   └── 🗃️ init.sql               # PostgreSQL schema and sample data
├── ⚙️ services/
│   ├── 📄 __init__.py            # Package initialization
│   └── 📥 csv_service.py         # CSV import and validation logic
├── 📊 sample_alumni_data.csv     # Sample data for testing (30 records)
├── 📖 README.md                  # This file
├── 🙈 .gitignore                 # Git ignore rules
└── 📚 CSV_Import_Guide.md        # Detailed CSV import documentation
```

## 💾 Database Schema

AlumDash uses PostgreSQL with a robust schema featuring:

### Core Tables
- **`alumni`** - Graduate information with privacy settings
- **`achievements`** - Awards, credits, and recognition with confidence scoring
- **`projects`** - Film/TV productions with metadata
- **`alumni_projects`** - Many-to-many relationships between alumni and projects
- **`import_logs`** - Complete audit trail of CSV imports

### Data Types
- **Custom Enums**: Degree programs, achievement types, project types
- **Constraints**: Email validation, URL validation, date ranges
- **Indexes**: Optimized for common queries and searches

## 📥 CSV Import System

### Supported Format

**Required Columns:**
- `name` - Alumni full name (max 100 characters)
- `graduation_year` - Year between 1970-2030
- `degree_program` - One of: Film Production, Screenwriting, Animation, Documentary, Television

**Optional Columns:**
- `email` - Valid email address
- `linkedin_url` - LinkedIn profile URL
- `imdb_url` - IMDb profile URL  
- `website` - Personal website URL

### Import Features

- ✅ **Real-time validation** with detailed error reporting
- 📊 **Import statistics** (successful/failed record counts)
- 🔍 **Duplicate detection** prevents importing the same alumni twice
- 📋 **Import history** with full audit logs
- 📁 **Template download** with sample data
- 🖱️ **Drag-and-drop interface** for easy file uploads

### Example CSV

```csv
name,graduation_year,degree_program,email,linkedin_url,imdb_url,website
John Smith,2020,Film Production,john@example.com,https://linkedin.com/in/johnsmith,https://imdb.com/name/nm123,https://johnfilms.com
Jane Doe,2021,Documentary,jane@example.com,,,
```

## 🐳 Docker Commands

### Development Workflow

```bash
# Start the application (builds containers, starts services)
alum-start

# Stop the application (stops and removes containers)
alum-stop

# Restart completely (stop, rebuild, start)
alum-restart

# View real-time logs
alum-logs

# Check container status
docker ps
```

### Advanced Operations

```bash
# Clean rebuild (no cache)
docker-compose build --no-cache && docker-compose up

# Reset database (removes all data)
alum-stop
docker volume rm alumdash_postgres_data
alum-start

# Access database directly
docker exec -it alumdash-db psql -U alumdash_user -d alumdash
```

## 🌐 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web interface |
| `GET` | `/health` | Health check |
| `GET` | `/api/alumni` | List all alumni |
| `POST` | `/api/alumni` | Create new alumni |
| `GET` | `/api/alumni/{id}` | Get specific alumni |
| `POST` | `/api/alumni/import-csv` | Import CSV file |
| `GET` | `/api/alumni/csv-template` | Download CSV template |
| `GET` | `/api/dashboard/stats` | Dashboard statistics |
| `GET` | `/api/import-history` | CSV import history |

### Example API Usage

```bash
# Get all alumni
curl http://localhost:8000/api/alumni

# Create new alumni
curl -X POST http://localhost:8000/api/alumni \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","graduation_year":2023,"degree_program":"Film Production"}'

# Health check
curl http://localhost:8000/health
```

## 🎯 Usage Guide

### Web Interface Navigation

1. **📊 Dashboard** - Overview statistics and recent achievements
2. **👥 Alumni** - Browse and search alumni directory  
3. **➕ Add Alumni** - Individual alumni creation form
4. **📥 Import CSV** - Bulk import with validation
5. **📋 Import History** - Audit trail of all imports

### CSV Import Workflow

1. **Download template** from the Import CSV section
2. **Prepare your data** following the format requirements
3. **Upload CSV file** via drag-and-drop or file selection
4. **Review results** with detailed statistics and error reports
5. **Check import history** for audit trail

## 🔧 Development

### Local Development (Alternative to Docker)

If you prefer traditional Python development:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set database URL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/alumdash"

# Run application
python main.py
```

### Adding New Features

1. **Database Models**: Add to `database/connection.py`
2. **API Endpoints**: Extend `main.py`
3. **Import Logic**: Modify `services/csv_service.py`
4. **Frontend**: Update `index.html`

## 🚀 Production Deployment

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
ENV=production
```

### Production Considerations

- Use external PostgreSQL database
- Implement SSL/HTTPS
- Add authentication and authorization
- Configure logging and monitoring
- Set up automated backups
- Use production WSGI server (Gunicorn)

## 🛠️ Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check Docker is running
docker --version

# View detailed logs
alum-logs

# Clean restart
alum-stop && alum-start
```

**Database connection issues:**
```bash
# Check database health
curl http://localhost:8000/health

# Reset database
docker volume rm alumdash_postgres_data
alum-restart
```

**CSV import fails:**
- Verify column names match exactly
- Check data format requirements
- Review error messages in import results
- Ensure degree programs use exact values

### Performance Tips

- Use Docker's layer caching for faster builds
- Monitor database connection pool
- Optimize CSV file size (recommend <10MB)
- Use database indexes for large datasets

## 📊 Sample Data

The application includes:
- **5 sample alumni** in the database initialization
- **30 diverse alumni** in `sample_alumni_data.csv`
- **Multiple degree programs** represented
- **Realistic data** with varying completeness

Test the CSV import using the included sample file!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with sample data
5. Submit a pull request

## 📄 License

This project is copyright A Helme and is a private application.

## 🆘 Support

For questions or issues:
- Check the troubleshooting section above
- Review Docker logs with `alum-logs`
- Test with the sample CSV data
- Contact: http://annahelme.com/contact

---

**Built with ❤️ using modern Python, PostgreSQL, and Docker technologies.**

---

### 🎉 Quick Commands Reference

```bash
# Essential commands
alum-start     # Start everything
alum-stop      # Stop everything  
alum-restart   # Complete restart
alum-logs      # View logs

# URLs
http://localhost:8000           # Main app
http://localhost:8000/docs      # API docs
http://localhost:8000/health    # Health check
```
