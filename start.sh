#!/bin/bash
# 一食万象 Demo - 一键启动脚本

echo "=============================="
echo "  一食万象 - One Bite One World"
echo "=============================="

# Start backend
echo "Starting backend..."
cd "$(dirname "$0")/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend started on http://localhost:8000 (PID: $BACKEND_PID)"

# Wait for backend to be ready
sleep 2

# Start frontend
echo "Starting frontend..."
cd "$(dirname "$0")/frontend"
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
echo "Frontend started on http://localhost:5173 (PID: $FRONTEND_PID)"

echo ""
echo "=============================="
echo "  Demo running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "=============================="
echo "Press Ctrl+C to stop"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
