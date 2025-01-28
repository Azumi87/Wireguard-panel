const fetchBackups = async () => {
    const manualBackupList = document.querySelector("#manualBackupList tbody");
    const wireguardBackupList = document.querySelector("#wireguardBackupList tbody");
    const dbBackupList = document.querySelector("#dbBackupList tbody");

    try {
        const manualResponse = await fetch("/api/backups");
        const wireguardResponse = await fetch("/api/auto-backups?folder=wireguard");
        const dbResponse = await fetch("/api/auto-backups?folder=db");

        if (!manualResponse.ok) throw new Error("دریافت پشتیبان‌های دستی موفقیت امیز نبود.");
        if (!wireguardResponse.ok) throw new Error("دریافت پشتیبان‌های Wireguard موفقیت امیز نبود");
        if (!dbResponse.ok) throw new Error("دریافت پشتیبان‌های دیتابیس موفقیت امیز نبود");

        const manualData = await manualResponse.json();
        const wireguardData = await wireguardResponse.json();
        const dbData = await dbResponse.json();

        manualBackupList.innerHTML = manualData.backups?.length
            ? manualData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td dir="rtl">${backup}</td>
                          <td class="action-buttons">
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'manual')">بازیابی</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'manual')">حذف</button>
                              <button class="btn-primary" onclick="downloadBackup('${backup}')">دانلود</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2" dir="rtl">پشتیبان دستی موجود نیست.</td></tr>`;

        wireguardBackupList.innerHTML = wireguardData.backups?.length
            ? wireguardData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td dir="rtl">${backup}</td>
                          <td>
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'wireguard')">بازیابی</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'wireguard')">حذف</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2" dir="rtl">پشتیبان‌های وایرگارد موجود نیست.</td></tr>`;

        dbBackupList.innerHTML = dbData.backups?.length
            ? dbData.backups
                  .map(
                      (backup) => `
                      <tr>
                          <td dir="rtl">${backup}</td>
                          <td>
                              <button class="btn-primary" onclick="restoreBackup('${backup}', 'db')">بازیابی</button>
                              <button class="btn-primary" onclick="deleteBackup('${backup}', 'db')">حذف</button>
                          </td>
                      </tr>`
                  )
                  .join("")
            : `<tr><td colspan="2" dir="rtl">پشتیبان‌های دیتابیس موجود نیست.</td></tr>`;

    } catch (error) {
        console.error("خطا در دریافت پشتیبان‌ها:", error);

        manualBackupList.innerHTML = `<tr><td colspan="2" dir="rtl">دریافت پشتیبان‌های دستی با شکست مواجه شد.</td></tr>`;
        wireguardBackupList.innerHTML = `<tr><td colspan="2" dir="rtl">دریافت پشتیبان‌های Wireguard با شکست مواجه شد.</td></tr>`;
        dbBackupList.innerHTML = `<tr><td colspan="2" dir="rtl">دریافت پشتیبان‌های دیتابیس با شکست مواجه شد.</td></tr>`;
    }
};


const deleteBackup = async (backupName, folder) => {
    showConfirm(`آیا از حذف پشتیبان ${backupName} مطمئن هستید؟`, async (confirmed) => {
        if (confirmed) {
            try {
                const folderParam = folder === "manual" ? "root" : folder;

                const response = await fetch(`/api/delete-backup?name=${backupName}&folder=${folderParam}`, { method: "DELETE" });
                const data = await response.json();
                if (response.ok) {
                    showAlert(data.message || "پشتیبان با موفقیت حذف شد!");
                    fetchBackups();
                } else {
                    showAlert(data.error || "حذف پشتیبان موفقیت امیز نبود");
                }
            } catch (error) {
                console.error("خطا در حذف پشتیبان:", error);
                showAlert("خطا در حذف پشتیبان.");
            }
        }
    });
};


const restoreBackup = async (backupName, folder) => {
    const endpoint =
        folder === "manual" ? "/api/restore-backup" : "/api/restore-automated-backup";

    showConfirm(`آیا از بازیابی پشتیبان: ${backupName} مطمئن هستید؟`, async (confirmed) => {
        if (confirmed) {
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ folder, backupName }),
                });
                const data = await response.json();
                if (response.ok) {
                    showAlert(data.message || "پشتیبان با موفقیت بازیابی شد!");
                    fetchBackups(); 
                } else {
                    showAlert(data.error || "بازیابی پشتیبان موفقیت امیز نبود");
                }
            } catch (error) {
                console.error("خطا در بازیابی پشتیبان:", error);
                showAlert("خطا در بازیابی پشتیبان.");
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
            showConfirm("آیا از ایجاد پشتیبان دستی مطمئن هستید؟", async (confirmed) => {
                if (confirmed) {
                    try {
                        const response = await fetch("/api/create-backup", { method: "POST" });
                        const data = await response.json();
                        if (response.ok) {
                            showAlert(data.message || "پشتیبان با موفقیت ایجاد شد!");
                            fetchBackups(); 
                        } else {
                            showAlert(data.error || "ایجاد پشتیبان موفقیت امیز نبود");
                        }
                    } catch (error) {
                        console.error("خطا در ایجاد پشتیبان دستی:", error);
                        showAlert("خطا در ایجاد پشتیبان.");
                    }
                }
            });
        });
    } else {
        console.error("دکمه ایجاد پشتیبان در DOM یافت نشد.");
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
                                <button onclick="restoreAutoBackup('${config}', '${backup}')">بازیابی</button>
                                <button onclick="deleteBackup('${backup}')">حذف</button>
                            </td>
                        </tr>`
                    ).join("")
                )
                .join("");
        } else {
            autoBackupList.innerHTML = `<tr><td colspan="2">خطا در بارگذاری پشتیبان‌های خودکار.</td></tr>`;
        }
    } catch (error) {
        console.error("خطا در دریافت پشتیبان‌های خودکار:", error);
        autoBackupList.innerHTML = `<tr><td colspan="2">دریافت پشتیبان‌های خودکار موفقیت امیز نبود</td></tr>`;
    }
};

const restoreAutoBackup = async (configName, backupName) => {
    showConfirm(`آیا از بازیابی پشتیبان ${backupName} برای کانفیگ ${configName} مطمئن هستید؟`, async (confirmed) => {
        if (confirmed) {
            try {
                const response = await fetch("/api/restore-auto-backup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ configName, backupName }),
                });
                const data = await response.json();
                showAlert(data.message || "پشتیبان با موفقیت بازیابی شد!");
            } catch (error) {
                console.error("خطا در بازیابی پشتیبان خودکار:", error);
                showAlert("خطا در بازیابی پشتیبان.");
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
