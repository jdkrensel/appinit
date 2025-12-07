package cmd

import (
	"appinit/assets"
	"log/slog"
	"os"

	"github.com/spf13/cobra"
)

// appName is the name of the root directory to create.
var appName string
var appOnly bool
var infraOnly bool

// createCmd represents the create command
var createCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new project structure",
	Long: `Create a new project structure. 
Example: appinit create --name my-app          (creates my-app with app and infra)
Example: appinit create --app-only             (creates app directory only)
Example: appinit create --infra-only           (creates infra directory only)`,
	Run: func(cmd *cobra.Command, args []string) {
		if appOnly && infraOnly {
			slog.Error("cannot use both --app-only and --infra-only")
			os.Exit(1)
		}
		if appName == "" && !appOnly && !infraOnly {
			slog.Error("either --name, --app-only, or --infra-only is required")
			os.Exit(1)
		}
		if err := runCreate(); err != nil {
			slog.Error("create command failed", "error", err)
			os.Exit(1)
		}
	},
}

func init() {
	rootCmd.AddCommand(createCmd)
	createCmd.Flags().StringVar(&appName, "name", "", "Name of the root directory to create")
	createCmd.Flags().BoolVar(&appOnly, "app-only", false, "Create only the app directory")
	createCmd.Flags().BoolVar(&infraOnly, "infra-only", false, "Create only the infra directory")
}

// runCreate scaffolds the project structure based on flags.
func runCreate() error {
	if appOnly {
		if err := createDirectory("app"); err != nil {
			return err
		}
		if err := walkTemplates("templates/app", "app"); err != nil {
			return err
		}
		if err := createDirectory("app/tests"); err != nil {
			return err
		}
		if err := createFile("app/tests/__init__.py", []byte{}); err != nil {
			return err
		}
		slog.Info("app directory created successfully")
	} else if infraOnly {
		if err := createDirectory("infra"); err != nil {
			return err
		}
		if err := walkTemplates("templates/infra", "infra"); err != nil {
			return err
		}
		if err := createDirectory("infra/stacks"); err != nil {
			return err
		}
		if err := createFile("infra/stacks/__init__.py", []byte{}); err != nil {
			return err
		}
		if err := createDirectory("infra/tests"); err != nil {
			return err
		}
		if err := createFile("infra/tests/__init__.py", []byte{}); err != nil {
			return err
		}
		slog.Info("infra directory created successfully")
	} else {
		// Default: create root directory with both app and infra
		if err := createDirectory(appName); err != nil {
			return err
		}

		// Copy root-level files
		if err := copyRootTemplates(appName); err != nil {
			return err
		}

		// Copy app and infra
		if err := createTemplates(appName); err != nil {
			return err
		}

		slog.Info("project structure created successfully", "name", appName)
	}
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

// createTemplates copies all template files from embedded assets to the base directory.
func createTemplates(baseDir string) error {
	return walkTemplates("templates", baseDir)
}

// copyRootTemplates copies root-level files (.gitignore, README, workspace config).
func copyRootTemplates(baseDir string) error {
	rootFiles := []string{".gitignore", "README.md", "repo.code-workspace"}

	for _, filename := range rootFiles {
		srcPath := "templates/" + filename
		destPath := baseDir + "/" + filename

		content, err := assets.Templates.ReadFile(srcPath)
		if err != nil {
			if os.IsNotExist(err) {
				// Skip if file doesn't exist
				continue
			}
			return err
		}

		if err := createFile(destPath, content); err != nil {
			return err
		}
	}
	return nil
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
