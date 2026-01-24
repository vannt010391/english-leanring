#!/bin/bash

# Manual Login Flow Test Script
# This script tests the complete login workflow

echo "==================================="
echo "VocabMaster Login Flow Test"
echo "==================================="
echo ""

BASE_URL="https://english.iamstudying.tech"

echo "1. Testing Login Page Access..."
LOGIN_PAGE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/login/")
if [ "$LOGIN_PAGE" = "200" ]; then
    echo "   ✓ Login page is accessible (HTTP 200)"
else
    echo "   ✗ Login page failed (HTTP $LOGIN_PAGE)"
fi
echo ""

echo "2. Testing Dashboard Redirect (Not Logged In)..."
DASHBOARD_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/dashboard/")
if [ "$DASHBOARD_REDIRECT" = "302" ]; then
    echo "   ✓ Dashboard correctly redirects when not logged in (HTTP 302)"
else
    echo "   ✗ Dashboard should redirect but got HTTP $DASHBOARD_REDIRECT"
fi
echo ""

echo "3. Testing API Login with Valid Credentials..."
# Create a temporary cookie jar
COOKIE_JAR=$(mktemp)

# Get CSRF token first
CSRF_TOKEN=$(curl -s -c "$COOKIE_JAR" "$BASE_URL/login/" | grep -oP 'csrfmiddlewaretoken.*?value="\K[^"]+' | head -1)

if [ -z "$CSRF_TOKEN" ]; then
    echo "   ! Warning: Could not extract CSRF token from page"
    # Try to get it from cookie
    CSRF_TOKEN=$(grep csrftoken "$COOKIE_JAR" | awk '{print $7}')
fi

# Perform login
LOGIN_RESPONSE=$(curl -s -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -d '{"username":"vannt","password":"Abcd@1234"}' \
    "$BASE_URL/api/auth/login/")

if echo "$LOGIN_RESPONSE" | grep -q '"token"'; then
    echo "   ✓ API login successful, token received"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -oP '"token":"\K[^"]+')
    echo "   Token: ${TOKEN:0:20}..."
else
    echo "   ✗ API login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi
echo ""

echo "4. Testing Dashboard Access After Login..."
DASHBOARD_AFTER=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" "$BASE_URL/dashboard/")
if [ "$DASHBOARD_AFTER" = "200" ]; then
    echo "   ✓ Dashboard is accessible after login (HTTP 200)"
else
    echo "   ✗ Dashboard access failed after login (HTTP $DASHBOARD_AFTER)"
fi
echo ""

echo "5. Testing Session Cookie..."
if grep -q "sessionid" "$COOKIE_JAR"; then
    echo "   ✓ Session cookie is set"
else
    echo "   ✗ Session cookie is NOT set"
fi
echo ""

echo "6. Testing CSRF Cookie..."
if grep -q "csrftoken" "$COOKIE_JAR"; then
    echo "   ✓ CSRF cookie is set"
else
    echo "   ✗ CSRF cookie is NOT set"
fi
echo ""

# Cleanup
rm "$COOKIE_JAR"

echo "==================================="
echo "Test Complete"
echo "==================================="
