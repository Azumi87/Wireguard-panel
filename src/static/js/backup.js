const fetchBackups = async () => {
    const manualBackupList = document.querySelector("#manualBackupList tbody");
    const wireguardBackupList = document.querySelector("#wireguardBackupList tbody");
    const dbBackupList = document.querySelector("#dbBackupList tbody");

    try {
        const manualResponse = await fetch("/api/backups");
        const wireguardResponse = await fetch("/api/auto-backups?folder=wireguard");
        const dbResponse = await fetch("/api/auto-backups?folder=db");

        if (!manualResponse.ok) throw new Error("fetch manual backups has failed.");
        if (!wireguardResponse.ok) throw new Error("fetch Wireguard backups has failed.");
        if (!dbResponse.ok) throw new Error("fetch database backups has failed.");

        const manualData = await manualResponse.json();
        const wireguardData = await wireguardResponse.json();
        const dbData = await dbResponse.json();

        manualBackupList.innerHTML = manualData.backups?.length
            ? manualData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td>${backup}</td>
                          <td class="action-buttons">
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'manual')">Restore</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'manual')">Delete</button>
                              <button class="btn-primary" onclick="downloadBackup('${backup}')">Download</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2">No manual backups available.</td></tr>`;

        wireguardBackupList.innerHTML = wireguardData.backups?.length
            ? wireguardData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td>${backup}</td>
                          <td>
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'wireguard')">Restore</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'wireguard')">Delete</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2">No Wireguard backups available.</td></tr>`;

        dbBackupList.innerHTML = dbData.backups?.length
            ? dbData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td>${backup}</td>
                          <td>
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'db')">Restore</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'db')">Delete</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2">No database backups available.</td></tr>`;

    } catch (error) {
        console.error("fetching backups error:", error);

        manualBackupList.innerHTML = `<tr><td colspan="2">fetching manual backups failed.</td></tr>`;
        wireguardBackupList.innerHTML = `<tr><td colspan="2">fetching Wireguard backups failed.</td></tr>`;
        dbBackupList.innerHTML = `<tr><td colspan="2">fetching database backups failed.</td></tr>`;
    }
};

const deleteBackup = async (backupName, folder) => {
    showConfirm(`Are you sure you want to delete the backup ${backupName}?`, async (confirmed) => {
        if (confirmed) {
            try {
                const folderParam = folder === "manual" ? "root" : folder;

                const response = await fetch(`/api/delete-backup?name=${backupName}&folder=${folderParam}`, { method: "DELETE" });
                const data = await response.json();
                if (response.ok) {
                    showAlert(data.message || "backup deleted successfully");
                    fetchBackups();
                } else {
                    showAlert(data.error || "backup deletion failed");
                }
            } catch (error) {
                console.error("error in deleting backup", error);
                showAlert("error in deleting backup");
            }
        }
    });
};


const restoreBackup = async (backupName, folder) => {
    const endpoint =
        folder === "manual" ? "/api/restore-backup" : "/api/restore-automated-backup";

    showConfirm(`Are you sure you want to restore the backup ${backupName}?`, async (confirmed) => {
        if (confirmed) {
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ folder, backupName }),
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert(data.message || "backup restored successfully");
                    fetchBackups(); 
                } else {
                    showAlert(data.error || "restoring backup failed!");
                }
            } catch (error) {
                console.error("error in restoring backup", error);
                showAlert("error in restoring backup");
            }
        }
    });
};

document.addEventListener("DOMContentLoaded", () => {
    const createBackupBtn = document.getElementById("createBackupBtn");

    if (createBackupBtn) {
        const newBackupBtn = createBackupBtn.cloneNode(true);
        createBackupBtn.replaceWith(newBackupBtn);

        newBackupBtn.addEventListener("click", async () => {
            showConfirm("Are you sure you want to create a manual backup?", async (confirmed) => {
                if (confirmed) {
                    try {
                        const response = await fetch("/api/create-backup", { method: "POST" });
                        const data = await response.json();
                        if (response.ok) {
                            showAlert(data.message || "Backup created successfully!");
                            fetchBackups(); 
                        } else {
                            showAlert(data.error || "creating backup failed.");
                        }
                    } catch (error) {
                        console.error("creating manual backup error:", error);
                        showAlert("error occurred creating the backup.");
                    }
                }
            });
        });
    } else {
        console.error("Create Backup button not found in the DOM.");
    }
});

const fetchAutoBackups = async () => {
    const autoBackupList = document.querySelector("#autoBackupList tbody");

    try {
        const response = await fetch("/api/auto-backups");
        const data = await response.json();

        if (response.ok && data.backups) {
            autoBackupList.innerHTML = Object.entries(data.backups)
                .map(([config, backups]) =>
                    backups.map(
                        (backup) => `
                        <tr>
                            <td>${config} - ${backup}</td>
                            <td>
                                <button onclick="restoreAutoBackup('${config}', '${backup}')">/Restore</button>
                                <button onclick="deleteBackup('${backup}')">Delete</button>
                            </td>
                        </tr>`
                    ).join("")
                )
                .join("");
        } else {
            autoBackupList.innerHTML = `<tr><td colspan="2">Error loading automated backups.</td></tr>`;
        }
    } catch (error) {
        console.error("fetching automated backups error:", error);
        autoBackupList.innerHTML = `<tr><td colspan="2">fetching automated backups failed.</td></tr>`;
    }
};

const restoreAutoBackup = async (configName, backupName) => {
    showConfirm(`Restore backup ${backupName} for configuration ${configName}?`, async (confirmed) => {
        if (confirmed) {
            try {
                const response = await fetch("/api/restore-auto-backup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ configName, backupName }),
                });
                const data = await response.json();
                showAlert(data.message || "Backup restored successfully!");
            } catch (error) {
                console.error("restoring automated backup error:", error);
                showAlert("error occurred restoring the backup.");
            }
        }
    });
};

const downloadBackup = (backupName) => {
    window.open(`/api/download-backup?name=${backupName}`, "_blank");
};

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

window.onload = fetchBackups;
setInterval(fetchBackups, 30000);
