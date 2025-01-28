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
                    console.error("گزینه انتخاب کانفیگ پیدا نشد.");
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
                console.error("خطا در دریافت کانفیگ‌ها:", data.error);
                showAlert("دریافت کانفیگ‌ها ناموفق بود. لطفاً دوباره تلاش کنید.");
            }
        } catch (error) {
            console.error("خطا در دریافت کانفیگ‌ها:", error);
            showAlert("دریافت کانفیگ‌ها امکان‌پذیر نیست.");
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
            showAlert("کاربری یافت نشد");
        }
    } catch (error) {
        console.error("error in fetching peers:", error);
        showAlert("دریافت اطلاعات کاربران امکان پذیر نیست");
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
    peerName.textContent = peer.peer_name || "نام‌گذاری نشده"; 

    const toggleSwitch = document.createElement("div");
    toggleSwitch.className = `toggle-switch ${peer.active ? "active" : ""}`; 
    toggleSwitch.addEventListener("click", () => togglePeerState(peer.peer_name, !peer.active)); 

    header.append(peerName, toggleSwitch);

    const content = document.createElement("div");
    content.className = "content"; 
    content.innerHTML = `
    <p dir="rtl">آدرس IP: <span dir="ltr">${peer.peer_ip || "نامشخص"}</span></p>
    <p dir="rtl">مصرف شده: <span dir="ltr">${peer.used_human || "0 MiB"}</span> / <span dir="ltr">${peer.limit_human || "نامحدود"}</span></p>
    <p dir="rtl">حجم باقی‌مانده: <span dir="ltr">${peer.remaining_human || "ناموجود"}</span></p>
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
        <button onclick="editPeer('${peer.peer_name}')">ویرایش</button>
        <button onclick="resetTraffic('${peer.peer_name}')">ریست مصرف</button>
        <button onclick="deletePeer('${peer.peer_name}')">حذف</button>
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
            showAlert(data.message || "انقضا با موفقیت ریست شد!");
            fetchPeers(config); 
        } else {
            showAlert(data.error || "ریست انقضا ناموفق بود.");
        }
    } catch (error) {
        console.error("خطا در ریست انقضا:", error);
        showAlert("خطایی رخ داده است. لطفاً دوباره تلاش کنید.");
    }
};

const renderPeers = (peers, config) => {
    const peerContainer = document.getElementById("peerContainer");

    if (!peerContainer) {
        console.error("محل نمایش کاربران یافت نشد.");
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
            peerName.textContent = peer.peer_name || "نام‌گذاری نشده";

            const toggleIcon = document.createElement("div");
            const isBlocked = peer.monitor_blocked || peer.expiry_blocked;
            toggleIcon.className = `toggle-icon ${isBlocked ? "inactive" : "active"}`;
            toggleIcon.title = isBlocked ? "فعال کردن کاربر" : "غیرفعال کردن کاربر";

            toggleIcon.addEventListener("click", async () => {
                await togglePeerState(peer.peer_name, isBlocked, config);
                toggleIcon.className = `toggle-icon ${!isBlocked ? "inactive" : "active"}`;
                toggleIcon.title = !isBlocked ? "فعال کردن کاربر" : "غیرفعال کردن کاربر";
            });

            const status = document.createElement("div");
            status.className = `status ${isBlocked ? "inactive" : "active"}`;
            status.textContent = isBlocked ? "غیرفعال" : "فعال";

            header.append(peerName, status, toggleIcon);

            const content = document.createElement("div");
            content.className = "content";

            let expiryText = "تنظیم نشده";

if (peer.remaining_time !== undefined) {
    let timer;

    const updateRemainingTime = () => {
        if (peer.remaining_time > 0) {
            const days = Math.floor(peer.remaining_time / (24 * 60));
            const hours = Math.floor((peer.remaining_time % (24 * 60)) / 60);
            const minutes = peer.remaining_time % 60;
            expiryText = `${days} روز، ${hours} ساعت، ${minutes} دقیقه`;
        } else {
            expiryText = "منقضی شده";
            clearInterval(timer); 
        }
    };

    updateRemainingTime(); 
    timer = setInterval(() => {
        peer.remaining_time -= 1; 
        updateRemainingTime(); 
    }, 60000); 
} else {
    expiryText = "تنظیم نشده";
}


            content.innerHTML = `
                <p dir="rtl">آدرس ایپی: <span dir="ltr">${peer.peer_ip || "نامشخص"}</span></p>
                <p dir="rtl">مصرف شده: <span dir="ltr">${peer.used_human || "0 MiB"}</span> / <span dir="ltr">${peer.limit_human || "نامحدود"}</span></p>
                <p dir="rtl">حجم باقی‌مانده: <span dir="ltr">${peer.remaining_human || "ناموجود"}</span></p>
                <p>انقضا: ${expiryText}</p>
            `;

            const footer = document.createElement("div");
            footer.className = "footer";

            const actions = document.createElement("div");
            actions.className = "actions";

            const editBtn = createActionButton("fas fa-edit", "ویرایش کاربر", () => openEditPeerModal(peer));
            const deleteBtn = createActionButton("fas fa-trash-alt", "حذف کاربر", () => {
            deletePeer(peer.peer_name, config)
                .then(() => {
            
                })
                .catch((error) => {
                 console.error("error in deleting peer:", error);
            });
        });

            const resetBtn = createActionButton("fas fa-sync-alt", "ریست مصرف", () => resetTraffic(peer.peer_name, config));
            const resetExpiryBtn = createActionButton("fas fa-clock", "ریست انقضا", () => resetExpiry(peer.peer_name, config));
            const qrBtn = createActionButton("fas fa-qrcode", "نمایش کد QR", () => showQrCode(peer.peer_name, config));
            const downloadBtn = createActionButton("fas fa-download", "دانلود کانفیگ", () => downloadPeerConfig(peer.peer_name, config));

            actions.append(editBtn, deleteBtn, resetBtn, resetExpiryBtn, qrBtn, downloadBtn);

            const templateContainer = document.createElement("div");
            templateContainer.className = "template-box";

            const templateButton = document.createElement("button");
            templateButton.className = "btn";
            templateButton.textContent = "نمایش قالب";

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
                            throw new Error(`خطا در دریافت کد QR: ${response.statusText}`);
                        }
                        const data = await response.json();
                        const qrCodeDataUrl = data.qr_code;

                        const qrImage = new Image();
                        qrImage.src = qrCodeDataUrl;
                        qrImage.onload = () => {
                            ctx.drawImage(qrImage, 30, 370, 100, 100);
                            ctx.fillStyle = "white";
                            ctx.font = "14px 'Vazir', 'Tahoma', sans-serif"; 
                            ctx.textAlign = "right"; 
                            ctx.direction = "rtl";

                            const textStartX = 400;  
                            const textStartY = 385; 
                            const lineHeight = 25;   

                            ctx.fillText(`نام کاربر: ${peer.peer_name || "ناموجود"}`, textStartX, textStartY);
                            ctx.fillText(`IP کاربر: ${peer.peer_ip || "ناموجود"}`, textStartX, textStartY + lineHeight);
                            ctx.fillText(`حجم مجاز: ${peer.limit_human || "مشخص نشده"}`, textStartX, textStartY + lineHeight * 2);
                            ctx.fillText(`انقضا: ${expiryText}`, textStartX, textStartY + lineHeight * 3);
                        };
                        qrImage.onerror = () => {
                            console.error("خطا در بارگذاری تصویر QR.");
                        };
                    } catch (error) {
                        console.error("خطا در دریافت کد QR:", error);
                        ctx.fillStyle = "red";
                        ctx.font = "16px 'Vazir', 'Tahoma', sans-serif"; 
                        ctx.fillText("خطا در بارگذاری کد QR.", 30, 420);
                    }
                };

                modalContent.innerHTML = "";
                modalContent.appendChild(closeButton);
                modalContent.appendChild(canvas);

                const saveButton = document.createElement("button");
                saveButton.textContent = "ذخیره به فرمت JPG";
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
                    link.download = `${peer.peer_name || "کاربر"}-قالب.jpg`;
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
    } else {
        peerContainer.innerHTML = "<p>هیچ کاربری یافت نشد.</p>";
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
const showLoadingSpinner = () => {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.style.display = "flex";  
};

const hideLoadingSpinner = () => {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.style.display = "none";  
};

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
        console.error("Error while fetching peers:", error);
        showAlert("دریافت اطلاعات کاربران امکان پذیر نیست");
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
        showAlert("هیچ کاربری انتخاب نشده است");
        return;
    }

    const configFile = configSelect.value; 

    const payload = {
        peerName: selectedPeerForEdit.peer_name,
        configFile, 
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
            showAlert(data.message || "اپدیت کاربر موفقیت آمیز بود");
            document.getElementById("editPeerModal").style.display = "none";
            fetchPeers(configFile); 
        } else {
            showAlert(data.error || "اپدیت کاربر موفقیت آمیز نبود");
        }
    } catch (error) {
        console.error("خطای اپدیت کاربر:", error);
        showAlert("یک خطا رخ داد. لطفاً دوباره تلاش کنید.");
    }
});


    const togglePeerState = async (peerName, currentState, config) => {
    try {
        const peerBox = document.querySelector(`[data-peer-name="${peerName}"] .toggle-icon`);
        if (peerBox) {
            peerBox.className = `toggle-icon ${!currentState ? "active" : "inactive"}`;
            peerBox.title = !currentState ? "غیرفعال کردن کاربر" : "فعال کردن کاربر";
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

            showAlert(data.message || "وضعیت کاربر با موفقیت به‌روزرسانی شد!");
        } else {
            console.error(data.error || "تغییر وضعیت کاربر ناموفق بود.");

            if (peerBox) {
                peerBox.className = `toggle-icon ${currentState ? "active" : "inactive"}`;
                peerBox.title = currentState ? "غیرفعال کردن کاربر" : "فعال کردن کاربر";
            }
            showAlert(data.error || "تغییر وضعیت کاربر ناموفق بود.");
        }
    } catch (error) {
        console.error("خطا در تغییر وضعیت کاربر:", error);

        const peerBox = document.querySelector(`[data-peer-name="${peerName}"] .toggle-icon`);
        if (peerBox) {
            peerBox.className = `toggle-icon ${currentState ? "active" : "inactive"}`;
            peerBox.title = currentState ? "غیرفعال کردن کاربر" : "فعال کردن کاربر";
        }

        showAlert("خطایی در تغییر وضعیت کاربر رخ داد.");
    }
};


    const deletePeer = async (peerName, config) => {
    return new Promise((resolve, reject) => {
        showConfirm(`آیا از حذف کاربر ${peerName} مطمئن هستید؟`, async (confirmed) => {
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
                        showAlert(data.message || "کاربر با موفقیت حذف شد.");
                        
                        peersData = peersData.filter(peer => peer.peer_name !== peerName);

                        if (peersData.length === 0 && currentPage > 1) {
                            currentPage -= 1;
                        }

                        fetchPeers(config, "", "", currentPage);  
                        resolve();  
                    } else {
                        showAlert(data.error || "حذف کاربر با خطا مواجه شد.");
                        reject();  
                    }
                } catch (error) {
                    console.error("خطا در حذف کاربر:", error);
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
        showAlert("نام کاربر برای تنظیم مجدد ترافیک الزامی است.");
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
            showAlert(data.message || "ترافیک با موفقیت تنظیم مجدد شد!");
            fetchPeers(config); 
        } else {
            console.error("خطا در تنظیم مجدد ترافیک:", data.error);
            showAlert(data.error || "تنظیم مجدد ترافیک با شکست مواجه شد.");
        }
    } catch (error) {
        console.error("خطا در تنظیم مجدد ترافیک:", error);
        showAlert("خطا در تنظیم مجدد ترافیک.");
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
