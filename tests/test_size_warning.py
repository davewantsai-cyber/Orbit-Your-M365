from orbit.tui.app import OrbitApp
from orbit.tui.screens.size_warning import SizeWarningScreen


async def test_small_terminal_shows_warning_then_continues(monkeypatch):
    monkeypatch.setattr("orbit.tui.screens.onboarding.has_saved_credentials", lambda: True)
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SizeWarningScreen)
        assert "80 × 24" in str(app.screen.query_one("Static").render())
        await pilot.click("#continue-anyway")
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"


async def test_large_terminal_skips_warning(monkeypatch):
    monkeypatch.setattr("orbit.tui.screens.onboarding.has_saved_credentials", lambda: True)
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"
