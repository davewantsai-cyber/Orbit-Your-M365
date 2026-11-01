from orbit.core import config_store
from orbit.tui.app import OrbitApp
from orbit.tui.screens.onboarding import OnboardingScreen


async def test_wizard_composes_and_skip_sets_first_run_false(monkeypatch):
    monkeypatch.setattr("orbit.tui.screens.onboarding.has_saved_credentials", lambda: False)
    config_store.update("app", first_run=True)
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, OnboardingScreen)
        await pilot.click("#skip-1")
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"
    assert config_store.load()["app"]["first_run"] is False


async def test_wizard_not_shown_after_first_run():
    config_store.update("app", first_run=False)
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"


async def test_wizard_tool_step_saves_selection(monkeypatch):
    monkeypatch.setattr("orbit.tui.screens.onboarding.has_saved_credentials", lambda: False)
    config_store.update("app", first_run=True)
    app = OrbitApp(dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#next-1")
        await pilot.click("#later-2")
        await pilot.click("#wiz-maester")
        await pilot.click("#next-3")
        await pilot.pause()
        assert "maester" in app.state.selected
        assert type(app.screen).__name__ == "HomeScreen"
