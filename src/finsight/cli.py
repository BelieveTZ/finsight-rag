import platform
import sys

import typer

from finsight import __version__

app = typer.Typer(help="FinSight-RAG command line tools.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Run reproducible data, retrieval, evaluation, and serving workflows."""


@app.command()
def doctor() -> None:
    """Check the minimum local development environment."""
    python_ok = sys.version_info >= (3, 11)
    typer.echo(f"FinSight-RAG: {__version__}")
    typer.echo(f"Python: {platform.python_version()}")
    typer.echo(f"Platform: {platform.system()} {platform.machine()}")
    typer.echo(f"Status: {'ready' if python_ok else 'Python 3.11+ required'}")
    if not python_ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
