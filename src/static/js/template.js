document.addEventListener("DOMContentLoaded", function () {
  if (!window.peerInfo) {
    console.error("peerInfo is not defined.");
    return;
  }

  const { peerName, configFile, token } = window.peerInfo;

  if (!peerName || !configFile || !token) {
    console.error("Missing required parameters for peer details:", window.peerInfo);
    return;
  }

  console.log("Peer Info:", window.peerInfo);

  const peerNameElem = document.getElementById("peer-name");
  const dataLimitElem = document.getElementById("data-limit");
  const remainingAmountLbl = document.getElementById("remaining-amount-label");
  const expiryDateElem = document.getElementById("expiry-date");
  const dataProgressBar = document.getElementById("data-progress");
  const remainingProgress = document.getElementById("remaining-progress");
  const expiryProgress = document.getElementById("expiry-progress");
  const refreshBtn = document.getElementById("refresh-btn");
  const qrCodeBtn = document.getElementById("qr-code-btn");
  const downloadConfigBtn = document.getElementById("download-config-btn");
  const qrModal = document.getElementById("qr-modal");
  const qrImage = document.getElementById("qr-image");
  const closeModal = document.getElementById("close-modal");
  const clientStatusLabel = document.getElementById("client-status-label");

  function formatHumanReadableSize(sizeStr) {
    const match = /([\d.]+)\s*(\w+)/.exec(sizeStr);
    if (!match) {
      return "نامشخص";
    }
    const value = match[1];
    const unit = match[2];
    return `${value} ${unit}`;
  }

  function parseExpiryHuman(expiryHuman) {
  const daysMatch = /(\d+)\s*روز/.exec(expiryHuman);
  const hoursMatch = /(\d+)\s*ساعت/.exec(expiryHuman);
  const minutesMatch = /(\d+)\s*دقیقه/.exec(expiryHuman);

  const days = daysMatch ? parseInt(daysMatch[1], 10) : 0;
  const hours = hoursMatch ? parseInt(hoursMatch[1], 10) : 0;
  const minutes = minutesMatch ? parseInt(minutesMatch[1], 10) : 0;

  return { days, hours, minutes };
}

let expiryTimeRemaining = 0;

  function formatRemainingTime(totalMinutes) {
    const days = Math.floor(totalMinutes / (24 * 60));
    const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
    const minutes = totalMinutes % 60;

    return `${days} روز، ${hours} ساعت، ${minutes} دقیقه`;
  }

function updateProgressBars(data) {
  const totalTimeMinutes = 30 * 24 * 60; // 30 days
  const remainingTimeMinutes = data.remaining_time || 0;
  const timeRatio = (remainingTimeMinutes / totalTimeMinutes) * 100;
  expiryProgress.style.width = `${Math.min(100, timeRatio)}%`;
  expiryProgress.style.backgroundColor = "#16a085";

  const remainingData = parseFloat(data.remaining_human || "0");
  const totalData = parseFloat(data.limit_human || "0");
  const dataRatio = (totalData > 0) ? (remainingData / totalData) * 100 : 100; 
  remainingProgress.style.width = `${Math.min(100, dataRatio)}%`;
  remainingProgress.style.backgroundColor = "#16a085";

  if (dataRatio === 0) {
    remainingProgress.style.backgroundColor = "#F44336"; 
  }
  if (timeRatio === 0) {
    expiryProgress.style.backgroundColor = "#F44336"; 
  }
}

function updateTimeRemaining() {
    if (expiryTimeRemaining > 0) {
      expiryTimeRemaining--;
      expiryDateElem.textContent = formatRemainingTime(expiryTimeRemaining);

      const totalMinutes = 30 * 24 * 60; 
      const expiryRatio = (expiryTimeRemaining / totalMinutes) * 100;
      expiryProgress.style.width = `${Math.min(100, expiryRatio)}%`;
    } else {
      expiryDateElem.textContent = "منقضی";
      expiryProgress.style.width = "0%";
    }
  }
function fetchPeerDetails() {
  const url = `/api/peer-detailz?peer_name=${encodeURIComponent(peerName)}`
    + `&config_file=${encodeURIComponent(configFile)}`
    + `&token=${encodeURIComponent(token)}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }

      peerNameElem.textContent = data.peer_name || "نامشخص";
      dataLimitElem.textContent = data.limit_human || "0 MiB";
      remainingAmountLbl.textContent = data.remaining_human || "0 MiB";
      expiryTimeRemaining = data.remaining_time || 0;

      if (data.status === "active") {
        clientStatusLabel.textContent = "فعال";
        clientStatusLabel.style.color = "#4CAF50";
      } else {
        clientStatusLabel.textContent = "غیرفعال";
        clientStatusLabel.style.color = "#F44336";
      }

      updateProgressBars(data);
      updateTimeRemaining(); 
    })
    .catch(error => {
      console.error("error in fetching peer details:", error);
    });
}



  refreshBtn.addEventListener("click", fetchPeerDetails);
  qrCodeBtn.addEventListener("click", function () {
    const url = `/api/qr-code?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(configFile)}`;
    fetch(url)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }
        qrImage.src = data.qr_code;
        qrModal.style.display = "flex";
      });
  });
  downloadConfigBtn.addEventListener("click", function () {
    const url = `/api/download-peer-config?peerName=${encodeURIComponent(peerName)}&config=${encodeURIComponent(configFile)}`;
    window.open(url, "_blank");
  });
  closeModal.addEventListener("click", () => {
    qrModal.style.display = "none";
  });

  fetchPeerDetails();
  setInterval(fetchPeerDetails, 5000);
});