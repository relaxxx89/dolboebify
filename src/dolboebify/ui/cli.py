"""Command-line interface for the Dolboebify audio player."""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from dolboebify.core import Player


class CLIApp:
    """Command-line interface for Dolboebify."""

    def __init__(self):
        """Initialize the CLI application."""
        self.player = Player()
        self.console = Console()
        self.is_running = False

    def _format_time(self, milliseconds: int) -> str:
        """Format milliseconds as MM:SS."""
        seconds = int(milliseconds / 1000)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _create_progress_bar(self) -> Progress:
        """Create a progress bar for playback."""
        return Progress(
            TextColumn("[blue]Time:"),
            TextColumn("{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[green]{task.percentage:.0f}%"),
            expand=True,
        )

    def _create_playback_info_panel(
        self, track_title: str, position: int, duration: int
    ) -> Panel:
        """Create a panel with playback information."""
        table = Table.grid(expand=True)

        # Add track info
        table.add_row(
            f"[yellow]Now Playing:[/yellow] " f"[green]{track_title}[/green]"
        )

        # Add progress bar
        progress = self._create_progress_bar()
        progress.add_task(
            f"{self._format_time(position)} / {self._format_time(duration)}",
            total=100,
            completed=int(self.player.position_percent),
        )

        table.add_row(progress)

        # Add controls info
        controls = (
            "[bold]Controls:[/bold] "
            "[blue]Space[/blue]=Play/Pause "
            "[blue]Left/Right[/blue]=Prev/Next "
            "[blue]Up/Down[/blue]=Volume "
            "[blue]Q[/blue]=Quit"
        )
        table.add_row(controls)

        return Panel(table, title="Dolboebify Player", border_style="green")

    def play_file(self, file_path: str):
        """Play a single audio file."""
        if self.player.play(file_path):
            self._run_player_interface()
        else:
            self.console.print(f"[red]Failed to play file: {file_path}[/red]")

    def play_playlist(self, directory: str):
        """Play all audio files in a directory as a playlist."""
        count = self.player.load_playlist(directory)
        if count > 0:
            self.console.print(
                f"[green]Loaded {count} tracks from {directory}[/green]"
            )
            if self.player.play(self.player.playlist[0]["path"]):
                self._run_player_interface()
        else:
            self.console.print(
                f"[red]No supported audio files found in {directory}[/red]"
            )

    def _run_player_interface(self):
        """Run the interactive player interface."""
        self.is_running = True

        with Live(auto_refresh=False) as live:
            while self.is_running and self.player.current_media:
                if not self.player.is_playing and not self.player.is_paused:
                    # Track ended, try to play next
                    if not self.player.next_track():
                        # No more tracks or error
                        self.is_running = False
                        break

                track_title = (
                    self.player.playlist[self.player.current_index]["title"]
                    if self.player.playlist and self.player.current_index >= 0
                    else Path(self.player.current_media.get_mrl()).stem
                )

                # Update display
                panel = self._create_playback_info_panel(
                    track_title,
                    self.player.position,
                    self.player.duration,
                )

                live.update(panel, refresh=True)

                # Sleep to reduce CPU usage
                time.sleep(0.1)


@click.group()
@click.option("--cli", is_flag=True, help="Force CLI mode (default)")
@click.option("--gui", is_flag=True, help="Use GUI mode instead of CLI")
@click.version_option()
def cli(cli: bool, gui: bool):
    """Dolboebify - A modern audio player.

    Run with '--gui' flag to start in GUI mode.
    """
    # Handle GUI flag
    if gui and not cli:
        # Import and start the GUI
        try:
            from dolboebify.gui import GUIApp

            app = GUIApp()
            sys.exit(app.run())
        except ImportError:
            click.echo("GUI dependencies not available. Please install PyQt5.")
            sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True), required=False)
def play(file_path: Optional[str] = None):
    """Play an audio file or start interactive mode."""
    app = CLIApp()

    if file_path:
        app.play_file(file_path)
    else:
        click.echo("Starting interactive mode (not implemented yet)")


@cli.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
def playlist(directory: str):
    """Play all audio files in a directory as a playlist."""
    app = CLIApp()
    app.play_playlist(directory)


def main():
    """Entry point for the application."""
    cli()
