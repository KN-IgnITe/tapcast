package auth

import (
	"context"
	"fmt"

	firebase "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/auth"
)

type Authenticator struct {
	client *auth.Client
}

func NewAuthenticator(ctx context.Context) (*Authenticator, error) {
	// Firebase SDK automatically reads the GOOGLE_APPLICATION_CREDENTIALS environment
	// variable to find the key file path, so no options need to be passed here.
	app, err := firebase.NewApp(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize firebase app: %w", err)
	}

	client, err := app.Auth(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to create firebase auth client: %w", err)
	}

	return &Authenticator{client: client}, nil
}

func (a *Authenticator) VerifyToken(ctx context.Context, idToken string) (*auth.Token, error) {
	token, err := a.client.VerifyIDToken(ctx, idToken)
	if err != nil {
		return nil, fmt.Errorf("invalid token: %w", err)
	}
	return token, nil
}
