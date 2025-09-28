#!/usr/bin/env python3
"""Simple IDF Stop Monitoring MCP Server - returns next departures from xxxxx to yyyyy"""
import os
import sys
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import httpx
from fastmcp import FastMCP
#from mcp.server.fastmcp import FastMCP

# Configure logging to stderr only (never stdout!)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,   # ✅ safe for stdio-based MCP servers
)
logger = logging.getLogger("idf_stop_monitoring-server")

# Initialize MCP server
mcp = FastMCP("idf_stop_monitoring")

# Configuration
#IDF_API_KEY = os.environ.get("IDF_API_KEY", "").strip()
IDF_API_KEY = "xxx"

# Default endpoint & MonitoringRef for xxxxx -> this is the station to monitor
DEFAULT_MONITORING_URL = (
    "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring?MonitoringRef=STIF:StopArea:SP:xxxxxx:"
)
# DestinationRef filter value for yyyyy
SAINT_LAZARE_DEST_REF = "STIF:StopArea:SP:yyyyy:"

# === UTILITY FUNCTIONS ===

def parse_iso_to_dt(isotext: str) -> datetime | None:
    if not isotext:
        return None
    try:
        # handle trailing Z
        if isotext.endswith("Z"):
            return datetime.fromisoformat(isotext.replace("Z", "+00:00"))
        return datetime.fromisoformat(isotext)
    except Exception:
        # try a fallback parse by trimming fractions
        try:
            return datetime.fromisoformat(isotext.split(".")[0])
        except Exception:
            return None

def hhmm_from_dt(dt: datetime) -> str:
    if not dt:
        return "unknown"
    paris = dt.astimezone(ZoneInfo("Europe/Paris"))
    return f"{paris.hour:02d}:{paris.minute:02d}"

def _iso_to_paris_local(iso_ts: str) -> str:
    """Convert an ISO timestamp string to Europe/Paris local time ISO format."""
    try:
        if iso_ts.endswith("Z"):
            dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso_ts)
        dt_utc = dt.astimezone(timezone.utc)
        paris = dt_utc.astimezone(ZoneInfo("Europe/Paris"))
        return paris.isoformat()
    except Exception:
        return iso_ts

# === MCP TOOLS ===

@mcp.tool()
async def next_trains_to_saint_lazare(monitoring_url: str = "", api_key_env: str = "") -> str:
    """Get next ExpectedDepartureTime values for Les Vallées => Saint Lazare."""
    logger.info("Tool called: next_trains_to_saint_lazare")

    # ✅ Ensure monitoring_url is valid, else fallback
    url = monitoring_url.strip()
    if not url.startswith("http"):
        logger.warning(f"Ignoring invalid monitoring_url='{url}', using default instead")
    # Actually use hardcoded URL or else LLM will allucinate and try to guess something 
    url = DEFAULT_MONITORING_URL

    # ✅ Ensure API key is valid, else fallback
    provided_key = api_key_env.strip() if api_key_env.strip() else IDF_API_KEY
    if not provided_key:
        logger.error("API key not provided, falling back to default")
    # Same as url
    provided_key = IDF_API_KEY

    headers = {"apikey": provided_key}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Requesting PRIM API: {url}")
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}")
        return f"❌ API Error: HTTP {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        logger.error(f"Network/Request error: {e}")
        return f"❌ Error: Network or request failure: {str(e)}"

    try:
        visits = []
        
        siri = data.get("Siri", {}) if isinstance(data, dict) else {}
        sd = siri.get("ServiceDelivery") or siri.get("serviceDelivery") or {}
        smd_list = sd.get("StopMonitoringDelivery") or sd.get("stopMonitoringDelivery") or []
        
        if isinstance(smd_list, dict):
            smd_list = [smd_list]

        for smd in smd_list:
            mvisits = smd.get("MonitoredStopVisit", []) or smd.get("monitoredStopVisit", [])
            if isinstance(mvisits, dict):
                mvisits = [mvisits]
            for mv in mvisits:
                visits.append(mv)

        if not visits:
            visits = data.get("MonitoredStopVisit", []) if isinstance(data, dict) else []

        if not visits:
            return "⚠️ No monitored visits found in API response."

        times = []
        for v in visits:
            if not isinstance(v, dict):
                continue

            mvj = v.get("MonitoredVehicleJourney") or v.get("monitoredVehicleJourney") or v
            dest = mvj.get("DestinationRef") or mvj.get("destinationRef") or mvj.get("Destination") or {}

            if isinstance(dest, dict):
                destination = dest.get("value") or dest.get("#text")
            elif isinstance(dest, str):
                destination = dest[0]
            else:
                destination = dest

            edt = (
                mvj.get("MonitoredCall").get("ExpectedDepartureTime")
                or ""
            )

            if destination == SAINT_LAZARE_DEST_REF:
                times.append(parse_iso_to_dt(edt) if edt else "unknown")

        if not times:
            return "⚠️ No upcoming departures to Saint Lazare found."

        try:
            sorted_times = sorted(times)
        except Exception:
            sorted_times = times

        out_lines = ["📊 Next departures from xxxxx → yyyyy:"]
        for t in sorted_times:
            out_lines.append(f"- {hhmm_from_dt(t)}")
        out_lines.append(f"\nSummary: {len(sorted_times)} upcoming departure(s) found.")
        return "\n".join(out_lines)

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return f"❌ Error processing API response: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting IDF Stop Monitoring MCP server...")
    try:
        #mcp.run(transport="stdio")
        mcp.run(transport="sse", host="0.0.0.0", port=8000, path="/mcp" ) # this option to be compatible with Home Assistant MCP integration
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

