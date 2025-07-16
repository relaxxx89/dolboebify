"""Entry point for the Dolboebify audio player."""

import sys

from dolboebify.gui import GUIApp


def main():
    """Main entry point for the package."""
    # Only GUI mode is now available
    app = GUIApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
