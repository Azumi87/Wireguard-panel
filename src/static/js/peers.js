document.addEventListener("DOMContentLoaded", () => {
    let peersData = [];
    let currentConfig = "wg0.conf"; 
    let selectedPeerForEdit = null; 
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

    if (typeof callback !== "function") {
        console.error("Callback is not a function", callback);
        return; 
    }

    confirmYes.onclick = () => {
        confirmModal.style.display = "none";
        callback(true);  
    };

    confirmNo.onclick = () => {
        confirmModal.style.display = "none";
        callback(false); 
    };
}

    const limit = 10; 

    const fetchConfigs = async () => {
        try {
            const response = await fetch("/api/configs");
            const data = await response.json();

            if (response.ok) {
                const configSelect = document.getElementById("configSelect");
                if (!configSelect) {
                    console.error("Configuration selector not found.");
                    return;
                }

                configSelect.innerHTML = ""; 
                data.configs.forEach((config) => {
                    const option = document.createElement("option");
                    option.value = config;
                    option.textContent = config;
                    if (config === currentConfig) {
                        option.selected = true;
                    }
                    configSelect.appendChild(option);
                });

                currentConfig = data.configs[0] || "wg0.conf"; 
                fetchPeers(currentConfig); 
            } else {
                console.error("error in fetching configs:", data.error);
                showAlert("fetching configs failed. try again.");
            }
        } catch (error) {
            console.error("error @ fetching configs:", error);
            showAlert("unable to fetch configurations.");
        }
    };
    let currentPage = 1; 
    let search = ""; 
    let filter = ""; 
    let isPaginationChanging = false;

    const fetchPeers = async (config, search = "", filter = "", page = currentPage, isPagination = false) => {
    try {
        if (isPagination) {
            showLoadingSpinner(); 
            isPaginationChanging = true;  
        }

        const response = await fetch(
            `/api/peers?config=${config}&search=${encodeURIComponent(search)}&filter=${encodeURIComponent(filter)}&page=${page}&limit=${limit}`
        );
        const data = await response.json();

        if (response.ok) {
            peersData = data.peers || [];
            totalPages = data.total_pages || 0;

            if (page > totalPages) {
                page = 1; 
            }

            if (page <= totalPages && page !== currentPage) {
                currentPage = page; 
            }

            renderPeers(peersData, config);
            renderPagination(currentPage, totalPages, config, search, filter);
        } else {
            console.error(data.error || "Couldn't fetch peers.");
            showAlert("No peers found.");
        }
    } catch (error) {
        console.error("error in fetching peers:", error);
        showAlert("Unable to fetch peers. Check your connection.");
    } finally {
        if (isPagination) {
            hideLoadingSpinner(); 
            isPaginationChanging = false;  
        }
    }
};


const renderPeerBox = (peer) => {
        const peerBox = document.createElement("div");
        peerBox.className = "peer-box";

        const header = document.createElement("div");
        header.className = "header";

        const peerName = document.createElement("span");
        peerName.className = "peer-name";
        peerName.textContent = peer.peer_name || "Unnamed Peer";

        const toggleSwitch = document.createElement("div");
        toggleSwitch.className = `toggle-switch ${peer.active ? "active" : ""}`;
        toggleSwitch.addEventListener("click", () => togglePeerState(peer.peer_name, !peer.active));

        header.append(peerName, toggleSwitch);

        const content = document.createElement("div");
        content.className = "content";
        content.innerHTML = `
            <p>IP: ${peer.peer_ip || "N/A"}</p>
            <p>Used: ${peer.used_human || "0 MiB"} / ${peer.limit_human || "N/A"}</p>
            <p>Remaining Data: ${peer.remaining_human || "N/A"}</p>
        `;

        const footer = document.createElement("div");
        footer.className = "footer";

        const menuButton = document.createElement("button");
        menuButton.className = "menu-button";
        menuButton.textContent = "⋮";
        menuButton.addEventListener("click", () => {
            menuDropdown.classList.toggle("active");
        });

        const menuDropdown = document.createElement("div");
        menuDropdown.className = "menu-dropdown";
        menuDropdown.innerHTML = `
            <button onclick="editPeer('${peer.peer_name}')">Edit</button>
            <button onclick="resetTraffic('${peer.peer_name}')">Reset Traffic</button>
            <button onclick="deletePeer('${peer.peer_name}')">Delete</button>
        `;
        menuButton.appendChild(menuDropdown);

        footer.appendChild(menuButton);
        peerBox.append(header, content, footer);

        return peerBox;
    };
const resetExpiry = async (peerName, config) => {
    try {
        const response = await fetch("/api/reset-expiry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerName, config }),
        });
        const data = await response.json();
        if (response.ok) {
            showAlert(data.message || "Expiry reset successfully!");
            fetchPeers(config); 
        } else {
            showAlert(data.error || "reset expiry failed.");
        }
    } catch (error) {
        console.error("resetting expiry error:", error);
        showAlert("error occurred. Plz try again.");
    }
};
const renderPeers = (peers, config) => {
    const peerContainer = document.getElementById("peerContainer");

    if (!peerContainer) {
        console.error("Peer container not found.");
        return;
    }

    peerContainer.innerHTML = ""; 

    if (peers && peers.length > 0) {
        peers.forEach((peer) => {
            const peerBox = document.createElement("div");
            peerBox.className = "peer-box";

            const header = document.createElement("div");
            header.className = "header";

            const peerName = document.createElement("strong");
            peerName.textContent = peer.peer_name || "Unnamed Peer";

            const toggleIcon = document.createElement("div");
            const isBlocked = peer.monitor_blocked || peer.expiry_blocked;
            toggleIcon.className = `toggle-icon ${isBlocked ? "inactive" : "active"}`;
            toggleIcon.title = isBlocked ? "Enable Peer" : "Disable Peer";

            toggleIcon.addEventListener("click", async () => {
                await togglePeerState(peer.peer_name, isBlocked, config);

                toggleIcon.className = `toggle-icon ${!isBlocked ? "inactive" : "active"}`;
                toggleIcon.title = !isBlocked ? "Enable Peer" : "Disable Peer";
            });

            const status = document.createElement("div");
            status.className = `status ${isBlocked ? "inactive" : "active"}`;
            status.textContent = isBlocked ? "Inactive" : "Active";

            header.append(peerName, status, toggleIcon);

            const content = document.createElement("div");
            content.className = "content";

            let expiryText = "Not Set";

if (peer.remaining_time !== undefined) {
    let timer;

    const updateRemainingTime = () => {
        if (peer.remaining_time > 0) {
            const days = Math.floor(peer.remaining_time / (24 * 60));
            const hours = Math.floor((peer.remaining_time % (24 * 60)) / 60);
            const minutes = peer.remaining_time % 60;
            expiryText = `${days} days, ${hours} hours, ${minutes} mins`;
        } else {
            expiryText = "Expired";
            clearInterval(timer); 
        }
    };

    updateRemainingTime(); 
    timer = setInterval(() => {
        peer.remaining_time -= 1; 
        updateRemainingTime(); 
    }, 60000); 
} else {
    expiryText = "Not Set"; 
}



            content.innerHTML = `
                <p>IP: ${peer.peer_ip || "N/A"}</p>
                <p>Used: ${peer.used_human || "0 MiB"} / ${peer.limit_human || "N/A"}</p>
                <p>Remaining Data: ${peer.remaining_human || "N/A"}</p>
                <p>Expiry: ${expiryText}</p>
            `;

            const footer = document.createElement("div");
            footer.className = "footer";

            const actions = document.createElement("div");
            actions.className = "actions";

            const editBtn = createActionButton("fas fa-edit", "Edit Peer", () => openEditPeerModal(peer));
            const deleteBtn = createActionButton("fas fa-trash-alt", "Delete Peer", () => {
            deletePeer(peer.peer_name, config)
                .then(() => {
            
                })
                .catch((error) => {
                 console.error("error in deleting peer:", error);
            });
        });
            const resetBtn = createActionButton("fas fa-sync-alt", "Reset Traffic", () => resetTraffic(peer.peer_name, config));
            const resetExpiryBtn = createActionButton("fas fa-clock", "Reset Expiry", () => resetExpiry(peer.peer_name, config));
            const qrBtn = createActionButton("fas fa-qrcode", "Show QR Code", () => showQrCode(peer.peer_name, config));
            const downloadBtn = createActionButton("fas fa-download", "Download Config", () => downloadPeerConfig(peer.peer_name, config));

            actions.append(editBtn, deleteBtn, resetBtn, resetExpiryBtn, qrBtn, downloadBtn);

            const templateContainer = document.createElement("div");
            templateContainer.className = "template-box"; 

            const templateButton = document.createElement("button");
            templateButton.className = "btn";
            templateButton.textContent = "Show Template";

            templateButton.addEventListener("click", async () => {
                const modal = document.createElement("div");
                modal.className = "modal";

                const modalContent = document.createElement("div");
                modalContent.className = "modal-content";

                const closeButton = document.createElement("span");
                closeButton.className = "close-modal";
                closeButton.textContent = "×";
                closeButton.addEventListener("click", () => {
                    modal.style.display = "none";
                    document.body.removeChild(modal);
                });

                const canvas = document.createElement("canvas");
                const ctx = canvas.getContext("2d");
                canvas.width = 430; 
                canvas.height = 500;

                const bgImage = new Image();
                bgImage.src = "/static/images/template.jpg"; 
                bgImage.onload = async () => {
                    ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);

                    ctx.fillStyle = "rgba(105, 105, 105, 0.9)"; 
                    ctx.fillRect(20, 360, 400, 120);

                    try {
                        const response = await fetch(`/api/qr-code?peerName=${encodeURIComponent(peer.peer_name)}&config=${encodeURIComponent(config)}`);
                        if (!response.ok) {
                            throw new Error(`error in fetching QR code: ${response.statusText}`);
                        }
                        const data = await response.json();
                        const qrCodeDataUrl = data.qr_code;

                        const qrImage = new Image();
                        qrImage.src = qrCodeDataUrl;
                        qrImage.onload = () => {
                            ctx.drawImage(qrImage, 30, 370, 100, 100);
                            ctx.fillStyle = "white";
                            ctx.font = "14px 'Poppins', Arial, sans-serif"; 
                            ctx.textAlign = "left";
                            const textStartX = 140;
                            const textStartY = 385; 
                            const lineHeight = 20;

                            ctx.fillText(`Peer Name: ${peer.peer_name || "N/A"}`, textStartX, textStartY);
                            ctx.fillText(`Peer IP: ${peer.peer_ip || "N/A"}`, textStartX, textStartY + lineHeight);
                            ctx.fillText(`Data Limit: ${peer.limit_human || "N/A"}`, textStartX, textStartY + lineHeight * 2);
                            ctx.fillText(`Expiry: ${expiryText}`, textStartX, textStartY + lineHeight * 3);
                        };
                        qrImage.onerror = () => {
                            console.error("Couldn't load QR code image.");
                        };
                    } catch (error) {
                        console.error("error in fetching QR code:", error);
                        ctx.fillStyle = "red";
                        ctx.font = "16px 'Poppins', Arial, sans-serif"; 
                        ctx.fillText("Couldn't load QR Code.", 30, 420);
                    }
                };

                modalContent.innerHTML = "";
                modalContent.appendChild(closeButton);
                modalContent.appendChild(canvas);

                const saveButton = document.createElement("button");
                saveButton.textContent = "Save as JPG";
                saveButton.className = "btn btn-primary";
                saveButton.style.marginTop = "10px";

                saveButton.addEventListener("click", () => {
                    const highResCanvas = document.createElement("canvas");
                    const scaleFactor = 2; 
                    highResCanvas.width = canvas.width * scaleFactor;
                    highResCanvas.height = canvas.height * scaleFactor;

                    const highResCtx = highResCanvas.getContext("2d");
                    highResCtx.scale(scaleFactor, scaleFactor); 

                    highResCtx.drawImage(canvas, 0, 0, canvas.width, canvas.height);

                    const imageData = highResCtx.getImageData(0, 0, highResCanvas.width, highResCanvas.height);
                    const sharpenedData = applySharpenFilter(imageData);
                    highResCtx.putImageData(sharpenedData, 0, 0);

                    const link = document.createElement("a");
                    link.href = highResCanvas.toDataURL("image/jpeg", 1.0); 
                    link.download = `${peer.peer_name || "peer"}-template-high-quality-sharpened.jpg`;
                    link.click();
                });

                modalContent.appendChild(saveButton);
                modal.appendChild(modalContent);
                document.body.appendChild(modal);
                modal.style.display = "flex";
            });

            templateContainer.appendChild(templateButton);

            footer.appendChild(actions);
            footer.appendChild(templateContainer);

            peerBox.append(header, content, footer);
            peerContainer.appendChild(peerBox);
        });
    }
};


function applySharpenFilter(imageData) {
    const weights = [0, -1, 0, -1, 5, -1, 0, -1, 0]; 
    const side = Math.round(Math.sqrt(weights.length));
    const halfSide = Math.floor(side / 2);

    const src = imageData.data;
    const sw = imageData.width;
    const sh = imageData.height;
    const output = new Uint8ClampedArray(src.length);

    for (let y = 0; y < sh; y++) {
        for (let x = 0; x < sw; x++) {
            const dstOff = (y * sw + x) * 4;
            let r = 0, g = 0, b = 0;

            for (let cy = 0; cy < side; cy++) {
                for (let cx = 0; cx < side; cx++) {
                    const scy = y + cy - halfSide;
                    const scx = x + cx - halfSide;
                    if (scy >= 0 && scy < sh && scx >= 0 && scx < sw) {
                        const srcOff = (scy * sw + scx) * 4;
                        const wt = weights[cy * side + cx];

                        r += src[srcOff] * wt;
                        g += src[srcOff + 1] * wt;
                        b += src[srcOff + 2] * wt;
                    }
                }
            }

            output[dstOff] = Math.min(Math.max(r, 0), 255);
            output[dstOff + 1] = Math.min(Math.max(g, 0), 255);
            output[dstOff + 2] = Math.min(Math.max(b, 0), 255);
            output[dstOff + 3] = src[dstOff + 3]; 
        }
    }

    imageData.data.set(output);
    return imageData;
}


const renderPagination = (currentPage, totalPages, config, search = "", filter = "") => {
    const paginationContainer = document.getElementById("paginationContainer");
    if (!paginationContainer) {
        console.error("Pagination container not found.");
        return;
    }

    paginationContainer.innerHTML = ""; 

    if (totalPages === 0) {
        return;
    }

    const validPage = currentPage > totalPages ? totalPages : currentPage; 

    for (let i = 1; i <= totalPages; i++) {
        const pageButton = document.createElement("button");
        pageButton.textContent = i;
        pageButton.className = i === validPage ? "active" : "";
        pageButton.addEventListener("click", () => {
            if (currentPage !== i) {
                fetchPeers(config, search, filter, i, true); 
            }
        });
        paginationContainer.appendChild(pageButton);
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
            showAlert(data.error || "Couldn't search peers.");
            return;
        }

        renderPeers(data.peers, configSelect.value);
    } catch (error) {
        console.error("searching peers error:", error);
        showAlert("error occurred while searching.");
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
                console.error("Error fetching peers:", data.error);
                return;
            }

            renderPeers(data.peers); 
        })
        .catch(error => {
            console.error("error in applyFilter:", error);
        });
}

window.applyFilter = applyFilter;

    document.getElementById("configSelect").addEventListener("change", async (event) => {
    currentConfig = event.target.value;

    const response = await fetch(`/api/peers?config=${currentConfig}&page=1&limit=${limit}`);
    const data = await response.json();

    if (data.total_pages < currentPage) {
        currentPage = 1;
    }

    showLoadingSpinner();

    try {
        const fetchResponse = await fetch(`/api/peers?config=${currentConfig}&page=${currentPage}&limit=${limit}`);
        const fetchData = await fetchResponse.json();

        if (fetchResponse.ok) {
            peersData = fetchData.peers || [];
            totalPages = fetchData.total_pages || 0;

            renderPeers(peersData, currentConfig);
            renderPagination(currentPage, totalPages, currentConfig);
        } else {
            showAlert(fetchData.error || "Couldn't fetch peers.");
        }
    } catch (error) {
        console.error("error in while fetching peers:", error);
        showAlert("Couldn't fetch peers. Check your connection.");
    } finally {
        hideLoadingSpinner();
    }
});


    const createActionButton = (iconClass, title, onClick) => {
        const btn = document.createElement("button");
        btn.title = title;
        btn.innerHTML = `<i class="${iconClass}"></i>`;
        btn.addEventListener("click", onClick);
        return btn;
    };

    const openEditPeerModal = (peer) => {
        selectedPeerForEdit = peer;

        document.getElementById("editDataLimit").value = parseFloat(peer.limit) || 0;
        document.getElementById("editDataLimitUnit").value = peer.limit.includes("GiB") ? "GB" : "MB";
        document.getElementById("editDns").value = peer.dns || "";
        document.getElementById("editExpiryDays").value = peer.expiry_time?.days || 0;
        document.getElementById("editExpiryMonths").value = peer.expiry_time?.months || 0;
        document.getElementById("editExpiryHours").value = peer.expiry_time?.hours || 0;
        document.getElementById("editExpiryMinutes").value = peer.expiry_time?.minutes || 0;
        document.getElementById("editPeerIp").value = peer.peer_ip;

        document.getElementById("editPeerModal").style.display = "flex";
    };

    document.getElementById("closeEditModal").addEventListener("click", () => {
        document.getElementById("editPeerModal").style.display = "none";
        selectedPeerForEdit = null;
    });

    document.getElementById("editPeerForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedPeerForEdit) {
        showAlert("No peer selected for editing.");
        return;
    }

    const payload = {
        peerName: selectedPeerForEdit.peer_name,
        configFile: configSelect.value, 
        dataLimit: `${document.getElementById("editDataLimit").value.trim()}${
            document.getElementById("editDataLimitUnit").value === "GB" ? "GiB" : "MiB"
        }`,
        dns: document.getElementById("editDns").value.trim(),
        expiryDays: parseInt(document.getElementById("editExpiryDays").value || 0),
        expiryMonths: parseInt(document.getElementById("editExpiryMonths").value || 0),
        expiryHours: parseInt(document.getElementById("editExpiryHours").value || 0),
        expiryMinutes: parseInt(document.getElementById("editExpiryMinutes").value || 0),
    };

    try {
        const response = await fetch("/api/edit-peer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (response.ok) {
            showAlert(data.message || "Peer updated successfully!");
            document.getElementById("editPeerModal").style.display = "none";
            fetchPeers(configSelect.value); 
            selectedPeerForEdit = null;
        } else {
            showAlert(data.error || "Updating peer failed.");
        }
    } catch (error) {
        console.error("Updating peer error:", error);
        showAlert("An error occurred. Please try again.");
    }
});

    const togglePeerState = async (peerName, currentState, config) => {
    try {
        const peerBox = document.querySelector(`[data-peer-name="${peerName}"] .toggle-icon`);
        if (peerBox) {
            peerBox.className = `toggle-icon ${!currentState ? "active" : "inactive"}`;
            peerBox.title = !currentState ? "Disable Peer" : "Enable Peer";
        }

        const response = await fetch(`/api/toggle-peer`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerName, blocked: !currentState, config }),
        });

        const data = await response.json();

        if (response.ok) {
            if (isFiltering || isSearching) {
                applyFilter(); 
            } else {
                await fetchPeers(config); 
            }

            showAlert(data.message || "Peer state updated successfully!");
        } else {
            console.error(data.error || "Toggle peer state failed.");

            if (peerBox) {
                peerBox.className = `toggle-icon ${currentState ? "active" : "inactive"}`;
                peerBox.title = currentState ? "Disable Peer" : "Enable Peer";
            }
            showAlert(data.error || "Toggle peer state failed.");
        }
    } catch (error) {
        console.error("error in toggling peer state:", error);

        const peerBox = document.querySelector(`[data-peer-name="${peerName}"] .toggle-icon`);
        if (peerBox) {
            peerBox.className = `toggle-icon ${currentState ? "active" : "inactive"}`;
            peerBox.title = currentState ? "Disable Peer" : "Enable Peer";
        }

        showAlert("Error in toggling peer state.");
    }
};


    const deletePeer = async (peerName, config) => {
    return new Promise((resolve, reject) => {
        showConfirm(`Are you sure you want to delete peer ${peerName}?`, async (confirmed) => {
            if (confirmed) {
                try {
                    const configFile = config || "wg0.conf";

                    const response = await fetch(`/api/delete-peer`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ peerName, configFile }),
                    });

                    const data = await response.json();
                    if (response.ok) {
                        showAlert(data.message || "Peer deleted successfully.");
                        fetchPeers(config);  
                        resolve();  
                    } else {
                        showAlert(data.error || "Deleting peer failed.");
                        reject();  
                    }
                } catch (error) {
                    console.error("error in deleting peer:", error);
                    reject(error);  
                }
            } else {
                resolve(); 
            }
        });
    });
};

    
const resetTraffic = async (peerName, config) => {
    if (!peerName) {
        showAlert("Peer name is required to reset traffic.");
        return;
    }

    try {
        const response = await fetch(`/api/reset-traffic`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerName, config }), 
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(data.message || "Traffic reset successfully!");
            fetchPeers(config); 
        } else {
            console.error("error in resetting traffic:", data.error);
            showAlert(data.error || "reseting traffic failed.");
        }
    } catch (error) {
        console.error("error in resetting traffic:", error);
        showAlert("error occurred resetting traffic.");
    }
};

    const showQrCode = async (peerName, config) => {
        const qrCodeModal = document.getElementById("qrCodeModal");
        const qrCodeCanvas = document.getElementById("qrCodeCanvas");
        const saveQrCode = document.getElementById("saveQrCode");

        if (!qrCodeModal || !qrCodeCanvas || !saveQrCode) {
            console.error("QR Code modal elements not found.");
            return;
        }

        qrCodeModal.style.display = "flex"; 

        try {
            const response = await fetch(`/api/export-peer?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(config)}`);
            const peerConfig = await response.text();

            QRCode.toCanvas(qrCodeCanvas, peerConfig, { width: 300 }, (error) => {
                if (error) console.error("error in generating QR code:", error);
            });

            saveQrCode.onclick = () => {
                const link = document.createElement("a");
                link.href = qrCodeCanvas.toDataURL("image/png");
                link.download = `${peerName}-qr-code.png`;
                link.click();
            };
        } catch (error) {
            console.error("fetching peer config for QR code caused an error:", error);
        }
    };

    document.getElementById("closeQrModal").addEventListener("click", () => {
        const qrCodeModal = document.getElementById("qrCodeModal");
        if (qrCodeModal) qrCodeModal.style.display = "none";
    });

    const downloadPeerConfig = (peerName, config) => {
        const url = `/api/export-peer?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(config)}`;
        window.location.href = url; 
    };

    const showErrorMessage = (message) => {
        const peerContainer = document.getElementById("peerContainer");
        if (peerContainer) {
            peerContainer.innerHTML = `<p>${message}</p>`;
        }
    };

    const defaultConfig = "wg0.conf";
    fetchPeers(defaultConfig);
    setInterval(() => {
    if (isSearching || isFiltering) {
        console.log("Skipping peer refresh due to active search or filter.");
        return; 
    }

    if (isPaginationChanging) {
        console.log("Skipping refresh due to active pagination.");
        return; 
    }

    console.log("Refreshing peer list...");
    fetchPeers(configSelect.value, search, filter, currentPage); 
}, 10000);

    fetchConfigs();
});
