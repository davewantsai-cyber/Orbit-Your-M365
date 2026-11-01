import sys
from pathlib import Path

from orbit.core.tools.base import LaunchSpec, Tool, cred_env


class ROADtools(Tool):
    name = "roadtools"
    display = "ROADtools"
    github = "https://github.com/dirkjanm/ROADtools"
    route = "pypi"
    package = "roadrecon"
    needs_pwsh = False

    def launch_spec(self, creds: dict, out_dir: Path) -> LaunchSpec:
        # Client ID and flow are read from env by a tiny launcher so argv stays secret-free.
        code = (
            "import os,sys;from roadtools.roadrecon.main import main;"
            "a=['auth','-f',os.path.join(os.environ['ORBIT_OUT_DIR'],'.roadtools_auth.json')];"
            "c=os.environ.get('ORBIT_ROAD_CLIENT_ID');"
            "a+=['-c',c] if c else [];"
            "a+=['--device-code'] if os.environ.get('ORBIT_ROAD_DEVICE_CODE') else [];"
            "sys.argv=['roadrecon']+a;main();"
            "sys.argv=['roadrecon','gather','-f',os.path.join(os.environ['ORBIT_OUT_DIR'],"
            "'.roadtools_auth.json'),'-d',os.path.join(os.environ['ORBIT_OUT_DIR'],'roadrecon.db')];"
            "main()"
        )
        env = cred_env("ROAD", creds)
        env["ORBIT_OUT_DIR"] = str(out_dir)
        return LaunchSpec([sys.executable, "-c", code], env, out_dir)
