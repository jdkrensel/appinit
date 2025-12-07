package cmd

import (
	"os"

	"github.com/spf13/cobra"
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "appinit",
	Short: "Scaffold a new project with app and infra structure",
	Long: `appinit scaffolds a new project with a standardized directory structure
for both application and infrastructure code.

Usage:
  appinit create --name my-app

This creates a project with the following structure:
  my-app/
  ├── app/        (application code)
  ├── infra/      (infrastructure as code)
  └── [templates] (pre-configured files)`,
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	// Global flags can be defined here if needed in the future
}
