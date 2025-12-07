package main

import (
	"log/slog"
	"os"

	"appinit/cmd"
)

func main() {
	level := slog.LevelInfo
	if os.Getenv("DEBUG") != "" {
		level = slog.LevelDebug
	}

	var handler slog.Handler

	if os.Getenv("ENV") == "production" {
		handler = slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
			Level:     level,
			AddSource: true,
		})
	} else {
		handler = slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{
			Level:     level,
			AddSource: false,
		})
	}

	slog.SetDefault(slog.New(handler))
	cmd.Execute()
}
