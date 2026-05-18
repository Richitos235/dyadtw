(function () {
    const STORAGE_KEY = "westbot_job_add";
    const INJECTED_ATTRIBUTE = "data-westbot-injected";
    const OBSERVER_CONFIG = { childList: true, subtree: true };

    function safeParse(value) {
        try {
            return JSON.parse(value);
        } catch (error) {
            return null;
        }
    }

    function buildButton(label, callbackName) {
        const button = document.createElement("button");
        button.innerText = label;
        button.style.margin = "4px 4px 4px 0";
        button.style.padding = "8px 12px";
        button.style.border = "1px solid rgba(255,255,255,.2)";
        button.style.background = "rgba(46, 134, 193, 0.95)";
        button.style.color = "#fff";
        button.style.cursor = "pointer";
        button.style.borderRadius = "4px";
        button.style.fontSize = "12px";
        button.addEventListener("click", () => window[callbackName] && window[callbackName]());
        return button;
    }

    function storeJobData(jobData) {
        if (!jobData || !jobData.jobId) {
            return;
        }

        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(jobData));
    }

    function extractJobPayload(root) {
        const jobIdElement = root.querySelector("[data-jobid], input[name='job_id'], [id*='job_id']");
        const jobId = jobIdElement ? parseInt(jobIdElement.getAttribute("data-jobid") || jobIdElement.value || jobIdElement.textContent, 10) : null;
        const titleElement = root.querySelector(".job_title, .headline, h1, h2, .window_header");
        const name = titleElement ? titleElement.textContent.trim() : "Neznáma práca";
        const motivationElement = root.querySelector(".motivation, .job_motivation, .motivation_label");
        const motivation = motivationElement ? parseFloat(motivationElement.textContent.replace(/[^0-9\.]/g, "")) : null;
        const durationElement = root.querySelector("[name='duration'], .duration_value, .job_duration");
        const duration = durationElement ? parseInt(durationElement.value || durationElement.textContent.replace(/[^0-9]/g, ""), 10) : 15;
        const coords = { x: null, y: null };
        const coordinateElements = root.querySelectorAll(".job_coordinates, .coordinates, .pos, .coordinate");

        coordinateElements.forEach((element) => {
            const value = element.textContent.replace(/[^0-9\-]/g, "");
            if (!coords.x) {
                coords.x = parseInt(value, 10);
            } else if (!coords.y) {
                coords.y = parseInt(value, 10);
            }
        });

        return {
            jobId,
            name,
            x: coords.x || 0,
            y: coords.y || 0,
            duration: duration || 15,
            motivation: motivation || 100
        };
    }

    function extractJobContainers() {
        const containers = Array.from(document.querySelectorAll(".jobWindow, .jobOverlay, .job-detail, .window_content")).filter((element) => {
            return !element.hasAttribute(INJECTED_ATTRIBUTE) && element.contains(document.querySelector("button[data-job-action]")) === false;
        });
        return containers;
    }

    function injectControls(root) {
        if (root.hasAttribute(INJECTED_ATTRIBUTE)) {
            return;
        }
        const payload = extractJobPayload(root);
        if (!payload.jobId) {
            return;
        }

        const container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexWrap = "wrap";
        container.style.marginTop = "12px";
        container.style.alignItems = "center";

        const startButton = buildButton("START", "westbotStartJob");
        const addButton = buildButton("PRIDAŤ", "westbotAddJob");

        window.westbotStartJob = function () {
            storeJobData(Object.assign({}, payload, { action: "start" }));
        };

        window.westbotAddJob = function () {
            storeJobData(Object.assign({}, payload, { action: "queue" }));
        };

        container.appendChild(startButton);
        container.appendChild(addButton);
        root.appendChild(container);
        root.setAttribute(INJECTED_ATTRIBUTE, "1");
    }

    function injectIntoDocument() {
        const targets = extractJobContainers();
        targets.forEach((target) => injectControls(target));
    }

    const observer = new MutationObserver(() => {
        injectIntoDocument();
    });

    function initialize() {
        injectIntoDocument();
        observer.observe(document.body, OBSERVER_CONFIG);
    }

    if (document.readyState === "complete" || document.readyState === "interactive") {
        initialize();
    } else {
        window.addEventListener("DOMContentLoaded", initialize);
    }
})();
