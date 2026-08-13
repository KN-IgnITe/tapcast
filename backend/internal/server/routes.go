package server

import (
	"net/http"

	fbauth "firebase.google.com/go/v4/auth"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"
	"github.com/m1kus3q/pubpredictor/backend/internal/auth"
	"github.com/m1kus3q/pubpredictor/backend/internal/middleware"
)

type Server struct {
	authenticator *auth.Authenticator
}

func NewServer(authenticator *auth.Authenticator) *Server {
	return &Server{authenticator: authenticator}
}

func (s *Server) Routes() http.Handler {
	r := chi.NewRouter()

	// cors setup
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	r.Get("/public", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("Anyone can see this public data"))
	})

	// protected routes
	r.Group(func(r chi.Router) {
		r.Use(middleware.Auth(s.authenticator))

		r.Get("/protected", func(w http.ResponseWriter, r *http.Request) {
			firebaseToken, ok := r.Context().Value(middleware.UserContextKey).(*fbauth.Token)
			if !ok {
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}

			_, _ = w.Write([]byte("Secret data for user: " + firebaseToken.UID))
		})
	})

	return r
}
