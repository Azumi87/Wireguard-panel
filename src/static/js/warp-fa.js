function toggleSpoiler(id) {
    const spoilerContent = document.getElementById(id);
    spoilerContent.classList.toggle('show');
}
document.addEventListener('DOMContentLoaded', function () {

    const spoilerToggles = document.querySelectorAll('.spoiler-toggle');
    spoilerToggles.forEach(toggle => {
        toggle.addEventListener('click', function () {
            const targetId = toggle.getAttribute('data-target'); 
            toggleSpoiler(targetId); 
        });
    });
    function showAlert(message) {
    const alertModal = document.getElementById("alertModal");
    const alertMessage = document.getElementById("alertMessage");

    alertMessage.textContent = message;
    alertModal.style.display = "flex";

    setTimeout(() => {
        alertModal.style.display = "none";
    }, 3000); 
}

    function showConfirm(message, callback) {
    const confirmModal = document.getElementById("confirmModal");
    const confirmMessage = document.getElementById("confirmMessage");
    const confirmYes = document.getElementById("confirmYes");
    const confirmNo = document.getElementById("confirmNo");

    confirmMessage.textContent = message;
    confirmModal.style.display = "flex";

    const safeCallback = typeof callback === "function" ? callback : () => {};

    confirmYes.onclick = () => {
        confirmModal.style.display = "none";
        safeCallback(true); 
    };

    confirmNo.onclick = () => {
        confirmModal.style.display = "none";
        safeCallback(false); 
    };
}
async function updateActiveGeosites() {
        try {
            const response = await fetch("/api/get-active-geosites");
            const data = await response.json();
            if (data.active_geosites) {
                const activeGeosites = data.active_geosites;
                activeGeosites.forEach((geosite) => {
                    const checkbox = document.querySelector(`input[name="geosites"][value="${geosite}"]`);
                    if (checkbox) {
                        checkbox.checked = true;  
                    }
                });
            } else {
                console.error("Couldn't fetch active geosites:", data.error);
            }
        } catch (error) {
            console.error("loading active geosites error:", error);
        }
    }

    updateActiveGeosites();

    async function updateStatus() {
        try {
            const warpResponse = await fetch('/warp/status');
            if (!warpResponse.ok) throw new Error(`fetching WARP status failed: ${warpResponse.status}`);
            const warpData = await warpResponse.json();

            const fullWarpStatusElement = document.getElementById('fullWarpStatus');
            const fullWarpStatus = warpData.wgcf_status === "Active" ? "فعال" : "غیرفعال";
            if (fullWarpStatusElement) {
                fullWarpStatusElement.textContent = fullWarpStatus.charAt(0).toUpperCase() + fullWarpStatus.slice(1);
                fullWarpStatusElement.className = `status-badge ${fullWarpStatus}`;
            }

            const xrayResponse = await fetch('/xray/status');
            if (!xrayResponse.ok) throw new Error(`fetching Xray status failed: ${xrayResponse.status}`);
            const xrayData = await xrayResponse.json();

            const xrayStatusElement = document.getElementById('xrayStatus');
            const xrayStatus = xrayData.xray_status === "Active" ? "فعال" : "غیرفعال";
            if (xrayStatusElement) {
                xrayStatusElement.textContent = xrayStatus.charAt(0).toUpperCase() + xrayStatus.slice(1);
                xrayStatusElement.className = `status-badge ${xrayStatus}`;
            }
        } catch (error) {
            console.error("error in fetching status:", error);

            const fullWarpStatusElement = document.getElementById('fullWarpStatus');
            const xrayStatusElement = document.getElementById('xrayStatus');

            if (fullWarpStatusElement) {
                fullWarpStatusElement.textContent = "Unknown";
                fullWarpStatusElement.className = "status-badge inactive";
            }

            if (xrayStatusElement) {
                xrayStatusElement.textContent = "Unknown";
                xrayStatusElement.className = "status-badge inactive";
            }
        }
    }

    setInterval(updateStatus, 5000);
    updateStatus();

    document.getElementById("installFullWARPButton").addEventListener("click", async () => {
    try {
        const response = await fetch("/warp/install", { method: "POST" });
        const data = await response.json();
        showAlert(data.message);
        updateStatus(); 
        pollProgress();  
    } catch (error) {
        console.error("error in Full WARP installation:", error);
        showAlert("نصب وارپ موفقیت امیز نبود");
    }
});

function pollProgress() {
    const progressBar = document.getElementById("installProgress");
    const progressText = document.getElementById("progressText");

    function fetchProgress() {
        fetch('/warp/install-progress')
            .then(response => response.json())
            .then(data => {
                console.log("Progress Data:", data); 
                const progress = data.progress;
                progressBar.value = progress;
                progressText.textContent = `${progress}%`;

                if (progress >= 100) {
                    progressText.textContent = "نصب انجام شد!";
                } else {
                    setTimeout(fetchProgress, 1000); 
                }
            })
            .catch(error => {
                console.error("error in fetching progress:", error);
            });
    }

    fetchProgress();  
}

    document.getElementById("stopFullWARPButton").addEventListener("click", async () => {
        try {
            const response = await fetch("/warp/stop", { method: "POST" });
            const data = await response.json();
            showAlert(data.message);
            updateStatus();
        } catch (error) {
            console.error("error in stopping FullWARP:", error);
            showAlert("متوقف کردن وارپ موفقیت امیز نبود");
        }
    });

    document.getElementById("resetFullWARPButton").addEventListener("click", async () => {
        try {
            const response = await fetch("/warp/reset", { method: "POST" });
            const data = await response.json();
            showAlert(data.message);
            updateStatus();
        } catch (error) {
            console.error("error in resetting FullWARP:", error);
            showAlert("ریست کردن وارپ موفقیت امیز نبود");
        }
    });

    document.getElementById("uninstallFullWARPButton").addEventListener("click", async () => {
        try {
            const response = await fetch("/warp/uninstall", { method: "POST" });
            const data = await response.json();
            showAlert(data.message);
            updateStatus();
        } catch (error) {
            console.error("error in uninstalling FullWARP:", error);
            showAlert("حذف وارپ موفقیت امیز نبود");
        }
    });

    document.getElementById("uninstallXrayWARPButton").addEventListener("click", async () => {
    try {
        const response = await fetch("/xray/uninstall", { method: "POST" });
        if (!response.ok) throw new Error("Couldn't uninstall XrayWARP.");
        const data = await response.json();
        showAlert(data.message);
        updateStatus();
    } catch (error) {
        console.error("error in uninstalling XrayWARP:", error);
        showAlert("حذف xray موفقیت امیز نبود");
    }
});


    document.getElementById("installXrayWARPButton").addEventListener("click", async () => {
    console.log("Install XrayWARP button clicked");

    try {
        const response = await fetch("/warp/install-xray", { method: "POST" });
        const data = await response.json();
        showAlert(data.message);   
        updateStatus();  

        pollProgress2();  
    } catch (error) {
        console.error("Xray + Warp installation error:", error);
        showAlert("نصب xray با وارپ موفقیت امیز نبود");
    }
}, { once: true });  

function pollProgress2() {
    const progressBar2 = document.getElementById("installProgress2");
    const progressText2 = document.getElementById("progressText2");

    function fetchProgress2() {
        fetch('/warp/install-xray-progress')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Progress Data:", data); 
                const progress = data.progress || 0;  

                progressBar2.value = progress;
                progressText2.textContent = `${progress}%`;

                if (progress >= 100) {
                    progressText2.textContent = "نصب انجام شد!";
                } else {
                    setTimeout(fetchProgress2, 1000); 
                }
            })
            .catch(error => {
                console.error("error in fetching progress:", error);
                progressText.textContent = "error in fetching progress!";
            });
    }

    fetchProgress2();  
}

    document.getElementById("stopXrayWARPButton").addEventListener("click", async () => {
        try {
            const response = await fetch("/xray/stop", { method: "POST" });
            const data = await response.json();
            showAlert(data.message);
            updateStatus();
        } catch (error) {
            console.error("stopping Xray + Warp error:", error);
            showAlert("متوقف کردن وارپ موفقیت امیز نبود");
        }
    });

    document.getElementById("resetXrayWARPButton").addEventListener("click", async () => {
        try {
            const response = await fetch("/xray/reset", { method: "POST" });
            const data = await response.json();
            showAlert(data.message);
            updateStatus();
        } catch (error) {
            console.error("resetting XrayWARP error:", error);
            showAlert("ریست کردن xray موفقیت امیز نبود");
        }
    });

    document.getElementById("geositesForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const geosites = Array.from(document.querySelectorAll('input[name="geosites"]:checked')).map(input => input.value);
        try {
            const response = await fetch("/warp/apply-geosites", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ geosites }),
            });
            const data = await response.json();
            showAlert(data.message);
        } catch (error) {
            console.error("applying geosites error:", error);
            showAlert("applying geosites failed.");
        }
    });
});