package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/m1kus3q/pubpredictor/backend/internal/auth"
)

type contextKey string

const UserContextKey contextKey = "user"

func Auth(authenticator *auth.Authenticator) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				http.Error(w, "Unauthorized: missing token", http.StatusUnauthorized)
				return
			}

			// We expect the Authorization header to be formatted exactly as "Bearer <token>".
			// We split the string by space to isolate the actual JWT token from the prefix.
			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				http.Error(w, "Unauthorized: invalid header format", http.StatusUnauthorized)
				return
			}

			token, err := authenticator.VerifyToken(r.Context(), parts[1])
			if err != nil {
				http.Error(w, "Unauthorized: invalid token", http.StatusUnauthorized)
				return
			}

			// We store the verified token inside the request context.
			// This makes user data accessible down the chain in individual route handlers.
			ctx := context.WithValue(r.Context(), UserContextKey, token)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
