async function loadSettings() {
        try {
            const flaskResponse = await fetch('/api/flask-config');
            if (!flaskResponse.ok) throw new Error("fetching Flask config failed");
            const flaskConfig = await flaskResponse.json();
            document.getElementById('webPort').value = flaskConfig.port || '';
            document.getElementById('enableTLS').value = flaskConfig.tls ? "true" : "false";

            const userResponse = await fetch('/api/user-info');
            if (!userResponse.ok) throw new Error("fetching user info failed");
            const userInfo = await userResponse.json();
            document.getElementById('newUsername').value = userInfo.username || '';

            const wgResponse = await fetch('/api/configs');
            if (!wgResponse.ok) throw new Error("fetching Wireguard configs failed");
            const wgConfigs = await wgResponse.json();
            const configSelect = document.getElementById('wgConfigSelect');

            configSelect.innerHTML = ""; 
            wgConfigs.configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config;
                option.textContent = config;
                configSelect.appendChild(option);
            });

            if (wgConfigs.configs.length > 0) {
                configSelect.value = wgConfigs.configs[0];
                await loadWGDetails(wgConfigs.configs[0]);
            }

            configSelect.addEventListener('change', (event) => {
                loadWGDetails(event.target.value);
            });
        } catch (error) {
            console.error('loading settings error:', error);
            showAlert(`loading settings error: ${error.message}`);
        }
    }

    async function loadWGDetails(configName) {
        try {
            const response = await fetch(`/api/config-details?config=${configName}`);
            if (!response.ok) throw new Error("fetching Wireguard config details failed");
            const details = await response.json();

            document.getElementById('wgPort').value = details.ListenPort || '';
            document.getElementById('wgMTU').value = details.MTU || '';
            document.getElementById('wgDNS').value = details.DNS || '';
        } catch (error) {
            console.error('loading Wireguard config details has failed:', error);
        }
    }

    document.getElementById('updateUserForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('/api/update-user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('newUsername').value,
                    password: document.getElementById('newPassword').value
                })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || "updating user has failed");
            showAlert(result.message);
        } catch (error) {
            console.error('updating user error:', error);
            showAlert(`updating user error: ${error.message}`);
        }
    });
    document.addEventListener('DOMContentLoaded', () => {
        
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const tlsSelect = document.getElementById('enableTLS');
    const tlsDependentFields = document.querySelectorAll('.tls-dependent');
    tlsSelect.addEventListener('change', () => {
        const isTLS = tlsSelect.value === 'true';
        tlsDependentFields.forEach(field => {
            field.style.display = isTLS ? 'block' : 'none';
        });
    });

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });

    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const container = header.parentElement;
            container.classList.toggle('active');
        });
    });
});


    document.getElementById('updateFlaskForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        const portString = document.getElementById('webPort').value;
        const port = parseInt(portString, 10); 
        const tls = document.getElementById('enableTLS').value === 'true';
        const certPath = document.getElementById('certPath').value;
        const keyPath = document.getElementById('keyPath').value;

        if (isNaN(port) || port < 1 || port > 65535) {
            showAlert("Port must be between 1 and 65535.");
            return;
        }

        const requestBody = { port: port, tls: tls };

        if (tls) {
            requestBody.cert_path = certPath;
            requestBody.key_path = keyPath;
        }

        const response = await fetch('/api/update-flask-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "updating Flask config has failed");
        showAlert(result.message);
    } catch (error) {
        console.error('updating Flask config error:', error);
        showAlert(`updating Flask config error: ${error.message}`);
    }
});


    document.getElementById('updateWGForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            const response = await fetch('/api/update-wireguard-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    config: document.getElementById('wgConfigSelect').value,
                    port: document.getElementById('wgPort').value || null,
                    mtu: document.getElementById('wgMTU').value || null,
                    dns: document.getElementById('wgDNS').value || null
                })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || "updating Wireguard config has failed");
            showAlert(result.message);
        } catch (error) {
            console.error('updating Wireguard config has failed:', error);
            showAlert(`updating Wireguard config error: ${error.message}`);
        }
    });
    async function loadCustomIp() {
            try {
                const response = await fetch('/api/get-custom-ip');
                if (!response.ok) throw new Error("fetching custom IP failed");
                const data = await response.json();
                document.getElementById('customIp').value = data.custom_ip || '';
            } catch (error) {
                console.error('loading custom IP error:', error);
                showAlert(`loading custom IP error: ${error.message}`);
            }
        }

        document.getElementById('updateCustomIpForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const customIp = document.getElementById('customIp').value.trim();

    try {
        const response = await fetch('/api/update-custom-ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ custom_ip: customIp })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "Updating custom IP/Subdomain failed");
        showAlert(result.message);
        loadCustomIp();
    } catch (error) {
        console.error('Updating custom IP/Subdomain error:', error);
        showAlert(`Updating custom IP/Subdomain error: ${error.message}`);
    }
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

    loadCustomIp();
    loadSettings();