from pathlib import Path

from orbit.core.tools.base import LaunchSpec, Tool, cred_env, ps_command


class Hawk(Tool):
    name = "hawk"
    display = "Hawk"
    github = "https://github.com/T0pCyber/hawk"
    route = "psgallery"
    package = "Hawk"
    fixture = ""

    def launch_spec(self, creds: dict, out_dir: Path) -> LaunchSpec:
        script = (
            "Import-Module Hawk; "
            "Start-HawkTenantInvestigation -FilePath $env:ORBIT_OUT_DIR -SkipUpdate"
        )
        env = cred_env("HAWK", creds)
        env["ORBIT_OUT_DIR"] = str(out_dir)
        return LaunchSpec(ps_command(script), env, out_dir)
