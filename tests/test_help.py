from textual.app import App

from orbit.tui.app import OrbitApp
from orbit.tui.screens.help import HelpScreen


async def test_help_screen_composes():
    class Host(App):
        def on_mount(self):
            self.push_screen(HelpScreen())

    app = Host()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        assert "Keyboard Shortcuts" in str(app.screen.query_one("Static").render())


async def test_question_mark_toggles_help():
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("question_mark")
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("question_mark")
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"
        await pilot.press("question_mark")
        await pilot.press("q")
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"
