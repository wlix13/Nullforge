"""Xray proxy deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server, systemd

from nullforge.molds import FeaturesMold, XrayCoreMold
from nullforge.smithy.http import CURL_ARGS
from nullforge.smithy.versions import STATIC_URLS


GEOIP_DAT_URL = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat"
GEOSITE_DAT_URL = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"

GEOIP_DAT = {"geoip.dat": GEOIP_DAT_URL}
GEOSITE_DAT = {"geosite.dat": GEOSITE_DAT_URL}


def deploy_xray() -> None:
    """Deploy Xray proxy configuration."""

    features: FeaturesMold = host.data.features
    xray_opts = features.xray

    _install_xray(xray_opts)
    _download_geo_data()


def _install_xray(opts: XrayCoreMold) -> None:
    """Install Xray using official installation script."""

    if host.get_fact(File, "/usr/local/bin/xray") and not opts.force_update:
        return

    server.shell(
        name="Install Xray proxy",
        commands=f'bash -lc "$(curl -L {STATIC_URLS["xray_install_script"]})" @ install --beta',
        _sudo=True,
    )

    systemd.service(
        name="Enable and start Xray service",
        service="xray",
        running=True,
        enabled=True,
        _sudo=True,
    )


def _download_geo_data() -> None:
    """Download GeoIP and GeoSite data files."""

    base_dir = "/usr/local/share/xray"

    for file, url in GEOIP_DAT.items():
        files.download(
            name=f"Download {file}",
            src=url,
            dest=f"{base_dir}/{file}",
            extra_curl_args=CURL_ARGS,
        )

    for file, url in GEOSITE_DAT.items():
        files.download(
            name=f"Download {file}",
            src=url,
            dest=f"{base_dir}/{file}",
            extra_curl_args=CURL_ARGS,
        )


deploy_xray()
