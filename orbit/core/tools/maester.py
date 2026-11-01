from pathlib import Path

from orbit.core.tools.base import LaunchSpec, Tool, cred_env, ps_command


class Maester(Tool):
    name = "maester"
    display = "Maester"
    github = "https://github.com/maester365/maester"
    route = "psgallery"
    package = "Maester"
    needs_admin = True
    fixture = "maester_sample.json"
    output_name = "maester.json"

    def launch_spec(self, creds: dict, out_dir: Path) -> LaunchSpec:
        script = (
            "Import-Module Maester; "
            "if ($env:ORBIT_MAESTER_CERT_THUMBPRINT) { Connect-MgGraph "
            "-ClientId $env:ORBIT_MAESTER_CLIENT_ID -TenantId $env:ORBIT_MAESTER_TENANT_ID "
            "-CertificateThumbprint $env:ORBIT_MAESTER_CERT_THUMBPRINT } else { "
            "$s = ConvertTo-SecureString $env:ORBIT_MAESTER_CLIENT_SECRET -AsPlainText -Force; "
            "$c = New-Object System.Management.Automation.PSCredential("
            "$env:ORBIT_MAESTER_CLIENT_ID, $s); "
            "Connect-MgGraph -TenantId $env:ORBIT_MAESTER_TENANT_ID -ClientSecretCredential $c }; "
            "Invoke-Maester -OutputJsonFile (Join-Path $env:ORBIT_OUT_DIR 'maester.json') "
            "-NonInteractive"
        )
        env = cred_env("MAESTER", creds)
        env["ORBIT_OUT_DIR"] = str(out_dir)
        return LaunchSpec(ps_command(script), env, out_dir)
