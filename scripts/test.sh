#!/bin/bash

# Test runner script for PRIMS
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
PARALLEL=false

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE       Test type: unit, integration, all (default: all)"
    echo "  -c, --no-coverage     Disable coverage reporting"
    echo "  -v, --verbose         Enable verbose output"
    echo "  -p, --parallel        Run tests in parallel"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests with coverage"
    echo "  $0 -t unit           # Run only unit tests"
    echo "  $0 -t integration -c # Run integration tests without coverage"
    echo "  $0 -v -p             # Run all tests verbosely in parallel"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate test type
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|all)$ ]]; then
    echo -e "${RED}Error: Invalid test type '$TEST_TYPE'. Must be 'unit', 'integration', or 'all'${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [[ -f ".venv/bin/activate" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add test directories based on type
case $TEST_TYPE in
    unit)
        PYTEST_CMD="$PYTEST_CMD tests/unit/"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD tests/integration/"
        ;;
    all)
        PYTEST_CMD="$PYTEST_CMD tests/"
        ;;
esac

# Add coverage options
if [[ "$COVERAGE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=server --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml"
fi

# Add verbose option
if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel option
if [[ "$PARALLEL" == "true" ]]; then
    # Check if pytest-xdist is installed
    if python -c "import xdist" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
    else
        echo -e "${YELLOW}Warning: pytest-xdist not installed. Running tests sequentially.${NC}"
    fi
fi

echo -e "${GREEN}Running $TEST_TYPE tests...${NC}"
echo -e "${YELLOW}Command: $PYTEST_CMD${NC}"
echo ""

# Run the tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ Tests completed successfully!${NC}"
    
    # Show coverage report location if coverage was enabled
    if [[ "$COVERAGE" == "true" ]]; then
        echo -e "${YELLOW}📊 Coverage report available at: htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi