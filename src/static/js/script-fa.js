document.addEventListener("DOMContentLoaded", () => {
    function showAlert(message) {
        const alertModal = document.getElementById("alertModal");
        const alertMessage = document.getElementById("alertMessage");

        if (alertModal && alertMessage) {
            alertMessage.textContent = message;
            alertModal.style.display = "flex";

            setTimeout(() => {
                alertModal.style.display = "none";
            }, 3000);
        } else {
            alert(message);
        }
    }

    function showConfirm(message, callback) {
        const confirmModal = document.getElementById("confirmModal");
        const confirmMessage = document.getElementById("confirmMessage");
        const confirmYes = document.getElementById("confirmYes");
        const confirmNo = document.getElementById("confirmNo");

        if (confirmModal && confirmMessage && confirmYes && confirmNo) {
            confirmMessage.textContent = message;
            confirmModal.style.display = "flex";

            confirmYes.onclick = () => {
                confirmModal.style.display = "none";
                callback(true);
            };

            confirmNo.onclick = () => {
                confirmModal.style.display = "none";
                callback(false);
            };
        } else {
            if (confirm(message)) {
                callback(true);
            } else {
                callback(false);
            }
        }
    }

    const generateKeysButton = document.getElementById("generateKeys");
    const bulkAddCheckbox = document.getElementById("bulkAdd");
    const bulkPeerCountContainer = document.getElementById("bulkPeerCountContainer");
    const peerForm = document.getElementById("peerForm");
    const configSelect = document.getElementById("configSelect");
    const toggleConfig = document.getElementById("toggleConfig");
    const peerContainer = document.getElementById("peerContainer");
    const peerListCard = document.getElementById("peerList");
    const peerIpSelect = document.getElementById("peerIp");
    const qrCodeModal = document.getElementById("qrCodeModal");
    const qrCodeCanvas = document.getElementById("qrCodeCanvas");
    const saveQrCode = document.getElementById("saveQrCode");
    const closeQrModal = document.getElementById("closeQrModal");
    const deleteAllBtn = document.getElementById("deleteAllBtn");
    const deletePeerModal = document.getElementById("deletePeerModal");
    const deleteAllModal = document.getElementById("deleteAllModal");
    const closeDeletePeerModal = document.getElementById("closeDeletePeerModal");
    const closeDeleteAllModal = document.getElementById("closeDeleteAllModal");
    const confirmDeletePeer = document.getElementById("confirmDeletePeer");
    const confirmDeleteAll = document.getElementById("confirmDeleteAll");
    const cancelDeletePeer = document.getElementById("cancelDeletePeer");
    const cancelDeleteAll = document.getElementById("cancelDeleteAll");
    const statusSpan = document.getElementById("wg-status");
    const toggleInterfaceBtn = document.getElementById("toggleInterfaceBtn");
    const privateKeySpan = document.getElementById("wg-private-key");
    const toggleKeyBtn = document.getElementById("toggleKeyBtn");
    const logsBox = document.getElementById('logsBox');
    const logsModal = document.getElementById('logsModal');
    const closeLogsModal = document.getElementById('closeLogsModal');
    const logsContent = document.getElementById('logsContent');
    const logFilter = document.getElementById('logFilter');
    const refreshLogs = document.getElementById('refreshLogs');
    const ipv4Address = document.getElementById('ipv4Address');
    const ipv6Address = document.getElementById('ipv6Address');

    if (generateKeysButton) {
        console.log("Attaching to 'generateKeys' button.");
        generateKeysButton.addEventListener("click", async () => {
            try {
                console.log("Generate Keys button clicked.");
                const response = await fetch("/api/generate-keys");
                const data = await response.json();

                if (data.error) {
                    showAlert("خطایی در تولید کلید ها پیش امد " + data.error);
                    return;     
                }

                const publicKeyInput = document.getElementById("publicKey");
                if (publicKeyInput) {
                    publicKeyInput.value = data.publicKey;
                    console.log("Public key generated.");
                } else {
                    console.error("ID 'publicKey' not found.");
                }
            } catch (error) {
                console.error("Generating keys failed:", error);
                showAlert("خطایی در تولید کلید پیش امد");
            }
        });
    } else {
        console.error("ID 'generateKeys' not found.");
    }

    if (bulkAddCheckbox) {
        console.log("Attaching to 'bulkAdd' checkbox.");
        bulkAddCheckbox.addEventListener("change", (event) => {
            if (bulkPeerCountContainer) {
                if (event.target.checked) {
                    bulkPeerCountContainer.style.display = "block";
                    console.log("Bulk Add checked. Showing its stuff.");
                } else {
                    bulkPeerCountContainer.style.display = "none";
                    console.log("Bulk Add unchecked. Hiding its stuff.");
                }
            } else {
                console.error("ID 'bulkPeerCountContainer' not found.");
            }
        });
    } else {
        console.error("ID 'bulkAdd' not found.");
    }

    if (peerForm) {
        console.log("Attaching submitform to 'peerForm'.");
        peerForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            console.log("submitform triggered.");

            const peerName = document.getElementById("peerName").value.trim();
            const peerIp = document.getElementById("peerIp").value.trim();
            const dataLimit = document.getElementById("dataLimit").value.trim();
            const dataLimitUnit = document.getElementById("dataLimitUnit").value; 
            const dns = document.getElementById("dns").value.trim(); 
            const expiryDays = parseInt(document.getElementById("expiryDays").value) || 0;
            const expiryMonths = parseInt(document.getElementById("expiryMonths").value) || 0;
            const expiryHours = parseInt(document.getElementById("expiryHours").value) || 0;
            const expiryMinutes = parseInt(document.getElementById("expiryMinutes").value) || 0;
            const config = document.getElementById("configSelect").value;
            const firstUsage = document.getElementById("firstUsage").checked;
            const persistentKeepalive = parseInt(document.getElementById("persistentKeepalive").value) || 25; 
            const mtu = parseInt(document.getElementById("mtu").value) || 1280; 
            const bulkAdd = document.getElementById("bulkAdd").checked;
            const bulkPeerCount = bulkAdd ? parseInt(document.getElementById("bulkPeerCount").value) || 1 : 1;

            if (!peerName || !peerIp || !dataLimit || !config) {
                showAlert("تمام قسمت های مورد نیاز را پر کنید");
                console.warn("Validation failed: Missing required fields.");
                return;
            }

            if (bulkAdd && (isNaN(bulkPeerCount) || bulkPeerCount < 1 || bulkPeerCount > 100)) {
                showAlert("لطفا بین 1 تا 50 تعداد کاربر انتخاب نمایید");
                console.warn("Validation failed: Invalid bulkPeerCount.");
                return;
            }

            const dataLimitValue = `${dataLimit}${dataLimitUnit}`;

            console.log("Expiry Fields Captured:");
            console.log("Days:", expiryDays, "Months:", expiryMonths, "Hours:", expiryHours, "Minutes:", expiryMinutes);

            const payload = {
                peerName,
                peerIp,
                dataLimit: dataLimitValue,
                configFile: config,
                dns, 
                expiryDays,
                expiryMonths,
                expiryHours,
                expiryMinutes,
                firstUsage,
                persistentKeepalive, 
                mtu, 
                bulkCount: bulkAdd ? bulkPeerCount : 1
            };

            console.log("Payload being sent to backend:", payload);

            try {
                const response = await fetch(`/api/create-peer`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                const data = await response.json();

                if (response.ok) {
                    if (bulkAdd) {
                        showAlert(`${data.message}`);
                        data.peers.forEach(peer => {
                            console.log(`Peer Created: ${peer.peer_name}, IP: ${peer.peer_ip}, Short Link: ${peer.short_link}`);
                        });
                    } else {
                        showAlert("کاربر با موفقیت ساخته شد");
                    }

                    document.getElementById("peerName").value = "";
                    document.getElementById("peerIp").value = "";
                    document.getElementById("publicKey").value = "";
                    document.getElementById("dataLimit").value = "";
                    document.getElementById("dataLimitUnit").value = "MiB";
                    document.getElementById("expiryDays").value = "";
                    document.getElementById("expiryMonths").value = "";
                    document.getElementById("expiryHours").value = "";
                    document.getElementById("expiryMinutes").value = "";
                    document.getElementById("firstUsage").checked = false;
                    document.getElementById("persistentKeepalive").value = 25; 
                    document.getElementById("mtu").value = 1280; 
                    document.getElementById("bulkAdd").checked = false;
                    document.getElementById("bulkPeerCount").value = "";
                    if (bulkPeerCountContainer) {
                        bulkPeerCountContainer.style.display = "none";
                    }
                    const createPeerModal = document.getElementById("createPeerModal");
                    if (createPeerModal) {
                        createPeerModal.style.display = "none";
                    }

                    if (typeof fetchPeers === "function") {
                        fetchPeers(config);
                    } else {
                        console.warn("Func 'fetchPeers' is not defined.");
                    }
                } else {
                    showAlert("خطای ساخت کاربر: " + data.error);
                    console.error("Backend returned an error:", data.error);
                }
            } catch (error) {
                console.error("error in fetch:", error);
                showAlert("ساخت کاربر موفقیت امیز نبود");
            }
        });
    } else {
        console.error("ID 'peerForm' not found.");
    }

    if (toggleConfig && peerContainer) {
        toggleConfig.addEventListener("click", () => {
            peerContainer.style.display = peerContainer.style.display === "none" ? "block" : "none";
        });
    }

async function showQrCode(peerName, config) {
    const qrCodeModal = document.getElementById("qrCodeModal");
    const qrCodeCanvas = document.getElementById("qrCodeCanvas");
    const saveQrCode = document.getElementById("saveQrCode");

    qrCodeModal.style.display = "flex";

    const response = await fetch(`/api/export-peer?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(config)}`);
    const peerConfig = await response.text();

    QRCode.toCanvas(qrCodeCanvas, peerConfig, { width: 300 }, (error) => {
        if (error) console.error(error);
        console.log("QR Code generated!");
    });

    saveQrCode.onclick = () => {
        const link = document.createElement("a");
        link.href = qrCodeCanvas.toDataURL("image/png");
        link.download = `${peerName}-qr-code.png`;
        link.click();
    };
}
document.getElementById("closeQrModal").addEventListener("click", () => {
    const qrCodeModal = document.getElementById("qrCodeModal");
    qrCodeModal.style.display = "none";
});

async function fetchSpeedData() {
    try {
        const response = await fetch('/api/speed'); 
        const data = await response.json();
        const uploadSpeed = formatSpeed(data.uploadSpeed);
        const downloadSpeed = formatSpeed(data.downloadSpeed);

        document.getElementById('uploadSpeed').textContent = uploadSpeed;
        document.getElementById('downloadSpeed').textContent = downloadSpeed;
    } catch (error) {
        console.error('fetching speed data error:', error);
    }
}

function formatSpeed(speed) {
    return speed >= 1024
        ? `${(speed / 1024).toFixed(2)} MB/s`
        : `${speed.toFixed(2)} KB/s`;
}


logsBox.addEventListener('click', () => {
    logsModal.style.display = 'flex';
    fetchLogs(logFilter.value);
});

closeLogsModal.addEventListener('click', () => {
    logsModal.style.display = 'none';
});

async function fetchLogs(limit = 20) {
    try {
        const response = await fetch(`/api/logs?limit=${limit}`);
        const data = await response.json();
        logsContent.innerHTML = data.logs.map(log => `<p>${log}</p>`).join('');
    } catch (error) {
        logsContent.innerHTML = '<p>خطای بازگذاری گزارش ها</p>';
    }
}

refreshLogs.addEventListener('click', () => {
    fetchLogs(logFilter.value);
});

const clearLogs = document.getElementById('clearLogs');

clearLogs.addEventListener('click', async () => {
    if (showConfirm('آیا مطمئن هستید که می‌خواهید همه گزارش‌ها را پاک کنید؟ این عملیات قابل بازگشت نیست.')) {
        try {
            const response = await fetch('/api/logs', {
                method: 'DELETE'
            });

            if (response.ok) {
                logsContent.innerHTML = '<p>گزارش‌ها با موفقیت پاک شدند.</p>';
            } else {
                logsContent.innerHTML = '<p>خطا در پاک کردن گزارش‌ها.</p>';
            }
        } catch (error) {
            logsContent.innerHTML = '<p>خطا در پاک کردن گزارش‌ها.</p>';
        }
    }
});


document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('.sidebar ul li a');
    links.forEach(link => {
        link.addEventListener('mouseover', () => {
            link.style.opacity = '0.8'; 
        });
        link.addEventListener('mouseout', () => {
            link.style.opacity = '1';
        });
    });
});

async function fetchServerIPs() {
    try {
        const response = await fetch('/api/server-ips');
        const data = await response.json();

        ipv4Address.textContent = data.public_ipv4 || 'در دسترس نیست';
        ipv6Address.textContent = data.public_ipv6 || 'در دسترس نیست';
    } catch (error) {
        ipv4Address.textContent = 'خطا';
        ipv6Address.textContent = 'خطا';
    }
}


document.getElementById('serverIPBox').addEventListener('mouseover', fetchServerIPs);

    if (!configSelect || !statusSpan || !toggleInterfaceBtn || !privateKeySpan || !toggleKeyBtn) {
        console.error("One or more required elements are missing.");
        showAlert("Critical UI elements are missing. use F12.");
        return; 
    }

    console.log("required elements found. Starting..");
                let selectedPeerName = null;
                function toggleModal(modalId, show = true) {
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        modal.style.display = show ? "flex" : "none";
                    }
                }
document.getElementById("toggleConfig").addEventListener("click", async () => {
    const button = document.getElementById("toggleConfig");
    const action = button.textContent.trim() === "فعال کنید" ? "enable" : "disable";
    try {
        const response = await fetch("/api/toggle-interface", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ action }),
        });

        if (!response.ok) {
            const error = await response.json();
            showAlert(`خطا: ${error.message}`);
            return;
        }

        const result = await response.json();
        showAlert(result.message);

        button.textContent = action === "enable" ? "غیرفعال" : "فعال کنید";
    } catch (error) {
        console.error("خطا در تغییر وضعیت اینترفیس:", error);
    }
});


document.addEventListener("click", async (event) => {
    if (event.target.classList.contains("peer-toggle-btn")) {
        const button = event.target;
        const peerName = button.getAttribute("data-peer-name");
        const action = button.textContent.trim() === "فعال کردن" ? "فعال کردن" : "غیرفعال کردن";

        try {
            const response = await fetch("/api/toggle-peer", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ peerName, action }),
            });

            if (!response.ok) {
                const error = await response.json();
                showAlert(`خطا: ${error.message}`);
                return;
            }

            const result = await response.json();
            showAlert(result.message);

            button.textContent = action === "فعال کردن" ? "غیرفعال کردن" : "فعال کردن";

            if (isFiltering || isSearching) {
                applyFilter(); 
            } else {
                fetchPeers(configSelect.value); 
            }
        } catch (error) {
            console.error("خطا در تغییر وضعیت کاربر:", error);
            showAlert("خطایی در تغییر وضعیت کاربر رخ داد.");
        }
    }
});



document.getElementById("closeEditModal").addEventListener("click", closeEditModal);
    function closeEditModal() {
    const editPeerModal = document.getElementById("editPeerModal");
    if (editPeerModal) {
        editPeerModal.style.display = "none"; 
    } else {
        console.error("Edit Peer Modal not found.");
    }
}

confirmDeletePeer.addEventListener("click", async () => {
                    try {
                        const response = await fetch("/api/delete-peer", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ peerName: selectedPeerName }),
                        });
                        const data = await response.json();
                        showAlert(data.message || "کاربر با موفقیت حذف شد");
                        toggleModal("deletePeerModal", false);
                        location.reload();
                    } catch (error) {
                        console.error("Error deleting peer:", error);
                        showAlert("خطایی در پاک کردن کاربر رخ داده است");
                    }
                });

deleteAllBtn.addEventListener("click", () => toggleModal("deleteAllModal", true));

confirmDeleteAll.addEventListener("click", async () => {
    try {
        const response = await fetch("/api/delete-all-configs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmation: true }),
        });
        const data = await response.json();
        showAlert(data.message || "تمام کانفیگ‌ها با موفقیت حذف شدند.");
        toggleModal("deleteAllModal", false);
        location.reload();
    } catch (error) {
        console.error("خطا در حذف تمامی کانفیگ‌ها:", error);
        showAlert("خطا در حذف تمامی کانفیگ‌ها.");
    }
});

cancelDeletePeer.addEventListener("click", () => toggleModal("deletePeerModal", false));
cancelDeleteAll.addEventListener("click", () => toggleModal("deleteAllModal", false));
closeDeletePeerModal.addEventListener("click", () => toggleModal("deletePeerModal", false));
closeDeleteAllModal.addEventListener("click", () => toggleModal("deleteAllModal", false));
                
const updateProgressBar = (circleId, value, maxValue = 100) => {
    const circle = document.querySelector(`#${circleId}`);
    const percentage = Math.min((value / maxValue) * 100, 100); 
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDasharray = `${circumference}`;
    circle.style.strokeDashoffset = `${offset}`;

    const valueElement = document.querySelector(`#${circleId.replace("progress", "value")}`);
    valueElement.textContent = `${Math.round(value)}%`;
    };
    const fetchMetrics = async () => {
        try {
            const response = await fetch("/api/metrics");

            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            updateProgressBar("cpu-progress", parseFloat(data.cpu) || 0);
            updateProgressBar("ram-progress", parseFloat(data.ram) || 0);
            updateProgressBar("disk-progress", parseFloat(data.disk?.percent) || 0);
            const uptimeElement = document.querySelector("#uptime-value");
            uptimeElement.textContent = data.uptime || "0d 0h 0m";
        } catch (error) {
            console.error("fetching metrics error:", error);
            updateProgressBar("cpu-progress", 0);
            updateProgressBar("ram-progress", 0);
            updateProgressBar("disk-progress", 0);
            const uptimeElement = document.querySelector("#uptime-value");
            uptimeElement.textContent = "N/A";
        }
    };

const fetchConfigs = async () => {
    try {
        const response = await fetch("/api/configs");
        const data = await response.json();
        configSelect.innerHTML = '<option value="" disabled selected>یک کانفیگ را انتخاب کنید</option>';
        if (data.configs && data.configs.length > 0) {
            const defaultConfig = data.configs.includes("wg0.conf") ? "wg0.conf" : data.configs[0];
            data.configs.forEach(config => {
                const option = document.createElement("option");
                option.value = config;
                option.textContent = config;
                if (config === defaultConfig) {
                    option.selected = true;
                }
                configSelect.appendChild(option);
            });
            await loadWireGuardDetails(defaultConfig);
            await fetchPeers(defaultConfig);
        } else {
            console.warn("هیچ کانفیگ وایرگاردی در دسترس نیست.");
            showAlert("هیچ کانفیگ وایرگاردی پیدا نشد. تنظیمات سرور خود را بررسی کنید.");
        }
    } catch (error) {
        console.error("خطا در دریافت پیکربندی‌ها:", error);
        showAlert("خطا در دریافت کانفیگ‌ها. سرور خود را بررسی کرده و دوباره تلاش کنید.");
    }
};

    
const fetchAvailableIps = async (config) => {
    try {
        const response = await fetch(`/api/available-ips?config=${config}`);
        const data = await response.json();
        peerIpSelect.innerHTML = '<option value="" disabled selected>یک آدرس IP موجود را انتخاب کنید</option>';
        data.availableIps.forEach(ip => {
            const option = document.createElement("option");
            option.value = ip;
            option.textContent = ip;
            peerIpSelect.appendChild(option);
        });
    } catch (error) {
        console.error("خطا در دریافت آدرس‌های IP موجود:", error);
    }
};

toggleConfig.addEventListener("click", async () => {
    const config = toggleConfig.dataset.config;
    const active = toggleConfig.dataset.active === "true";
    try {
        const response = await fetch(`/api/toggle-config?config=${config}&active=${!active}`, {
            method: "POST"
        });
        const data = await response.json();
        showAlert(data.message || "موفقیت امیر بود");
    } catch (error) {
        console.error("toggling configuration error:", error);
    } 
});

let peersData = []; 
let currentPage = 1; 
let totalPages = 0; 
const limit = 10; 
let isPaginationChanging = false;

const fetchPeers = async (config, page = currentPage, isPagination = false) => {
    try {
        if (isPagination) {
            showLoadingSpinner();
            isPaginationChanging = true; 
        }

        const response = await fetch(
            `/api/peers?config=${config}&page=${page}&limit=${limit}`
        );
        const data = await response.json();

        if (response.ok) {
            peersData = data.peers || [];
            totalPages = data.total_pages || 0;

            currentPage = page;

            renderPeers(peersData, config);
            renderPagination(currentPage, totalPages, config);
        } else {
            console.error(data.error || "دریافت کاربران ناموفق بود.");
            showAlert(data.error || "دریافت کاربران ناموفق بود.");
        }
    } catch (error) {
        console.error("خطا در دریافت کاربران:", error);
        showAlert("خطا در دریافت کاربران. لطفا دوباره تلاش کنید.");
    } finally {
        if (isPagination) {
            hideLoadingSpinner();
            isPaginationChanging = false; 
        }
    }
};


const showLoadingSpinner = () => {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.style.display = "flex";
};

const hideLoadingSpinner = () => {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.style.display = "none";
};


const renderPeers = (peers, config) => {
    const peerContainer = document.getElementById("peerContainer");
    peerContainer.innerHTML = "";

    if (peers && peers.length > 0) {
        peers.forEach(peer => {
            const peerBox = document.createElement("div");
            peerBox.className = "peer-box";

            const header = document.createElement("div");
            header.className = "header";

            const peerName = document.createElement("strong");
            peerName.textContent = peer.peer_name || "Peer بدون نام";

            const isBlocked = peer.monitor_blocked || peer.expiry_blocked;
            const toggleIcon = document.createElement("div");
            toggleIcon.className = `toggle-icon ${isBlocked ? "inactive" : "active"}`;
            toggleIcon.title = isBlocked ? "فعال کردن کاربر" : "غیرفعال کردن کاربر";

            toggleIcon.onclick = async () => {
                try {
                    const response = await fetch("/api/toggle-peer", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            peerName: peer.peer_name,
                            blocked: !isBlocked,
                            config: config
                        }),
                    });

                    const result = await response.json();
                    if (response.ok) {
                        showAlert(result.message || `Peer ${peer.peer_name} updated successfully.`);
                        fetchPeers(config);
                    } else {
                        showAlert(result.error || "تغییر وضعیت کاربر ناموفق بود.");
                    }
                } catch (error) {
                    console.error("خطا در تغییر وضعیت کاربر:", error);
                    showAlert("خطایی رخ داد. دوباره تلاش کنید.");
                }
            };

            const status = document.createElement("div");
            status.className = `status ${isBlocked ? "inactive" : "active"}`;
            status.textContent = isBlocked ? "غیرفعال" : "فعال";

            const shortLinkBtn = document.createElement("button");
            shortLinkBtn.title = "لینک کوتاه";
            shortLinkBtn.classList.add("short-link-btn");
            shortLinkBtn.innerHTML = `<i class="fas fa-link"></i>`;

            shortLinkBtn.onclick = async () => {
                try {
                    if (peer.short_link) {
                        copyToClipboard(peer.short_link);
                        showAlert("لینک کوتاه کپی شد!");
                    } else {
                        const url = `/api/get-peer-link?peerName=${encodeURIComponent(peer.peer_name)}&config=${encodeURIComponent(peer.config)}`;
                        const response = await fetch(url);
                        const data = await response.json();

                        if (response.ok && data.short_link) {
                            peer.short_link = data.short_link;
                            copyToClipboard(peer.short_link);
                            showAlert("لینک کوتاه کپی شد!");
                        } else {
                            showAlert(data.error || "لینک کوتاه یافت نشد.");
                        }
                    }
                } catch (err) {
                    console.error("خطا در گرفتن لینک کوتاه:", err);
                    showAlert("خطایی رخ داد. دوباره تلاش کنید.");
                }
            };

            header.appendChild(peerName);
            header.appendChild(shortLinkBtn);
            header.appendChild(status);
            header.appendChild(toggleIcon);

            const remainingTimeElement = document.createElement("p");
            const updateRemainingTime = () => {
                const remainingMinutes = peer.remaining_time;
                if (remainingMinutes <= 0) {
                    remainingTimeElement.textContent = "زمان باقی‌مانده: منقضی شده";
                    toggleIcon.className = "toggle-icon inactive";
                    toggleIcon.title = "فعال کردن کاربر";
                    clearInterval(timer);
                    return;
                }

                const days = Math.floor(remainingMinutes / (24 * 60));
                const hours = Math.floor((remainingMinutes % (24 * 60)) / 60);
                const minutes = remainingMinutes % 60;

                remainingTimeElement.textContent = `زمان باقی‌مانده: ${days} روز ${hours} ساعت ${minutes} دقیقه`;
            };

            const timer = setInterval(() => {
                if (peer.remaining_time > 0) {
                    peer.remaining_time -= 1;
                    updateRemainingTime();
                } else {
                    clearInterval(timer);
                }
            }, 60000);

            updateRemainingTime();

            const content = document.createElement("div");
            content.className = "content";
            content.innerHTML = `
                <p dir="rtl">آدرس IP: <span dir="ltr">${peer.peer_ip || "نامشخص"}</span></p>
                <p dir="rtl">مصرف شده: <span dir="ltr">${peer.used_human || "0 MiB"}</span> / <span dir="ltr">${peer.limit_human || "نامحدود"}</span></p>
                <p dir="rtl">حجم باقی‌مانده: <span dir="ltr">${peer.remaining_human || "ناموجود"}</span></p>
            `;

            content.appendChild(remainingTimeElement);

            const footer = document.createElement("div");
            footer.className = "footer";

            const actions = document.createElement("div");
            actions.className = "actions";

            const downloadBtn = document.createElement("button");
            downloadBtn.title = "دانلود کانفیگ";
            downloadBtn.innerHTML = `<i class="fas fa-download"></i>`;
            downloadBtn.onclick = () => downloadPeerConfig(peer.peer_name, config);

            const qrCodeBtn = document.createElement("button");
            qrCodeBtn.title = "نمایش qr کد";
            qrCodeBtn.innerHTML = `<i class="fas fa-qrcode"></i>`;
            qrCodeBtn.onclick = () => showQrCode(peer.peer_name, config);

            const resetBtn = document.createElement("button");
            resetBtn.title = "ریست ترافیک";
            resetBtn.innerHTML = `<i class="fas fa-sync-alt"></i>`;
            resetBtn.onclick = async () => {
                try {
                    const response = await fetch("/api/reset-traffic", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            peerName: peer.peer_name,
                            config: config,
                        }),
                    });
                    const data = await response.json();
                    if (response.ok) {
                        showAlert(data.message || "ترافیک با موفقیت ریست شد");
                        fetchPeers(config);
                    } else {
                        showAlert(data.error || "ریست ترافیک ناموفق بود.");
                    }
                } catch (error) {
                    console.error("خطا در ریست ترافیک:", error);
                    showAlert("خطایی رخ داد. دوباره تلاش کنید.");
                }
            };

            const resetExpiryBtn = document.createElement("button");
            resetExpiryBtn.title = "ریست تاریخ انقضا";
            resetExpiryBtn.innerHTML = `<i class="fas fa-clock"></i>`;
            resetExpiryBtn.onclick = async () => {
                try {
                    const response = await fetch("/api/reset-expiry", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            peerName: peer.peer_name,
                            config: config,
                        }),
                    });
                    const data = await response.json();
                    if (response.ok) {
                        showAlert(data.message || "ریست موفقیت‌آمیز بود");
                        fetchPeers(config);
                    } else {
                        showAlert(data.error || "ریست تاریخ انقضا ناموفق بود.");
                    }
                } catch (error) {
                    console.error("خطا در ریست تاریخ انقضا:", error);
                }
            };

            const deleteBtn = document.createElement("button");
            deleteBtn.title = "حذف کاربر";
            deleteBtn.innerHTML = `<i class="fas fa-trash-alt"></i>`;
            deleteBtn.onclick = async () => {
                showConfirm(`آیا از حذف کاربر ${peer.peer_name} اطمینان دارید؟`, async (confirmed) => {
                    if (confirmed) {
                        try {
                            const configFile = peer.config || "wg0.conf";

                            const response = await fetch("/api/delete-peer", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    peerName: peer.peer_name,
                                    configFile: configFile,
                                    peerIp: peer.peer_ip,
                                }),
                            });

                            const result = await response.json();
                            if (response.ok) {
                                showAlert(result.message || "کاربر با موفقیت حذف شد");

                                peersData = peersData.filter(
                                    (p) => !(p.peer_name === peer.peer_name && p.peer_ip === peer.peer_ip)
                                );

                                if (peersData.length === 0 && currentPage > 1) {
                                    currentPage -= 1;
                                }

                                fetchPeers(configFile, currentPage, false);
                            } else {
                                showAlert(result.error || "خطا در حذف کاربر.");
                            }
                        } catch (error) {
                            console.error("خطا در حذف کاربر:", error);
                        }
                    }
                });
            };

            const editBtn = document.createElement("button");
            editBtn.title = "ویرایش کاربر";
            editBtn.innerHTML = `<i class="fas fa-edit"></i>`;
            editBtn.onclick = () => openEditPeerModal(peer);

            actions.appendChild(downloadBtn);
            actions.appendChild(qrCodeBtn);
            actions.appendChild(resetBtn);
            actions.appendChild(resetExpiryBtn);
            actions.appendChild(deleteBtn);
            actions.appendChild(editBtn);

            footer.appendChild(actions);

            peerBox.appendChild(header);
            peerBox.appendChild(content);
            peerBox.appendChild(footer);
            peerContainer.appendChild(peerBox);
        });
    } else {
        peerContainer.innerHTML = "<p>کاربری ندارید</p>";
    }
};

function copyToClipboard(text) {
    if (!navigator.clipboard) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand("copy");
        } catch (err) {
            console.error("کپی ناموفق:", err);
        }
        document.body.removeChild(textArea);
        return;
    }

    navigator.clipboard.writeText(text).catch(err => {
        console.error("کپی نشد:", err);
    });
}



const renderPagination = (currentPage, totalPages, config) => {
    const paginationContainer = document.getElementById("paginationContainer");
    paginationContainer.innerHTML = "";

    if (totalPages === 0) {
        return;
    }

    for (let i = 1; i <= totalPages; i++) {
        const pageButton = document.createElement("button");
        pageButton.textContent = i;
        pageButton.className = i === currentPage ? "active" : "";
        pageButton.addEventListener("click", () => {
            if (currentPage !== i) {
                fetchPeers(config, i, true);  
            }
        });
        paginationContainer.appendChild(pageButton);
    }
};


let selectedPeerForEdit = null;

function openEditPeerModal(peer) {
    selectedPeerForEdit = peer;

    const limitValue = parseFloat(peer.limit) || 0;
    const limitUnit = peer.limit.includes("GiB") ? "GB" : "MB";

    document.getElementById("editDataLimit").value = limitValue;
    document.getElementById("editDataLimitUnit").value = limitUnit;
    document.getElementById("editDns").value = peer.dns || "";
    document.getElementById("editExpiryDays").value = peer.expiry_time?.days || 0;
    document.getElementById("editExpiryMonths").value = peer.expiry_time?.months || 0;
    document.getElementById("editExpiryHours").value = peer.expiry_time?.hours || 0;
    document.getElementById("editExpiryMinutes").value = peer.expiry_time?.minutes || 0;
    document.getElementById("editPeerIp").value = peer.peer_ip;
    document.getElementById("editPeerModal").style.display = "flex";
}

document.getElementById("closeEditModal").addEventListener("click", () => {
    document.getElementById("editPeerModal").style.display = "none";
    selectedPeerForEdit = null;
});

document.getElementById("editPeerForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedPeerForEdit) {
        showAlert("هیچ کاربری برای ویرایش انتخاب نشده است");
        return;
    }

    const dataLimit = document.getElementById("editDataLimit").value.trim();
    const dataLimitUnit = document.getElementById("editDataLimitUnit").value;
    const formattedLimit = `${dataLimit}${dataLimitUnit === "GB" ? "GiB" : "MiB"}`;
    const dns = document.getElementById("editDns").value.trim();
    const expiryDays = parseInt(document.getElementById("editExpiryDays").value || 0);
    const expiryMonths = parseInt(document.getElementById("editExpiryMonths").value || 0);
    const expiryHours = parseInt(document.getElementById("editExpiryHours").value || 0);
    const expiryMinutes = parseInt(document.getElementById("editExpiryMinutes").value || 0);
    const configFile = configSelect.value;

    const payload = {
        peerName: selectedPeerForEdit.peer_name,
        configFile,
        dataLimit: dataLimit ? formattedLimit : null,
        dns,
        expiryDays,
        expiryMonths,
        expiryHours,
        expiryMinutes,
    };

    try {
        const response = await fetch("/api/edit-peer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (response.ok) {
            showAlert(data.message || "ویرایش کاربر با موفقیت انجام شد");
            document.getElementById("editPeerModal").style.display = "none";

            const index = peersData.findIndex(
                (p) => p.peer_name === selectedPeerForEdit.peer_name && p.peer_ip === selectedPeerForEdit.peer_ip
            );

            if (index !== -1) {
                peersData[index] = { ...peersData[index], ...data.updatedPeer };
            }

            renderPeers(peersData, configFile); 
            selectedPeerForEdit = null;
        } else {
            showAlert(data.error || "اپدیت کاربر موفقیت امیز نبود");
        }
    } catch (error) {
        console.error("Updating peer error:", error);
        showAlert("خطا. لطفا دوباره تلاش کنید");
    }
});



let isFiltering = false; 
let isSearching = false; 

document.getElementById("searchInput").addEventListener("input", async () => {
    const searchValue = document.getElementById("searchInput").value.trim().toLowerCase(); 
    const peerContainer = document.getElementById("peerContainer"); 

    if (searchValue === "") {
        isSearching = false;
        if (!isFiltering) {
            fetchPeers(configSelect.value); 
        }
        return;
    }

    isSearching = true; 

    try {
        const response = await fetch(`/api/search-peers?query=${encodeURIComponent(searchValue)}`); 
        const data = await response.json();

        if (!response.ok) {
            showAlert(data.error || "جستجوی کاربران امکان‌پذیر نیست.");
            return;
        }

        renderPeers(data.peers, configSelect.value); 
    } catch (error) {
        console.error("خطا در جستجوی کاربران:", error);
        showAlert("در هنگام جستجو خطایی رخ داد.");
    }
});

document.getElementById("filterSelect").addEventListener("change", () => {
    const filterValue = document.getElementById("filterSelect").value; 
    if (!filterValue) {
        isFiltering = false;
        fetchPeers(configSelect.value); 
        return;
    }

    isFiltering = true; 
    applyFilter(); 
});

function applyFilter() {
    const filterValue = document.getElementById("filterSelect").value; 
    const query = document.getElementById("searchInput").value.trim(); 

    const url = `/api/search-peers?query=${encodeURIComponent(query)}&filter=${encodeURIComponent(filterValue)}`; 

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("خطا در دریافت کاربران:", data.error);
                return;
            }

            renderPeers(data.peers); 
        })
        .catch(error => {
            console.error("خطا در اعمال فیلتر:", error);
        });
}

window.applyFilter = applyFilter;
async function toggleBlock(peerName, currentState) {
    try {
        const response = await fetch(`/api/toggle-block`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerName, blocked: currentState }),
        });
        const result = await response.json();
        if (result.success) {
            return true; 
        } else {
            showAlert(result.error || "update block status has failed");
            return false; 
        }
    } catch (error) {
        console.error("toggling block status error:", error);
        showAlert("Unable to toggle block.");
        return false; 
    }
}
window.downloadPeerConfig = (peerName, config) => {
    try {
        const url = `/api/export-peer?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(config)}`;
        console.log(`Downloading configuration from URL: ${url}`); 
        window.location.href = url;
    } catch (error) {
        console.error("triggering download error:", error);
    }
};

async function fetchStatuses() {
    try {
        const [stuffResponse, botResponse] = await Promise.all([
            fetch('/api/stuff'), 
            fetch('/bot-status') 
        ]);

        if (!stuffResponse.ok) {
            const errorText = await stuffResponse.text();
            console.error(`fetching WARP/Xray statuses failed: ${stuffResponse.status}`, errorText);
            return;
        }

        if (!botResponse.ok) {
            const errorText = await botResponse.text();
            console.error(`fetching bot status failed: ${botResponse.status}`, errorText);
            return;
        }

        const { warp, xray } = await stuffResponse.json();
        const { status: botStatus } = await botResponse.json();

        console.log("Received bot status from backend:", botStatus);

        const warpStatusElement = document.getElementById('warpStatus');
        warpStatusElement.textContent = warp ? 'فعال' : 'غیرفعال';
        warpStatusElement.style.color = warp ? 'green' : 'red';

        const xrayStatusElement = document.getElementById('xrayStatus');
        xrayStatusElement.textContent = xray ? 'فعال' : 'غیرفعال';
        xrayStatusElement.style.color = xray ? 'green' : 'red';

        const botStatusElement = document.getElementById('botStatus');
        if (botStatusElement) {
            botStatusElement.textContent =
                botStatus.toLowerCase() === "running" ? "فعال" :
                botStatus.toLowerCase() === "stopped" ? "غیرفعال" :
                "نصب نیست";
            botStatusElement.style.color = botStatus.toLowerCase() === "running" ? "green" : "red";
        } else {
            console.error("Bot status element not found in DOM.");
        }
    } catch (error) {
        console.error('fetching statuses error:', error);
    }
}
document.getElementById("createPeerBtn").addEventListener("click", () => {
    const selectedConfig = configSelect.value;
    if (selectedConfig) {
        fetchAvailableIps(selectedConfig);
        document.getElementById("createPeerModal").style.display = "flex";
    } else {
        showAlert("نخست یک کانفیگ انتخاب نمایید");
    }
});

document.getElementById("closeModal").addEventListener("click", () => {
document.getElementById("createPeerModal").style.display = "none";
});

configSelect.addEventListener("change", () => {
    const selectedConfig = configSelect.value;
    if (selectedConfig) {
        fetchPeers(selectedConfig); 
    }
});
let keyVisible = false; 
const loadWireGuardDetails = async (config) => {
    try {
        if (!config) {
            console.error("No Wireguard config provided.");
            showAlert("لطفا کانفیگ وایرگارد انتخاب نمایید");
            return;
        }

        const response = await fetch(`/api/wireguard-details?config=${config}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Wireguard details fetched:", data); 

        const wgInterface = document.getElementById("wg-interface");
        const wgStatus = document.getElementById("wg-status");
        const wgUptime = document.getElementById("wg-uptime");
        const wgIp = document.getElementById("wg-ip");
        const wgPort = document.getElementById("wg-port");
        const wgDns = document.getElementById("wg-dns");
        const toggleInterfaceBtn = document.getElementById("toggleInterfaceBtn");
        const privateKeySpan = document.getElementById("wg-private-key");
        const toggleKeyBtn = document.getElementById("toggleKeyBtn");

        if (!wgInterface || !wgStatus || !wgUptime || !wgIp || !wgPort || !wgDns || !toggleInterfaceBtn || !privateKeySpan || !toggleKeyBtn) {
            console.error("Critical DOM elements are missing.");
            showAlert("Critical DOM elements are missing. Check devtools.");
            return;
        }

        wgInterface.textContent = data.interface || "نامشخص";
        wgStatus.textContent = data.active ? "فعال" : "غیرفعال";
        wgStatus.className = `status ${data.active ? "active" : "inactive"}`;
        wgUptime.textContent = data.uptime || "0d 0h 0m";
        wgIp.textContent = data.ip || "نامشخص";
        wgPort.textContent = data.port || "نامشخص";
        wgDns.textContent = data.dns || "نامشخص";
        toggleInterfaceBtn.textContent = data.active ? "غیرفعال کنید" : "فعال کنید";
        toggleInterfaceBtn.dataset.active = data.active; 
        toggleInterfaceBtn.dataset.config = config; 

        toggleKeyBtn.textContent = "پنهان";
        toggleKeyBtn.textContent = "نمایش";

        toggleKeyBtn.onclick = async () => {
    if (!keyVisible) {
        try {
            const keyResponse = await fetch(`/api/wireguard-details?config=${config}`);
            const keyData = await keyResponse.json();
            if (keyData.private_key && keyData.private_key !== "N/A") {
                privateKeySpan.textContent = keyData.private_key;
                toggleKeyBtn.textContent = "پنهان کن";
                keyVisible = true; 
            } else {
                privateKeySpan.textContent = "خطا";
            }
        } catch (error) {
            console.error("خطا در دریافت کلید خصوصی:", error);
            privateKeySpan.textContent = "خطا";
        }
    } else { 
        privateKeySpan.textContent = "پنهان شده";
        toggleKeyBtn.textContent = "نمایش";
        keyVisible = false; 
    }
};

        console.log(`Wireguard interface and private key updated for: ${config}`);
    } catch (error) {
        console.error("loading WireGuard details error:", error);
        showAlert("امکان بارگذاری کانفیگ وایرگارد وجود ندارد");
    }
};

const toggleInterface = async () => {
    const config = configSelect.value; 
    if (!config) {
        showAlert("لطفا یک کانفیگ انتخاب نمایید");
        return;
    }
    const action = document.getElementById("wg-status").classList.contains("active") ? "down" : "up";
    try {
        const response = await fetch(`/api/toggle-config?config=${config}&active=${action === "up"}`, {
            method: "POST",
        });
        const data = await response.json();
        showAlert(data.message || "موفقیت امیر بود");
        await loadWireGuardDetails(config);
    } catch (error) {
        console.error("toggling interface error:", error);
        showAlert("toggle interface has failed.");
    }
};
const toggleKeyVisibility = async () => {
    if (privateKeySpan.textContent === "Hidden") {
        try {
            const response = await fetch(`/api/wireguard-details?config=${configSelect.value}`);
            const data = await response.json();
            if (data.private_key && data.private_key !== "N/A") {
                privateKeySpan.textContent = data.private_key;
                toggleKeyBtn.textContent = "Hide";
            } else {
                privateKeySpan.textContent = "Error";
            }
        } catch (error) {
            console.error("fetching private key error:", error);
            privateKeySpan.textContent = "Error";
        }
    } else {
        privateKeySpan.textContent = "پنهان";
        toggleKeyBtn.textContent = "نمایش";
    }
};
document.getElementById("configSelect").addEventListener("change", async () => {
    const selectedConfig = document.getElementById("configSelect").value;
    if (!selectedConfig) {
        showAlert("لطفا یک کانفیگ انتخاب نمایید");
        return;
    }

    console.log(`Switching to configuration: ${selectedConfig}`);

    showLoadingSpinner(); 
    currentPage = 1;

    try {
        await fetchPeers(selectedConfig, currentPage);  
        renderPagination(currentPage, totalPages, selectedConfig);
        await loadWireGuardDetails(selectedConfig);
    } catch (error) {
        console.error("Error loading configuration:", error);
        showAlert("خطایی در بارگذاری اینترفیس رخ داده است.");
    } finally {
        hideLoadingSpinner();
    }
});



const resetTraffic = async (peerName, config) => {
    if (!peerName) {
        alert("Peer name is required to reset traffic.");
        return;
    }

    try {
        const response = await fetch(`/api/reset-traffic`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerName }),
        });

        const data = await response.json();
        if (response.ok) {
            showAlert(data.message || "ریست ترافیک موفقیت امیز بود");
            fetchPeers(config); 
        } else {
            showAlert(data.error || "ریست ترافیک موفقیت امیر نبود");
        }
    } catch (error) {
        console.error("resetting traffic error:", error);
        showAlert("خطایی در ریست ترافیک رخ داده است");
    }
};
toggleInterfaceBtn.addEventListener("click", toggleInterface);
toggleKeyBtn.addEventListener("click", toggleKeyVisibility);
configSelect.addEventListener("change", () => loadWireGuardDetails(configSelect.value));
loadWireGuardDetails("wg0.conf"); 
fetchMetrics();
fetchStatuses(); 
fetchSpeedData();
fetchConfigs();
const defaultConfig = "wg0.conf"; 
fetchPeers(defaultConfig);
setInterval(fetchMetrics, 10000); 
setInterval(fetchSpeedData, 5000);
setInterval(fetchStatuses, 10000);
const refreshPeerList = (config) => {
    fetchPeers(config, currentPage, false); 
};

setInterval(() => {
    if (isPaginationChanging) {
        console.log("Skipping peer refresh due to active pagination.");
        return;
    }

    if (isSearching || isFiltering) {
        console.log("Skipping peer refresh due to active search or filter.");
        return;
    }

    console.log("Refreshing peer list...");
    refreshPeerList(configSelect.value);
}, 10000);
});