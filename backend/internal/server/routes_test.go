package server

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestPublicRoute(t *testing.T) {
	srv := NewServer(nil)
	router := srv.Routes()

	req := httptest.NewRequest(http.MethodGet, "/public", nil)
	rec := httptest.NewRecorder()

	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status %d, got %d", http.StatusOK, rec.Code)
	}

	expectedBody := "Anyone can see this public data"
	if rec.Body.String() != expectedBody {
		t.Errorf("expected body %q, got %q", expectedBody, rec.Body.String())
	}
}

func TestCORSPreflight(t *testing.T) {
	srv := NewServer(nil)
	router := srv.Routes()

	req := httptest.NewRequest(http.MethodOptions, "/public", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	req.Header.Set("Access-Control-Request-Method", "GET")

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status %d, got %d", http.StatusOK, rec.Code)
	}

	allowOrigin := rec.Header().Get("Access-Control-Allow-Origin")
	if allowOrigin != "http://localhost:3000" {
		t.Errorf("expected Access-Control-Allow-Origin header to be %q, got %q", "http://localhost:3000", allowOrigin)
	}
}

func TestProtectedRouteUnauthorizedWithoutToken(t *testing.T) {
	srv := NewServer(nil)
	router := srv.Routes()

	req := httptest.NewRequest(http.MethodGet, "/protected", nil)
	rec := httptest.NewRecorder()

	router.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Errorf("expected status %d for unauthenticated request, got %d", http.StatusUnauthorized, rec.Code)
	}
}
