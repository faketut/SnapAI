#!/bin/bash
# SnapAI Test Runner

echo "Setting up testing environment..."
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-qt

echo "Running SnapAI Comprehensive Test Suite..."
# Using -v for verbose output and -s to show prints if needed
python3 -m pytest tests/ -v

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All tests passed successfully!"
else
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi
