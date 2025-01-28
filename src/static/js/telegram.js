document.addEventListener("DOMContentLoaded", () => {
    const apiKeyContainer = document.getElementById("api-key-container");
    const apiKeyBox = document.getElementById("api-key-box");
    const apiKeyList = document.getElementById("api-key-list");
    const createApiButton = document.getElementById("create-api-btn");
    const deleteApiButton = document.getElementById("delete-api-btn");
    const telegramForm = document.getElementById("telegram-config-form");
    const enableTelegramCheckbox = document.getElementById("enable-telegram");
    const telegramSection = document.querySelector(".telegram-section");
    const uninstallButton = document.getElementById("uninstall-btn");
    const installButton = document.getElementById("install-btn");
    const startButton = document.getElementById("start-btn");
    const stopButton = document.getElementById("stop-btn");
    const statusText = document.getElementById("bot-status");

    const botTokenInput = document.getElementById("bot-token");
    const baseUrlInput = document.getElementById("base-url");
    const apiKeyInput = document.getElementById("api-key");
    const adminChatIdInput = document.getElementById("admin-chat-ids");


    function fetchBotStatus() {
        fetch("/bot-status")
            .then(response => response.json())
            .then(data => {
                updateUI(data.status);
            })
            .catch(error => console.error("fetching bot status error:", error));
    }
    uninstallButton.addEventListener("click", () => {
    fetch("/uninstall-telegram", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "uninstalled") {
                showAlert("Telegram bot uninstalled successfully.");
                fetchBotStatus(); 
            } else {
                showAlert("Couldn't uninstall Telegram bot.");
            }
        })
        .catch(error => console.error("error in uninstalling bot:", error));
});


    function fetchAdminChatIds() {
    fetch("/get-admin-chat-ids")  
        .then(response => {
            if (!response.ok) throw new Error(`Error in: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const adminChatIdInput = document.getElementById("admin-chat-ids");
            if (data.admin_chat_ids) {
                adminChatIdInput.value = data.admin_chat_ids.join(", "); 
            } else {
                adminChatIdInput.value = ""; 
            }
        })
        .catch(error => console.error("Error in fetching admin chat IDs:", error));
}



    enableTelegramCheckbox.addEventListener("change", (event) => {
    if (event.target.checked) {
        telegramSection.style.display = "block";
        installButton.classList.remove("hidden");
    } else {
        telegramSection.style.display = "none";
        installButton.classList.add("hidden");
    }
});

function updateUI(status) {
    if (status === "running") {
        statusText.innerHTML = 'Status: <span class="running">Running</span>';
        enableTelegramCheckbox.checked = true;
        enableTelegramCheckbox.disabled = false;
        telegramSection.style.display = "block";

        installButton.classList.add("hidden");
        uninstallButton.classList.remove("hidden");
        startButton.classList.add("hidden");
        stopButton.classList.remove("hidden");
    } else if (status === "stopped") {
        statusText.innerHTML = 'Status: <span class="stopped">Stopped</span>';
        enableTelegramCheckbox.checked = true;
        enableTelegramCheckbox.disabled = false;
        telegramSection.style.display = "block";

        installButton.classList.add("hidden");
        uninstallButton.classList.remove("hidden");
        startButton.classList.remove("hidden");
        stopButton.classList.add("hidden");
    } else if (status === "uninstalled") {
        statusText.innerHTML = 'Status: <span class="stopped">Not Installed</span>';
        enableTelegramCheckbox.checked = false;
        enableTelegramCheckbox.disabled = false; 
        telegramSection.style.display = "none";

        installButton.classList.remove("hidden");
        uninstallButton.classList.add("hidden");
        startButton.classList.add("hidden");
        stopButton.classList.add("hidden");
    }
}

    function fetchConfig() {
    fetch("/get-telegram-config")
        .then(response => response.json())
        .then(data => {
            if (data["bot_token"]) botTokenInput.value = data["bot_token"];
            if (data["base_url"]) baseUrlInput.value = data["base_url"];
            if (data["api_key"]) apiKeyInput.value = data["api_key"];
        })
        .catch(error => console.error("Error in fetching bot config:", error));

    fetch("/get-admin-chat-ids")  
        .then(response => {
            if (!response.ok) throw new Error(`Error in: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.admin_chat_ids) {
                adminChatIdInput.value = data.admin_chat_ids.join(", ");
            } else {
                adminChatIdInput.value = ""; 
            }
        })
        .catch(error => console.error("Error in fetching admin chat IDs:", error));
}


    installButton.addEventListener("click", () => {
    const language = "en"; 
    fetch(`/install-telegram-${language}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "installing") {
                showProgressBar();
            } else {
                fetchBotStatus();
            }
        })
        .catch(error => console.error("error in toggling installation:", error));
});

    startButton.addEventListener("click", () => {
        fetch("/start-telegram", { method: "POST" })
            .then(() => fetchBotStatus())
            .catch(error => console.error("starting bot error:", error));
    });

    stopButton.addEventListener("click", () => {
        fetch("/stop-telegram", { method: "POST" })
            .then(() => fetchBotStatus())
            .catch(error => console.error("stopping bot error:", error));
    });

    enableTelegramCheckbox.addEventListener("change", (event) => {
    if (event.target.checked) {
        telegramSection.style.display = "block";
        installButton.classList.remove("hidden");
    } else {
        telegramSection.style.display = "none";
        installButton.classList.add("hidden");
    }
});


    function fetchApiKeys() {
        fetch("/get-api-keys", { method: "GET" })
            .then(response => response.json())
            .then(data => {
                if (data.api_keys) {
                    apiKeyList.innerHTML = ""; 
                    data.api_keys.forEach((key, index) => {
                        addApiKeyToList(key, index);
                    });
                }
            })
            .catch(error => console.error("fetching API keys error:", error));
    }
    function addApiKeyToList(apiKey, index) {
        const apiKeyBox = document.createElement("div");
        apiKeyBox.className = "api-key-box";
        apiKeyBox.innerHTML = `
            <span>${apiKey}</span>
            <button class="btn-danger" onclick="deleteApiKey(${index})">Delete</button>
        `;
        apiKeyList.appendChild(apiKeyBox);
    }

    enableTelegramCheckbox.addEventListener("change", (event) => {
        if (event.target.checked) {
            telegramSection.style.display = "block";
        } else {
            telegramSection.style.display = "none";
        }
    });

    createApiButton.addEventListener("click", () => {
    fetch("/create-api-key", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.api_key) {
                showAlert("API key created successfully.");
                fetchApiKeys(); 
            } else {
                showAlert("Couldn't create API key.");
            }
        })
        .catch(error => console.error("error in creating API key:", error));
});


    window.deleteApiKey = (index) => {
        fetch(`/delete-api-key/${index}`, { method: "DELETE" })
            .then(response => {
                if (response.ok) {
                    fetchApiKeys();
                } else {
                    showAlert("deleting API key failed.");
                }
            })
            .catch(error => console.error("deleting API key error:", error));
    };
    let alertShown = false;
    function showProgressBar() {
    const progressBarContainer = document.getElementById("progress-bar-container");
    const progressBar = document.getElementById("progress-bar");
    progressBarContainer.classList.remove("hidden");

    let interval = setInterval(() => {
        fetch("/telegram-install-progress")
            .then(response => response.json())
            .then(data => {
                progressBar.style.width = `${data.progress}%`;
                progressBar.textContent = `${data.progress}%`;

                if (data.message) {
                    console.log(data.message);
                }

                if ((data.progress >= 100 || !data.installing) && !alertShown) {
                    clearInterval(interval);
                    progressBarContainer.classList.add("hidden");
                    showAlert("installation completed!");
                    alertShown = true; 
                    fetchBotStatus(); 
                }
            })
            .catch(error => {
                console.error("error in fetching install progress:", error);
                clearInterval(interval);
                progressBarContainer.classList.add("hidden");
            });
    }, 1000);
}

    telegramForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const botToken = botTokenInput.value;
    const baseUrl = baseUrlInput.value;
    const apiKey = apiKeyInput.value;
    const adminChatIds = adminChatIdInput.value.split(",").map(id => id.trim()); 

    fetch("/save-telegram-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            bot_token: botToken,
            base_url: baseUrl,
            api_key: apiKey,
            admin_chat_ids: adminChatIds,
        }),
    })
        .then((response) => response.json())
        .then((data) => showAlert(data.message))
        .catch((error) => console.error("Error saving Telegram config:", error));
});


fetchConfig();
fetchAdminChatIds();
fetchBotStatus();
fetchApiKeys();
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