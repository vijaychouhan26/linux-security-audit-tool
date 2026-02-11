#!/bin/bash
# Linux Security Audit Tool - Complete System Runner

set -e

echo "=================================================="
echo "Linux Security Audit Tool - Complete System"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the project directory
if [ ! -f "audit_api.py" ] && [ ! -f "frontend/dashboard.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Function to start backend API
start_backend() {
    echo -e "${BLUE}Starting Backend API...${NC}"
    
    if check_port 5000; then
        echo -e "${YELLOW}Port 5000 already in use${NC}"
        read -p "Kill existing process? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill_port 5000
        else
            echo -e "${YELLOW}Using existing backend on port 5000${NC}"
            return
        fi
    fi
    
    if [ -f "audit_api.py" ]; then
        python3 audit_api.py > backend.log 2>&1 &
        BACKEND_PID=$!
        echo -e "${GREEN}Backend API started (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}Error: audit_api.py not found${NC}"
        exit 1
    fi
    
    # Wait for backend to start
    echo -e "${BLUE}Waiting for backend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5000/health >/dev/null 2>&1; then
            echo -e "${GREEN}Backend API is ready${NC}"
            return
        fi
        sleep 1
    done
    
    echo -e "${RED}Backend failed to start${NC}"
    cat backend.log
    exit 1
}

# Function to start frontend dashboard
start_frontend() {
    echo -e "${BLUE}Starting Frontend Dashboard...${NC}"
    
    if check_port 8080; then
        echo -e "${YELLOW}Port 8080 already in use${NC}"
        read -p "Kill existing process? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill_port 8080
        else
            echo -e "${YELLOW}Using existing frontend on port 8080${NC}"
            return
        fi
    fi
    
    if [ -f "frontend/dashboard.py" ]; then
        cd frontend
        python3 dashboard.py > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        echo -e "${GREEN}Frontend Dashboard started (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${RED}Error: frontend/dashboard.py not found${NC}"
        exit 1
    fi
    
    # Wait for frontend to start
    echo -e "${BLUE}Waiting for frontend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8080/ >/dev/null 2>&1; then
            echo -e "${GREEN}Frontend Dashboard is ready${NC}"
            return
        fi
        sleep 1
    done
    
    echo -e "${RED}Frontend failed to start${NC}"
    cat frontend.log
    exit 1
}

# Function to install dependencies
install_deps() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    
    # Backend dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Frontend dependencies
    if [ -f "frontend/requirements.txt" ]; then
        pip install -r frontend/requirements.txt
    fi
    
    # Install Flask and flask-cors if not present
    python3 -c "import flask" 2>/dev/null || pip install Flask flask-cors
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${GREEN}System Status${NC}"
    echo -e "${BLUE}==================================================${NC}"
    
    # Check backend
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend API: http://localhost:5000${NC}"
    else
        echo -e "${RED}✗ Backend API: Not running${NC}"
    fi
    
    # Check frontend
    if curl -s http://localhost:8080/ >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend Dashboard: http://localhost:8080${NC}"
    else
        echo -e "${RED}✗ Frontend Dashboard: Not running${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Useful URLs:${NC}"
    echo -e "  Dashboard:    ${BLUE}http://localhost:8080/${NC}"
    echo -e "  API Docs:     ${BLUE}http://localhost:5000/${NC}"
    echo -e "  API Health:   ${BLUE}http://localhost:5000/health${NC}"
    echo ""
    echo -e "${YELLOW}Log files:${NC}"
    echo -e "  Backend:      backend.log"
    echo -e "  Frontend:     frontend.log"
    echo ""
    echo -e "${YELLOW}To stop both services, press Ctrl+C${NC}"
}

# Function to clean up on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Main execution
main() {
    echo -e "${BLUE}Linux Security Audit Tool - Starting Complete System${NC}"
    echo ""
    
    # Install dependencies if requested
    read -p "Install dependencies? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_deps
    fi
    
    # Start services
    start_backend
    start_frontend
    
    # Show status
    show_status
    
    # Keep script running
    echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
    wait
}

# Run main function
main
