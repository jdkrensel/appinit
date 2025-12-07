package cmd

import (
	"appinit/assets"
	"log/slog"
	"os"

	"github.com/spf13/cobra"
)

// appName is the name of the app to create.
var appName string

// createCmd represents the create command
var createCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new app structure with the given name",
	Long: `Create a new app structure with the given name. 
Example: appinit create --name my-app`,
	Run: func(cmd *cobra.Command, args []string) {
		if appName == "" {
			slog.Error("app name is required")
			os.Exit(1)
		}
		if err := runCreate(appName); err != nil {
			slog.Error("create command failed", "error", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(createCmd)
	createCmd.Flags().StringVar(&appName, "name", "", "Name of the app to create (required)")
	createCmd.MarkFlagRequired("name")
}

// runCreate scaffolds the project structure with directories, files, and templates.
func runCreate(appName string) error {
	if err := createDirectory(appName); err != nil {
		return err
	}

	if err := createTemplates(appName); err != nil {
		return err
	}

	slog.Info("repository structure created successfully", "app", appName)
	return nil
}

// createDirectory creates a directory, ignoring errors if it already exists.
func createDirectory(name string) error {
	if err := os.Mkdir(name, 0755); err != nil && !os.IsExist(err) {
		slog.Error("failed to create directory", "path", name, "error", err)
		return err
	}
	slog.Debug("directory created", "path", name)
	return nil
}

// createFile creates a file, ignoring errors if it already exists.
func createFile(path string, content []byte) error {
	if err := os.WriteFile(path, content, 0644); err != nil && !os.IsExist(err) {
		slog.Error("failed to create file", "path", path, "error", err)
		return err
	}
	slog.Debug("file created", "path", path)
	return nil
}

// createTemplates copies template files from embedded assets to the base directory.
func createTemplates(baseDir string) error {
	return walkTemplates("templates", baseDir)
}

// walkTemplates recursively copies template directory structure to destination.
func walkTemplates(srcDir, destDir string) error {
	entries, err := assets.Templates.ReadDir(srcDir)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		srcPath := srcDir + "/" + entry.Name()
		destPath := destDir + "/" + entry.Name()

		if entry.IsDir() {
			if err := createDirectory(destPath); err != nil {
				return err
			}
			if err := walkTemplates(srcPath, destPath); err != nil {
				return err
			}
		} else {
			content, err := assets.Templates.ReadFile(srcPath)
			if err != nil {
				return err
			}
			if err := createFile(destPath, content); err != nil {
				return err
			}
		}
	}
	return nil
}
