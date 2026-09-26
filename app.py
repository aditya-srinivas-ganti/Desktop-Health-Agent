from flask import Flask, render_template, jsonify
import psutil
import socket
import json
import requests

from pathlib import Path
from datetime import datetime, timezone, timedelta


app = Flask(__name__)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EVENT_FILE = BASE_DIR / "agent_events.json"
LOG_FILE = BASE_DIR / "computer_health.log"


# ============================================================
# AI MODEL RELEASE DATA
# Curated major model releases from the last ~3 years.
# ============================================================

AI_MODELS = [

    # ========================================================
    # 2023
    # ========================================================

    {
        "name": "Mistral 7B",
        "company": "Mistral AI",
        "date": "2023-09-27",
        "type": "LLM",
        "category": "Open Weight",
        "description": "7B parameter open-weight language model designed for efficient local inference."
    },

    {
        "name": "GPT-4 Turbo",
        "company": "OpenAI",
        "date": "2023-11-06",
        "type": "LLM",
        "category": "Frontier",
        "description": "GPT-4 family model with expanded context and improved efficiency."
    },

    {
        "name": "Grok-1",
        "company": "xAI",
        "date": "2023-11-04",
        "type": "LLM",
        "category": "Frontier",
        "description": "xAI's first large language model released for the Grok system."
    },

    {
        "name": "Gemini 1.0",
        "company": "Google",
        "date": "2023-12-06",
        "type": "Multimodal",
        "category": "Frontier",
        "description": "Google's multimodal Gemini model family spanning Nano, Pro and Ultra variants."
    },


    # ========================================================
    # 2024
    # ========================================================

    {
        "name": "Gemini 1.5 Pro",
        "company": "Google",
        "date": "2024-02-15",
        "type": "Multimodal",
        "category": "Frontier",
        "description": "Long-context multimodal model from the Gemini 1.5 family."
    },

    {
        "name": "Claude 3",
        "company": "Anthropic",
        "date": "2024-03-04",
        "type": "Multimodal",
        "category": "Frontier",
        "description": "Claude 3 family including Opus, Sonnet and Haiku models."
    },

    {
        "name": "Command R",
        "company": "Cohere",
        "date": "2024-03-11",
        "type": "LLM",
        "category": "Enterprise",
        "description": "Enterprise-focused language model optimized for retrieval-augmented generation."
    },

    {
        "name": "DBRX",
        "company": "Databricks",
        "date": "2024-03-27",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Mixture-of-experts large language model released by Databricks."
    },

    {
        "name": "Llama 3",
        "company": "Meta",
        "date": "2024-04-18",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Meta's Llama 3 generation initially released in 8B and 70B variants."
    },

    {
        "name": "Phi-3",
        "company": "Microsoft",
        "date": "2024-04-23",
        "type": "Small LLM",
        "category": "Open Weight",
        "description": "Compact language-model family designed to deliver strong capability with smaller models."
    },

    {
        "name": "DeepSeek-V2",
        "company": "DeepSeek",
        "date": "2024-05-07",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Mixture-of-experts language model from DeepSeek."
    },

    {
        "name": "GPT-4o",
        "company": "OpenAI",
        "date": "2024-05-13",
        "type": "Multimodal",
        "category": "Frontier",
        "description": "Omni model designed to work across text, vision and audio with low-latency interaction."
    },

    {
        "name": "Claude 3.5 Sonnet",
        "company": "Anthropic",
        "date": "2024-06-20",
        "type": "LLM",
        "category": "Frontier",
        "description": "Claude model focused on reasoning, coding and general-purpose tasks."
    },

    {
        "name": "Mistral Large 2",
        "company": "Mistral AI",
        "date": "2024-07-24",
        "type": "LLM",
        "category": "Frontier",
        "description": "Large language model generation emphasizing reasoning, coding and multilingual tasks."
    },

    {
        "name": "Llama 3.1",
        "company": "Meta",
        "date": "2024-07-23",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Llama generation including the 405B flagship model and extended context support."
    },

    {
        "name": "Grok-2",
        "company": "xAI",
        "date": "2024-08-13",
        "type": "LLM",
        "category": "Frontier",
        "description": "Second-generation Grok model with improved reasoning and multimodal capabilities."
    },

    {
        "name": "Phi-3.5",
        "company": "Microsoft",
        "date": "2024-08-20",
        "type": "Small LLM",
        "category": "Open Weight",
        "description": "Updated Phi family with improved small-model reasoning and multimodal capabilities."
    },

    {
        "name": "FLUX.1",
        "company": "Black Forest Labs",
        "date": "2024-08-01",
        "type": "Image",
        "category": "Generative",
        "description": "Text-to-image model family focused on high-quality image generation."
    },

    {
        "name": "Pixtral 12B",
        "company": "Mistral AI",
        "date": "2024-09-10",
        "type": "Multimodal",
        "category": "Open Weight",
        "description": "Vision-language model combining image understanding with language capabilities."
    },

    {
        "name": "Qwen2.5",
        "company": "Alibaba",
        "date": "2024-09-19",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Qwen model family update covering multiple parameter sizes."
    },

    {
        "name": "Llama 3.2",
        "company": "Meta",
        "date": "2024-09-25",
        "type": "Multimodal",
        "category": "Open Weight",
        "description": "Llama generation introducing smaller models and vision-capable variants."
    },

    {
        "name": "OpenAI o1",
        "company": "OpenAI",
        "date": "2024-09-12",
        "type": "Reasoning",
        "category": "Reasoning",
        "description": "Reasoning-focused model family designed to spend additional computation on difficult problems."
    },

    {
        "name": "DeepSeek-V3",
        "company": "DeepSeek",
        "date": "2024-12-26",
        "type": "LLM",
        "category": "Open Weight",
        "description": "Large mixture-of-experts model released with strong general and coding capabilities."
    },

    {
        "name": "Phi-4",
        "company": "Microsoft",
        "date": "2024-12-12",
        "type": "Small LLM",
        "category": "Open Weight",
        "description": "Compact reasoning-focused language model in Microsoft's Phi series."
    },

    {
        "name": "Amazon Nova",
        "company": "Amazon",
        "date": "2024-12-03",
        "type": "Multimodal",
        "category": "Enterprise",
        "description": "Amazon's foundation-model family for text, multimodal and enterprise workloads."
    },


    # ========================================================
    # 2025
    # ========================================================

    {
        "name": "DeepSeek-R1",
        "company": "DeepSeek",
        "date": "2025-01-20",
        "type": "Reasoning",
        "category": "Open Weight",
        "description": "Reasoning-focused model released with open model weights."
    },

    {
        "name": "o3-mini",
        "company": "OpenAI",
        "date": "2025-01-31",
        "type": "Reasoning",
        "category": "Reasoning",
        "description": "Smaller reasoning model designed for efficient reasoning workloads."
    },

    {
        "name": "Grok 3",
        "company": "xAI",
        "date": "2025-02-19",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Third-generation Grok model with enhanced reasoning and coding capabilities."
    },

    {
        "name": "Claude 3.7 Sonnet",
        "company": "Anthropic",
        "date": "2025-02-24",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Hybrid reasoning model supporting both standard and extended-thinking workflows."
    },

    {
        "name": "Mistral Small 3.1",
        "company": "Mistral AI",
        "date": "2025-03-17",
        "type": "Multimodal",
        "category": "Open Weight",
        "description": "Compact multimodal model designed for efficient local and enterprise deployment."
    },

    {
        "name": "Gemini 2.5 Pro",
        "company": "Google",
        "date": "2025-03-25",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Gemini 2.5 reasoning model focused on complex reasoning and coding."
    },

    {
        "name": "GPT-4.1",
        "company": "OpenAI",
        "date": "2025-04-14",
        "type": "LLM",
        "category": "Frontier",
        "description": "GPT model optimized for coding, instruction following and long-context tasks."
    },

    {
        "name": "o3",
        "company": "OpenAI",
        "date": "2025-04-16",
        "type": "Reasoning",
        "category": "Reasoning",
        "description": "Advanced reasoning model designed for difficult STEM, coding and analysis tasks."
    },

    {
        "name": "o4-mini",
        "company": "OpenAI",
        "date": "2025-04-16",
        "type": "Reasoning",
        "category": "Reasoning",
        "description": "Smaller reasoning model optimized for efficiency."
    },

    {
        "name": "Llama 4 Scout",
        "company": "Meta",
        "date": "2025-04-05",
        "type": "Multimodal",
        "category": "Open Weight",
        "description": "Native multimodal mixture-of-experts model with very long context support."
    },

    {
        "name": "Llama 4 Maverick",
        "company": "Meta",
        "date": "2025-04-05",
        "type": "Multimodal",
        "category": "Open Weight",
        "description": "Larger Llama 4 mixture-of-experts model designed for multimodal workloads."
    },

    {
        "name": "Qwen3",
        "company": "Alibaba",
        "date": "2025-04-28",
        "type": "Reasoning",
        "category": "Open Weight",
        "description": "Qwen generation with hybrid thinking and non-thinking modes."
    },

    {
        "name": "Claude 4 Opus",
        "company": "Anthropic",
        "date": "2025-05-22",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Claude 4 model focused on advanced reasoning, coding and agentic workflows."
    },

    {
        "name": "Claude 4 Sonnet",
        "company": "Anthropic",
        "date": "2025-05-22",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Claude 4 model designed for strong reasoning, coding and agent workflows."
    },

    {
        "name": "DeepSeek-V3.1",
        "company": "DeepSeek",
        "date": "2025-08-21",
        "type": "Reasoning",
        "category": "Open Weight",
        "description": "Updated DeepSeek model combining reasoning and general-purpose capabilities."
    },

    {
        "name": "GPT-5",
        "company": "OpenAI",
        "date": "2025-08-07",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Unified OpenAI model combining fast responses with deeper reasoning."
    },

    {
        "name": "Claude Opus 4.1",
        "company": "Anthropic",
        "date": "2025-08-05",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Updated Opus model focused on coding, reasoning and agentic tasks."
    },

    {
        "name": "Grok 4",
        "company": "xAI",
        "date": "2025-07-09",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Fourth-generation Grok model focused on reasoning and complex tasks."
    },

    {
        "name": "Grok 4.1",
        "company": "xAI",
        "date": "2025-11-17",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Updated Grok model with improved reasoning and general-purpose capabilities."
    },

    {
        "name": "GPT-5.2",
        "company": "OpenAI",
        "date": "2025-12-11",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "GPT-5 generation focused on professional knowledge work and long-running agents."
    },


    # ========================================================
    # 2026
    # ========================================================

    {
        "name": "Claude Opus 4.6",
        "company": "Anthropic",
        "date": "2026-02-05",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Advanced Claude model focused on coding, agents, reasoning and long-context work."
    },

    {
        "name": "Claude Sonnet 4.6",
        "company": "Anthropic",
        "date": "2026-02-17",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Sonnet generation focused on coding, computer use, reasoning and agent planning."
    },

    {
        "name": "Claude Sonnet 5",
        "company": "Anthropic",
        "date": "2026-06-30",
        "type": "Agentic",
        "category": "Frontier",
        "description": "Agent-focused Claude model designed for tool use, coding and autonomous workflows."
    },

    {
        "name": "Grok 4.5",
        "company": "xAI",
        "date": "2026-07-16",
        "type": "Reasoning",
        "category": "Frontier",
        "description": "Grok model focused on coding, agentic tasks and knowledge work."
    },

    {
        "name": "Grok 4.6",
        "company": "xAI",
        "date": "2026-08-12",
        "type": "Agentic",
        "category": "Frontier",
        "description": "Grok model focused on long-running agents and interactive workloads."
    },

    {
        "name": "GPT-6 Astra",
        "company": "OpenAI",
        "date": "2026-09-03",
        "type": "Agentic",
        "category": "Frontier",
        "description": "OpenAI's GPT-6 generation focused on computer use, software engineering, cybersecurity and professional work."
    },

    {
        "name": "Grok 4.7",
        "company": "xAI",
        "date": "2026-09-21",
        "type": "Agentic",
        "category": "Frontier",
        "description": "Grok generation focused on coding, knowledge work and longer-running tasks."
    },

    {
        "name": "Claude Opus 5.5",
        "company": "Anthropic",
        "date": "2026-09-22",
        "type": "Agentic",
        "category": "Frontier",
        "description": "Claude Opus generation focused on long-running agents, coding and professional work."
    }
]


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

    try:
        cpu = psutil.cpu_percent(interval=0.1)

        memory = psutil.virtual_memory()

        system_drive = Path.home().anchor

        disk = psutil.disk_usage(system_drive)

        return jsonify({
            "hostname": socket.gethostname(),
            "cpu": round(cpu, 1),
            "memory": round(memory.percent, 1),
            "disk": round(disk.percent, 1),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500


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
                "pid": info.get("pid"),
                "name": info.get("name") or "Unknown",
                "cpu": round(info.get("cpu_percent") or 0, 1),
                "memory": round(info.get("memory_percent") or 0, 1)
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied
        ):
            continue

    process_list.sort(
        key=lambda process: process["cpu"],
        reverse=True
    )

    return jsonify(process_list[:20])


# ============================================================
# ACTIVITY
# ============================================================

@app.route("/api/activity")
def activity():

    try:

        if not EVENT_FILE.exists():
            return jsonify([])

        with EVENT_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            events = json.load(file)

        if not isinstance(events, list):
            return jsonify([])

        latest_events = events[-50:]

        latest_events.reverse()

        return jsonify(latest_events)

    except json.JSONDecodeError as error:

        return jsonify({
            "error": "agent_events.json contains invalid JSON.",
            "details": str(error)
        }), 500

    except OSError as error:

        return jsonify({
            "error": "Unable to read agent_events.json.",
            "details": str(error)
        }), 500

    except Exception as error:

        return jsonify({
            "error": "Activity processing failed.",
            "details": str(error)
        }), 500


# ============================================================
# LOGS
# ============================================================

@app.route("/api/logs")
def logs():

    log_entries = []

    try:

        if not LOG_FILE.exists():
            return jsonify([])

        with LOG_FILE.open(
            "r",
            encoding="utf-8",
            errors="replace"
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

            log_entries.append({
                "time": line[:19],
                "type": log_type,
                "message": line
            })

        log_entries.reverse()

        return jsonify(log_entries)

    except Exception as error:

        return jsonify({
            "error": "Log processing failed.",
            "details": str(error)
        }), 500


# ============================================================
# CVE FEED
# ============================================================

@app.route("/api/cves")
def cves():

    try:

        url = (
            "https://services.nvd.nist.gov/"
            "rest/json/cves/2.0"
        )

        now = datetime.now(timezone.utc)

        start_date = now - timedelta(days=7)

        pub_start = start_date.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        pub_end = now.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        response = requests.get(
            url,
            params={
                "pubStartDate": pub_start,
                "pubEndDate": pub_end,
                "sortBy": "publishDate",
                "sortOrder": "desc",
                "resultsPerPage": 20,
                "startIndex": 0
            },
            headers={
                "User-Agent": "Security-Monitor-Dashboard/1.0"
            },
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        vulnerabilities = []

        for item in data.get("vulnerabilities", []):

            cve = item.get("cve", {})

            cve_id = cve.get(
                "id",
                "Unknown"
            )

            description = "No description available."

            for desc in cve.get(
                "descriptions",
                []
            ):

                if desc.get("lang") == "en":

                    description = desc.get(
                        "value",
                        description
                    )

                    break

            score = None

            severity = "UNKNOWN"

            metrics = cve.get(
                "metrics",
                {}
            )

            metric_groups = (
                "cvssMetricV40",
                "cvssMetricV31",
                "cvssMetricV30",
                "cvssMetricV2"
            )

            for metric_group in metric_groups:

                if metrics.get(metric_group):

                    metric = metrics[
                        metric_group
                    ][0]

                    cvss_data = metric.get(
                        "cvssData",
                        {}
                    )

                    score = cvss_data.get(
                        "baseScore"
                    )

                    severity = (
                        cvss_data.get(
                            "baseSeverity"
                        )
                        or metric.get(
                            "baseSeverity"
                        )
                        or "UNKNOWN"
                    )

                    break

            references = []

            for reference in cve.get(
                "references",
                []
            )[:3]:

                reference_url = reference.get(
                    "url"
                )

                if reference_url:
                    references.append(
                        reference_url
                    )

            vulnerabilities.append({

                "id": cve_id,

                "description": description,

                "score": score,

                "severity": severity,

                "published": cve.get(
                    "published"
                ),

                "modified": cve.get(
                    "lastModified"
                ),

                "references": references
            })

        return jsonify({

            "source": "NVD",

            "updated": now.isoformat(),

            "count": len(vulnerabilities),

            "vulnerabilities": vulnerabilities
        })

    except requests.exceptions.Timeout as error:

        return jsonify({
            "error": "NVD request timed out.",
            "details": str(error)
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Unable to reach NVD.",
            "details": str(error)
        }), 502

    except ValueError as error:

        return jsonify({
            "error": "Invalid JSON received from NVD.",
            "details": str(error)
        }), 502

    except Exception as error:

        return jsonify({
            "error": "CVE processing failed.",
            "details": str(error)
        }), 500


# ============================================================
# AI MODEL RELEASE FEED
# ============================================================

@app.route("/api/models")
def models():

    try:

        # Last three years relative to today.
        cutoff = datetime.now().date() - timedelta(days=365 * 3)

        filtered_models = []

        for model in AI_MODELS:

            release_date = datetime.strptime(
                model["date"],
                "%Y-%m-%d"
            ).date()

            if release_date >= cutoff:

                filtered_models.append(model)

        filtered_models.sort(
            key=lambda model: model["date"],
            reverse=True
        )

        return jsonify({
            "source": "Curated AI model release index",
            "updated": datetime.now(
                timezone.utc
            ).isoformat(),
            "period": {
                "from": cutoff.isoformat(),
                "to": datetime.now().date().isoformat()
            },
            "count": len(filtered_models),
            "models": filtered_models
        })

    except Exception as error:

        return jsonify({
            "error": "AI model feed processing failed.",
            "details": str(error)
        }), 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )