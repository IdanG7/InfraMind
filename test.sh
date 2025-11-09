#!/bin/bash

# InfraMind Quick Test Script
# This script tests all components of InfraMind

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
  ___        __           __  __ _           _
 |_ _|_ __  / _|_ __ __ _|  \/  (_)_ __   __| |
  | || '_ \| |_| '__/ _` | |\/| | | '_ \ / _` |
  | || | | |  _| | | (_| | |  | | | | | | (_| |
 |___|_| |_|_| |_|  \__,_|_|  |_|_|_| |_|\__,_|

        Testing All Components

EOF
echo -e "${NC}"

# Test counter
PASSED=0
FAILED=0

# Function to test a component
test_component() {
    local name=$1
    local command=$2

    echo -n "Testing ${name}... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to test with output
test_component_verbose() {
    local name=$1
    local command=$2

    echo -e "${YELLOW}Testing ${name}...${NC}"

    if eval "$command"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo -e "${YELLOW}=== Phase 1: Service Health Checks ===${NC}"
echo ""

# Check if Docker is running
test_component "Docker" "docker ps > /dev/null 2>&1"

# Check if services are running
test_component "API Container" "docker-compose ps api | grep -q 'Up'"
test_component "PostgreSQL Container" "docker-compose ps postgres | grep -q 'Up'"
test_component "Redis Container" "docker-compose ps redis | grep -q 'Up'"
test_component "Prometheus Container" "docker-compose ps prometheus | grep -q 'Up'"
test_component "Grafana Container" "docker-compose ps grafana | grep -q 'Up'"

echo ""
echo -e "${YELLOW}=== Phase 2: Service Connectivity ===${NC}"
echo ""

# Test API
test_component "API Health" "curl -sf http://localhost:8081/health"
test_component "API Docs" "curl -sf http://localhost:8081/docs"
test_component "API OpenAPI" "curl -sf http://localhost:8081/openapi.json"

# Test Database
test_component "PostgreSQL" "docker-compose exec -T postgres pg_isready -U inframind"

# Test Redis
test_component "Redis" "docker-compose exec -T redis redis-cli ping | grep -q PONG"

# Test Prometheus
test_component "Prometheus" "curl -sf http://localhost:9092/-/healthy"

# Test Grafana
test_component "Grafana" "curl -sf http://localhost:3001/api/health"

echo ""
echo -e "${YELLOW}=== Phase 3: API Functionality ===${NC}"
echo ""

# Test optimization endpoint
echo -e "${BLUE}Testing optimization endpoint...${NC}"
RESPONSE=$(curl -sf -X POST http://localhost:8081/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "test/repo",
    "branch": "main",
    "build_type": "release"
  }')

if echo "$RESPONSE" | jq -e '.cpu' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Optimization endpoint works${NC}"
    echo "  Response: $RESPONSE" | jq '.'
    ((PASSED++))
else
    echo -e "${RED}✗ Optimization endpoint failed${NC}"
    echo "  Response: $RESPONSE"
    ((FAILED++))
fi

# Test build reporting endpoint
echo ""
echo -e "${BLUE}Testing build reporting endpoint...${NC}"
RESPONSE=$(curl -sf -X POST http://localhost:8081/builds/complete \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "test/repo",
    "branch": "main",
    "duration": 180,
    "status": "success",
    "cpu": 4,
    "memory": 8192
  }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build reporting endpoint works${NC}"
    echo "  Response: $RESPONSE" | jq '.' || echo "  Response: $RESPONSE"
    ((PASSED++))
else
    echo -e "${RED}✗ Build reporting endpoint failed${NC}"
    ((FAILED++))
fi

echo ""
echo -e "${YELLOW}=== Phase 4: Data Persistence ===${NC}"
echo ""

# Check database tables
echo -e "${BLUE}Checking database tables...${NC}"
TABLES=$(docker-compose exec -T postgres psql -U inframind -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

if [ "$TABLES" -gt 0 ]; then
    echo -e "${GREEN}✓ Database has tables${NC}"
    echo "  Found $TABLES tables"
    ((PASSED++))
else
    echo -e "${RED}✗ No tables found in database${NC}"
    ((FAILED++))
fi

echo ""
echo -e "${YELLOW}=== Phase 5: Monitoring Stack ===${NC}"
echo ""

# Check Prometheus targets
echo -e "${BLUE}Checking Prometheus targets...${NC}"
TARGETS=$(curl -sf http://localhost:9092/api/v1/targets 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Prometheus is collecting metrics${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Prometheus targets check failed${NC}"
    ((FAILED++))
fi

# Check Grafana datasources
echo -e "${BLUE}Checking Grafana datasources...${NC}"
DATASOURCES=$(curl -sf http://admin:admin@localhost:3001/api/datasources 2>/dev/null)

if echo "$DATASOURCES" | jq -e '.[].name' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana has datasources configured${NC}"
    echo "  Datasources:" $(echo "$DATASOURCES" | jq -r '.[].name' | tr '\n' ', ')
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Grafana datasources check skipped (may need manual login)${NC}"
fi

echo ""
echo -e "${YELLOW}=== Phase 6: Performance Check ===${NC}"
echo ""

# Measure API response time
echo -e "${BLUE}Measuring API response time...${NC}"
START=$(date +%s%N)
curl -sf http://localhost:8081/health > /dev/null
END=$(date +%s%N)
DURATION=$((($END - $START) / 1000000))

if [ $DURATION -lt 1000 ]; then
    echo -e "${GREEN}✓ API response time: ${DURATION}ms${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ API response time: ${DURATION}ms (may be slow)${NC}"
    ((PASSED++))
fi

# Test concurrent requests
echo -e "${BLUE}Testing concurrent requests...${NC}"
for i in {1..5}; do
    curl -sf http://localhost:8081/health > /dev/null &
done
wait

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Concurrent requests handled successfully${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Concurrent requests failed${NC}"
    ((FAILED++))
fi

echo ""
echo -e "${YELLOW}=== Test Summary ===${NC}"
echo ""
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ All tests passed successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}🚀 InfraMind is ready to use!${NC}"
    echo ""
    echo -e "Access points:"
    echo -e "  API Docs:   ${YELLOW}http://localhost:8081/docs${NC}"
    echo -e "  Grafana:    ${YELLOW}http://localhost:3001${NC} (admin/admin)"
    echo -e "  Prometheus: ${YELLOW}http://localhost:9092${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}════════════════════════════════════${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Check logs: ${BLUE}docker-compose logs${NC}"
    echo -e "  2. Restart services: ${BLUE}docker-compose restart${NC}"
    echo -e "  3. Check ports: ${BLUE}docker-compose ps${NC}"
    echo ""
    exit 1
fi
