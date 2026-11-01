from pathlib import Path

from orbit.core.tools.base import LaunchSpec, Tool, cred_env, ps_command


class ScubaGear(Tool):
    name = "scubagear"
    display = "ScubaGear"
    github = "https://github.com/cisagov/ScubaGear"
    route = "psgallery"
    package = "ScubaGear"
    needs_admin = True
    supported_os = ("windows",)
    fixture = "scubagear_sample.json"
    output_name = "ScubaResults.json"

    def launch_spec(self, creds: dict, out_dir: Path) -> LaunchSpec:
        script = (
            "Import-Module ScubaGear; "
            "Invoke-SCuBA -ProductNames * -OutPath $env:ORBIT_OUT_DIR "
            "-AppID $env:ORBIT_SCUBA_CLIENT_ID -Organization $env:ORBIT_SCUBA_TENANT_ID "
            "-CertificateThumbprint $env:ORBIT_SCUBA_CERT_THUMBPRINT"
        )
        env = cred_env("SCUBA", creds)
        env["ORBIT_OUT_DIR"] = str(out_dir)
        return LaunchSpec(ps_command(script), env, out_dir)
