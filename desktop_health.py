from flask import Flask, render_template, jsonify
import psutil
import socket
import json
import requests

from pathlib import Path
from datetime import datetime, timezone


app = Flask(__name__)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EVENT_FILE = BASE_DIR / "agent_events.json"
LOG_FILE = BASE_DIR / "computer_health.log"


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


# ============================================================
# SYSTEM INFORMATION
# ============================================================

@app.route("/api/system")
def system_info():

    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return jsonify({
        "hostname": socket.gethostname(),
        "cpu": cpu,
        "memory": memory.percent,
        "disk": disk.percent,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })


# ============================================================
# PROCESSES
# ============================================================

@app.route("/api/processes")
def processes():

    process_list = []

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):

        try:

            info = process.info

            process_list.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu": round(
                    info["cpu_percent"] or 0,
                    1
                ),
                "memory": round(
                    info["memory_percent"] or 0,
                    1
                )
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):

            continue


    process_list.sort(
        key=lambda x: x["cpu"],
        reverse=True
    )


    return jsonify(process_list[:20])


# ============================================================
# AGENT ACTIVITY
# ============================================================

@app.route("/api/activity")
def activity():

    try:

        if not EVENT_FILE.exists():
            return jsonify([])

        with open(
            EVENT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            events = json.load(file)

        if not isinstance(events, list):
            return jsonify([])

        return jsonify(events[-50:])


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# LOGS
# ============================================================

@app.route("/api/logs")
def logs():

    logs = []

    try:

        if not LOG_FILE.exists():
            return jsonify([])

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            lines = file.readlines()


        for line in lines[-100:]:

            line = line.strip()

            if not line:
                continue


            log_type = "INFO"

            if "High" in line or "WARNING" in line:
                log_type = "WARNING"

            if "error" in line.lower():
                log_type = "ERROR"


            logs.append({
                "time": line[:20],
                "type": log_type,
                "message": line
            })


        return jsonify(logs)


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


# ============================================================
# LIVE NVD CVE DATA
# ============================================================

@app.route("/api/cves")
def cves():

    try:

        # Request recently published CVEs.
        # We intentionally limit the result count so
        # the dashboard stays lightweight.

        url = (
            "https://services.nvd.nist.gov/"
            "rest/json/cves/2.0"
        )


        response = requests.get(
            url,
            params={
                "resultsPerPage": 20,
                "startIndex": 0
            },
            timeout=15
        )


        response.raise_for_status()

        data = response.json()


        vulnerabilities = []


        for item in data.get(
            "vulnerabilities",
            []
        ):

            cve = item.get(
                "cve",
                {}
            )


            cve_id = cve.get(
                "id",
                "Unknown"
            )


            descriptions = cve.get(
                "descriptions",
                []
            )


            description = "No description available."


            for desc in descriptions:

                if desc.get("lang") == "en":

                    description = desc.get(
                        "value",
                        description
                    )

                    break


            # ------------------------------------------------
            # CVSS
            # ------------------------------------------------

            score = None
            severity = "UNKNOWN"


            metrics = cve.get(
                "metrics",
                {}
            )


            # Prefer CVSS 4.0
            if metrics.get("cvssMetricV40"):

                metric = metrics[
                    "cvssMetricV40"
                ][0]

                cvss_data = metric.get(
                    "cvssData",
                    {}
                )

                score = cvss_data.get(
                    "baseScore"
                )

                severity = cvss_data.get(
                    "baseSeverity",
                    "UNKNOWN"
                )


            # Fall back to CVSS 3.1
            elif metrics.get("cvssMetricV31"):

                metric = metrics[
                    "cvssMetricV31"
                ][0]

                cvss_data = metric.get(
                    "cvssData",
                    {}
                )

                score = cvss_data.get(
                    "baseScore"
                )

                severity = cvss_data.get(
                    "baseSeverity",
                    "UNKNOWN"
                )


            # Fall back to CVSS 3.0
            elif metrics.get("cvssMetricV30"):

                metric = metrics[
                    "cvssMetricV30"
                ][0]

                cvss_data = metric.get(
                    "cvssData",
                    {}
                )

                score = cvss_data.get(
                    "baseScore"
                )

                severity = cvss_data.get(
                    "baseSeverity",
                    "UNKNOWN"
                )


            # ------------------------------------------------
            # DATES
            # ------------------------------------------------

            published = cve.get(
                "published"
            )

            modified = cve.get(
                "lastModified"
            )


            # ------------------------------------------------
            # REFERENCES
            # ------------------------------------------------

            references = []

            for reference in cve.get(
                "references",
                []
            )[:3]:

                ref_url = reference.get(
                    "url"
                )

                if ref_url:
                    references.append(
                        ref_url
                    )


            vulnerabilities.append({

                "id": cve_id,

                "description": description,

                "score": score,

                "severity": severity,

                "published": published,

                "modified": modified,

                "references": references

            })


        return jsonify({
            "source": "NVD",
            "updated": datetime.now(
                timezone.utc
            ).isoformat(),
            "count": len(
                vulnerabilities
            ),
            "vulnerabilities": vulnerabilities
        })


    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Unable to reach NVD.",
            "details": str(error)
        }), 502


    except Exception as error:

        return jsonify({
            "error": "CVE processing failed.",
            "details": str(error)
        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )