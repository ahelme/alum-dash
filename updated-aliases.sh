# =============================================================================
# AlumDash Docker aliases - Updated for Multi-Architecture Support
# Updated on 20 June 2025 - Now supports both ARM64 and AMD64
# =============================================================================

# Detect architecture and set compose command
if [[ $(uname -m) == "arm64" ]]; then
    ALUM_COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.arm64.yml"
    ALUM_ARCH_MSG="(ARM64/Apple Silicon)"
else
    ALUM_COMPOSE_CMD="docker-compose"
    ALUM_ARCH_MSG="(AMD64/Intel)"
fi

# Start the Alumni Tracker application (builds and runs containers)
alias alum-start="echo \"🚀 Starting AlumDash Alumni Tracker $ALUM_ARCH_MSG...\" && $ALUM_COMPOSE_CMD up --build"

# Stop the Alumni Tracker application (stops and removes containers)
alias alum-stop="echo \"🛑 Stopping AlumDash Alumni Tracker...\" && $ALUM_COMPOSE_CMD down"

# Restart the application completely (stop, rebuild, start)
alias alum-restart="echo \"🔄 Restarting AlumDash Alumni Tracker $ALUM_ARCH_MSG...\" && $ALUM_COMPOSE_CMD down && $ALUM_COMPOSE_CMD up --build"

# View real-time application logs
alias alum-logs="echo \"📋 Showing AlumDash Alumni Tracker logs...\" && $ALUM_COMPOSE_CMD logs -f"

# Check container status and health
alias alum-status='echo "📊 AlumDash Alumni Tracker Status:" && docker ps --filter "name=alumdash" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Clean rebuild (no cache) - useful for troubleshooting
alias alum-rebuild="echo \"🔨 Clean rebuild of AlumDash Alumni Tracker $ALUM_ARCH_MSG...\" && $ALUM_COMPOSE_CMD build --no-cache && $ALUM_COMPOSE_CMD up"

# Quick development mode (just bring up, no rebuild)
alias alum-dev="echo \"⚡ Quick start AlumDash Alumni Tracker $ALUM_ARCH_MSG...\" && $ALUM_COMPOSE_CMD up"

# Remove all Alum Dash containers and images (complete cleanup)
alias alum-clean="echo \"🧹 Cleaning up AlumDash Alumni Tracker containers...\" && $ALUM_COMPOSE_CMD down -v --rmi all --remove-orphans"

# Architecture-specific aliases for manual override
alias alum-start-arm64='echo "🚀 Starting AlumDash (ARM64 forced)..." && docker-compose -f docker-compose.yml -f docker-compose.arm64.yml up --build'
alias alum-start-amd64='echo "🚀 Starting AlumDash (AMD64 forced)..." && docker-compose up --build'

# Show current architecture and compose command
alias alum-info="echo \"AlumDash Environment Info:\" && echo \"Architecture: $(uname -m)\" && echo \"Compose Command: $ALUM_COMPOSE_CMD\" && echo \"Container Filter: alumdash\""