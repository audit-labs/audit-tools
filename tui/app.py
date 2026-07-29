"""
Audit Tools — interactive terminal UI.

Presents a platform menu, walks the user through credentials and check
selection, then runs the selected platform's collectors with live progress.

Run it with:

    python audit_tui.py
"""

from typing import ClassVar

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from tui import platforms
from tui.common import Check, ProgressEvent


class MenuScreen(Screen):
    """Pick a platform to audit."""

    BINDINGS: ClassVar[list] = [("q", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Vertical(id="menu-box"):
            yield Static("Select a platform to audit", classes="prompt")
            for platform in platforms.PLATFORMS:
                label = platform.label
                if not platform.enabled:
                    label = f"{label}  —  coming soon"
                yield Button(
                    label,
                    id=platform.key,
                    variant="primary" if platform.enabled else "default",
                    disabled=not platform.enabled,
                )
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = "Select a platform"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for platform in platforms.PLATFORMS:
            if event.button.id == platform.key and platform.enabled:
                self.app.platform = platform
                self.app.push_screen(ConfigScreen())
                return


class ConfigScreen(Screen):
    """Collect the connection details for the chosen platform."""

    BINDINGS: ClassVar[list] = [("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        platform = self.app.platform
        yield Header()
        with Center(), Vertical(id="form-box"):
            yield Static(
                f"{platform.label} audit — connection details", classes="prompt"
            )
            for f in platform.fields:
                yield Label(f.label)
                yield Input(
                    value=platforms.prefill(f),
                    placeholder=f.placeholder,
                    password=f.password,
                    id=f.key,
                )
            yield Static("", id="form-error", classes="error")
            with Horizontal(classes="buttons"):
                yield Button("Back", id="back")
                yield Button("Continue", id="continue", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        platform = self.app.platform
        self.sub_title = f"{platform.label} · connection"
        self.query_one(f"#{platform.fields[0].key}", Input).focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "continue":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        platform = self.app.platform
        settings = {}
        missing = []
        for f in platform.fields:
            value = self.query_one(f"#{f.key}", Input).value.strip()
            if not value:
                value = f.default
            if f.required and not value:
                missing.append(f.label.lower())
            settings[f.key] = value

        if missing:
            self.query_one("#form-error", Static).update(
                f"Please provide: {', '.join(missing)}."
            )
            return

        self.app.settings = settings
        self.app.push_screen(ChecksScreen())


class ChecksScreen(Screen):
    """Choose which checks to run."""

    BINDINGS: ClassVar[list] = [("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        platform = self.app.platform
        yield Header()
        with Center(), Vertical(id="checks-box"):
            yield Static("Select checks to run", classes="prompt")
            yield SelectionList(
                *[
                    Selection(
                        self._prompt(c),
                        c.key,
                        c.key in platform.default_selection,
                    )
                    for c in platform.checks
                ],
                id="checks",
            )
            yield Static("", id="checks-error", classes="error")
            with Horizontal(classes="buttons"):
                yield Button("Back", id="back")
                yield Button("Run audit", id="run", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"{self.app.platform.label} · select checks"
        self.query_one("#checks", SelectionList).focus()

    @staticmethod
    def _prompt(check: Check) -> Text:
        text = Text(check.label)
        if check.note:
            text.append(f"  ({check.note})", style="dim italic")
        return text

    def action_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "run":
            selected = list(self.query_one("#checks", SelectionList).selected)
            if not selected:
                self.query_one("#checks-error", Static).update(
                    "Select at least one check."
                )
                return
            self.app.selected_keys = selected
            self.app.push_screen(RunScreen())


class RunScreen(Screen):
    """Run the selected checks with live progress."""

    BINDINGS: ClassVar[list] = [("escape", "home", "Menu")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="run-box"):
            yield Static(id="run-target", classes="prompt")
            yield ProgressBar(id="progress", show_eta=False)
            yield RichLog(id="log", markup=True, highlight=False, wrap=True)
            with Horizontal(classes="buttons"):
                yield Button("Back to menu", id="menu", disabled=True)
                yield Button("Quit", id="quit", disabled=True, variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        platform = self.app.platform
        settings = self.app.settings
        keys = self.app.selected_keys
        self.sub_title = f"{platform.label} · running"
        self.output_dir = platform.output_dir(settings)
        target = settings[platform.id_key]
        self.query_one("#run-target", Static).update(
            f"Auditing [b]{target}[/]  ·  {len(keys)} checks  ·  → {self.output_dir}"
        )
        self._progress.update(total=len(keys), progress=0)
        self.run_audit()

    @property
    def _progress(self) -> ProgressBar:
        return self.query_one("#progress", ProgressBar)

    @work(thread=True)
    def run_audit(self) -> None:
        platform = self.app.platform
        settings = self.app.settings
        keys = self.app.selected_keys
        try:
            platform.run(
                settings,
                self.output_dir,
                keys,
                lambda ev: self.app.call_from_thread(self._handle_event, ev),
            )
        except Exception as e:
            self.app.call_from_thread(self._log, f"[red]Run failed:[/] {e}")
        finally:
            self.app.call_from_thread(self._finish)

    def _log(self, markup: str) -> None:
        self.query_one("#log", RichLog).write(markup)

    def _handle_event(self, ev: ProgressEvent) -> None:
        if ev.kind == "fetch":
            self._log(f"[dim]· {ev.label}…[/]")
        elif ev.kind == "start":
            self._log(f"[cyan]▶[/] {ev.label}…")
        elif ev.kind == "done":
            self._log(f"[green]✓[/] {ev.label} — [b]{ev.count}[/] rows")
            self._progress.advance(1)
        elif ev.kind == "error":
            self._log(f"[red]✗[/] {ev.label} — {ev.message}")
            self._progress.advance(1)
        elif ev.kind == "summary":
            self._log("")
            self._log(f"[bold green]Done.[/] Package written to {ev.label}")

    def _finish(self) -> None:
        self.query_one("#menu", Button).disabled = False
        self.query_one("#quit", Button).disabled = False

    def action_home(self) -> None:
        self.app.show_menu()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "menu":
            self.app.show_menu()
        elif event.button.id == "quit":
            self.app.exit()


class AuditApp(App):
    TITLE = "Audit Tools"

    CSS = """
    Screen {
        align: center middle;
    }
    #menu-box, #form-box, #checks-box {
        width: 64;
        height: auto;
        padding: 1 2;
        border: round $primary;
    }
    #run-box {
        width: 90%;
        height: 90%;
        padding: 1 2;
        border: round $primary;
    }
    .prompt {
        text-style: bold;
        margin-bottom: 1;
    }
    .error {
        color: $error;
        margin-top: 1;
    }
    Label {
        margin-top: 1;
    }
    .buttons {
        height: auto;
        margin-top: 1;
        align-horizontal: right;
    }
    .buttons Button {
        margin-left: 2;
    }
    #menu-box Button {
        width: 100%;
        margin-top: 1;
    }
    #checks {
        height: auto;
        max-height: 14;
    }
    #log {
        height: 1fr;
        border: round $panel;
        padding: 0 1;
        margin-top: 1;
    }
    """

    def on_mount(self) -> None:
        self.platform = None
        self.settings: dict = {}
        self.selected_keys: list = []
        self.push_screen(MenuScreen())

    def show_menu(self) -> None:
        """Pop back to the platform menu."""
        while len(self.screen_stack) > 2:
            self.pop_screen()


def main() -> None:
    AuditApp().run()


if __name__ == "__main__":
    main()
