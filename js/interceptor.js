(function() {
    const BACKEND_URL = "http://localhost:8000/api/jobs/log";
    const TARGET_PATTERN = "window=task&action=add";

    const XHR = XMLHttpRequest.prototype;
    const open = XHR.open;
    const send = XHR.send;

    // Helper to parse form-encoded data
    function parseParams(str) {
        const params = new URLSearchParams(str);
        const result = {};
        for (const [key, value] of params) {
            // Handle tasks[0][jobId] style keys
            const match = key.match(/tasks\[0\]\[(.*?)\]/);
            if (match) {
                result[match[1]] = value;
            } else {
                result[key] = value;
            }
        }
        return result;
    }

    XHR.open = function(method, url) {
        this._url = url;
        this._method = method;
        return open.apply(this, arguments);
    };

    XHR.send = function(postData) {
        if (this._url && this._url.includes(TARGET_PATTERN) && postData) {
            try {
                const data = parseParams(postData);
                
                // Attempt to grab the job name from the DOM if a job window is open
                let jobName = "Unknown Job";
                const titleElem = document.querySelector('.jobwindow .headline, .jobwindow .textart_title');
                if (titleElem) {
                    jobName = titleElem.textContent.trim().split('(')[0].trim();
                }

                const payload = {
                    jobId: parseInt(data.jobId || 0),
                    x: parseInt(data.x || 0),
                    y: parseInt(data.y || 0),
                    duration: parseInt(data.duration || 15),
                    taskType: data.taskType || "job",
                    name: jobName,
                    timestamp: new Date().toISOString()
                };

                // Send to our local backend
                fetch(BACKEND_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                    mode: "cors"
                }).catch(err => console.error("Audit Log Error:", err));

            } catch (e) {
                console.error("Interceptor parsing failed", e);
            }
        }
        return send.apply(this, arguments);
    };

    console.log("WestBot Audit Interceptor Active");
})();