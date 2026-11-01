import sys

from orbit.core.outputs import OutputConfig, make_run_folder
from orbit.core.pipeline import finalize
from orbit.core.runner import Runner, RunStatus, stream_process
from orbit.core.tools import get_tool
from orbit.tui.app import OrbitApp

SECRET = "hunter2-SECRET"


async def test_stream_redacts_and_env_only():
    lines: list[str] = []
    code = "import os;print('token=' + os.environ['ORBIT_X'])"
    rc = await stream_process([sys.executable, "-c", code], {"ORBIT_X": SECRET}, lines.append, [SECRET])
    assert rc == 0 and lines == ["token=***"]


async def test_dry_run_pipeline_end_to_end(tmp_path):
    folder = make_run_folder(tmp_path)
    tools = [get_tool("scubagear"), get_tool("maester")]
    runs = await Runner(folder, {}, dry_run=True).run_all(tools)
    assert all(r.status is RunStatus.COMPLETE and r.progress == 100 for r in runs.values())
    cfg = OutputConfig(base_dir=tmp_path, formats={"PDF", "DOCX"}, encrypt=True, keep_unencrypted=False)
    findings, written = finalize(folder, ["ScubaGear", "Maester"], cfg, True, "pw")
    assert len(findings) == 16
    assert any(p.name.endswith(".orbit.zip") for p in written)
    assert not folder.exists()  # unencrypted copy removed only after archive was written


async def test_hash_mismatch_skips_tool(tmp_path):
    from orbit.core.hash_checker import HashResult, HashStatus
    bad = HashResult("maester", "1", HashStatus.MISMATCH, ["x.psm1"])
    r = Runner(tmp_path, {}, hash_results=[bad])
    run = await r.run_tool(get_tool("maester"))
    assert run.status is RunStatus.SKIPPED


async def test_missing_binary_fails_cleanly(tmp_path):
    run = await Runner(tmp_path, {}).run_tool(get_tool("hawk"))
    # pwsh absent -> FileNotFoundError handled; pwsh present -> module absent -> Failed
    assert run.status is RunStatus.FAILED


async def test_tui_launches_dry_run():
    app = OrbitApp(dry_run=True)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert type(app.screen).__name__ == "HomeScreen"
        assert app.state.dry_run
        for target in ("credentials", "tool_select", "output", "installer", "run", "report"):
            app.push_screen(target)
            await pilot.pause()
            assert target.replace("_", "") in type(app.screen).__name__.lower()
            app.pop_screen()


async def test_run_screen_dry_run_flow(tmp_path):
    app = OrbitApp(dry_run=True)
    app.state.output.base_dir = tmp_path
    app.state.selected = {"scubagear", "maester"}
    async with app.run_test(size=(120, 60)) as pilot:
        app.push_screen("run")
        await pilot.pause()
        app.screen.start_run()
        for _ in range(100):
            await pilot.pause(0.1)
            if app.state.runs and "Done." in str(app.screen.query_one("#result").render()):
                break
        assert {r.status for r in app.state.runs.values()} == {RunStatus.COMPLETE}
        assert any(p.name == "ORBIT_Summary_DRYRUN.pdf" for p in app.state.run_folder.iterdir())
