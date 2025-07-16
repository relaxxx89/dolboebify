"""Entry point for the Dolboebify audio player."""

import sys

from dolboebify.ui.cli import main as cli_main

if __name__ == "__main__":
    # Check if '--gui' flag is passed to use GUI mode
    if "--gui" in sys.argv:
        # Remove '--gui' flag to prevent issues with other argument parsers
        sys.argv.remove("--gui")
        from dolboebify.gui import GUIApp

        app = GUIApp()
        sys.exit(app.run())
    else:
        # Default to CLI mode
        cli_main()
