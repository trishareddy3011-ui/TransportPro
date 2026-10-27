#!/bin/bash
set -e

echo "=================================================="
echo " Starting VahanOne Transport Operating System "
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH."
    echo ""
    echo "Please install Docker Desktop for your OS:"
    echo "  - Mac:   https://docs.docker.com/desktop/setup/install/mac-install/"
    echo "  - Linux: https://docs.docker.com/engine/install/"
    echo "  - Win:   https://docs.docker.com/desktop/setup/install/windows-install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running."
    echo "Please launch Docker Desktop and wait until the engine starts, then re-run this script."
    exit 1
fi

echo "==> Docker is active. Building and launching services..."
echo "==> This spins up PostgreSQL, FastAPI backend (auto-migrated & seeded), and Vite frontend."
echo ""

docker compose up --build -d

echo ""
echo "=================================================="
echo " VahanOne is successfully running! "
echo "=================================================="
echo " Frontend Website : http://localhost"
echo " Backend API Docs : http://localhost:8000/docs"
echo " Backend Health   : http://localhost:8000/"
echo ""
echo " Default Demo Credentials:"
echo "   Email    : admin@vahanone.com"
echo "   Password : AdminPassword123!"
echo "   Org ID   : 00000000-0000-0000-0000-000000000001"
echo ""
echo " To view service logs:"
echo "   docker compose logs -f"
echo ""
echo " To stop all services:"
echo "   docker compose down"
echo "=================================================="
