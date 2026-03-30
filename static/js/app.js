(function () {
  "use strict";

  // --- DOM refs ---
  var dropzone     = document.getElementById("dropzone");
  var fileInput    = document.getElementById("fileInput");
  var fileList     = document.getElementById("fileList");
  var settingsArea = document.getElementById("settingsArea");
  var processBtn   = document.getElementById("processBtn");
  var clearBtn     = document.getElementById("clearBtn");
  var shuffleBtn   = document.getElementById("shuffleBtn");
  var statusMsg    = document.getElementById("statusMsg");
  var overlay      = document.getElementById("processingOverlay");
  var pdfPreview   = document.getElementById("pdfPreviewSection");
  var pdfViewer    = document.getElementById("pdfViewer");
  var downloadBtn  = document.getElementById("downloadBtn");
  var backBtn      = document.getElementById("backBtn");

  // --- Config from data attributes ---
  var cfg = {
    accept:     dropzone.dataset.accept,
    multiple:   dropzone.dataset.multiple === "true",
    endpoint:   dropzone.dataset.endpoint,
    resultType: dropzone.dataset.resultType,
    toolName:   dropzone.dataset.toolName
  };

  // --- State ---
  var files = [];
  var dragIdx = null;
  var blobUrl = null;
  var resultFilename = "output";

  // ============================================================
  // FILE MANAGEMENT
  // ============================================================

  function addFiles(incoming) {
    var arr = Array.prototype.slice.call(incoming);
    var accepted = arr.filter(function (f) {
      if (cfg.accept === "image/*") return f.type.indexOf("image/") === 0;
      if (cfg.accept === ".pdf")
        return f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf");
      return true;
    });

    if (!cfg.multiple) {
      files = accepted.length ? [accepted[0]] : [];
    } else {
      files = files.concat(accepted);
    }
    cleanupPreview();
    renderFileList();
    setStatus("");
  }

  function removeFile(idx) {
    files.splice(idx, 1);
    renderFileList();
  }

  function clearFiles() {
    files = [];
    cleanupPreview();
    renderFileList();
    setStatus("");
  }

  function shuffleFiles() {
    for (var i = files.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = files[i];
      files[i] = files[j];
      files[j] = tmp;
    }
    renderFileList();
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  // ============================================================
  // RENDER FILE LIST
  // ============================================================

  function renderFileList() {
    while (fileList.firstChild) fileList.removeChild(fileList.firstChild);

    var hasFiles = files.length > 0;
    settingsArea.classList.toggle("active", hasFiles);
    processBtn.disabled = !hasFiles;
    if (shuffleBtn) shuffleBtn.disabled = files.length < 2;

    files.forEach(function (file, idx) {
      var item = document.createElement("div");
      item.className = "file-item";
      item.draggable = cfg.multiple;
      item.dataset.idx = idx;

      var left = document.createElement("div");
      left.className = "file-item-left";

      if (cfg.multiple) {
        var grip = document.createElement("span");
        grip.className = "file-item-grip";
        grip.textContent = "\u2261";
        left.appendChild(grip);
      }

      var name = document.createElement("span");
      name.className = "file-item-name";
      name.textContent = file.name;
      left.appendChild(name);

      var size = document.createElement("span");
      size.className = "file-item-size";
      size.textContent = formatSize(file.size);

      var removeBtn = document.createElement("button");
      removeBtn.className = "file-item-remove";
      removeBtn.textContent = "\u00d7";
      removeBtn.addEventListener("click", function () { removeFile(idx); });

      item.appendChild(left);
      item.appendChild(size);
      item.appendChild(removeBtn);

      // Drag-and-drop reorder
      if (cfg.multiple) {
        (function (currentIdx) {
          item.addEventListener("dragstart", function () {
            dragIdx = currentIdx;
            item.classList.add("dragging");
          });
          item.addEventListener("dragend", function () {
            item.classList.remove("dragging");
            dragIdx = null;
            var overs = document.querySelectorAll(".drag-over");
            for (var k = 0; k < overs.length; k++) overs[k].classList.remove("drag-over");
          });
          item.addEventListener("dragover", function (e) {
            e.preventDefault();
            item.classList.add("drag-over");
          });
          item.addEventListener("dragleave", function () {
            item.classList.remove("drag-over");
          });
          item.addEventListener("drop", function (e) {
            e.preventDefault();
            item.classList.remove("drag-over");
            if (dragIdx === null || dragIdx === currentIdx) return;
            var moved = files.splice(dragIdx, 1)[0];
            files.splice(currentIdx, 0, moved);
            renderFileList();
          });
        })(idx);
      }

      fileList.appendChild(item);
    });
  }

  // ============================================================
  // DROPZONE EVENTS
  // ============================================================

  dropzone.addEventListener("click", function () { fileInput.click(); });

  dropzone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropzone.classList.add("active");
  });

  dropzone.addEventListener("dragleave", function () {
    dropzone.classList.remove("active");
  });

  dropzone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropzone.classList.remove("active");
    addFiles(e.dataTransfer.files);
  });

  fileInput.addEventListener("change", function () {
    addFiles(fileInput.files);
    fileInput.value = "";
  });

  // ============================================================
  // BUTTON EVENTS
  // ============================================================

  clearBtn.addEventListener("click", clearFiles);
  if (shuffleBtn) shuffleBtn.addEventListener("click", shuffleFiles);

  // ============================================================
  // TOGGLES
  // ============================================================

  var toggleEls = document.querySelectorAll("[data-toggle-name]");
  for (var t = 0; t < toggleEls.length; t++) {
    (function (el) {
      el.addEventListener("click", function () {
        el.classList.toggle("active");
      });
    })(toggleEls[t]);
  }

  // ============================================================
  // PROCESS
  // ============================================================

  processBtn.addEventListener("click", function () {
    if (files.length === 0) return;

    var formData = new FormData();
    files.forEach(function (f) { formData.append("files", f); });

    // Collect fields
    var fieldEls = document.querySelectorAll("[data-field-name]");
    for (var i = 0; i < fieldEls.length; i++) {
      var el = fieldEls[i];
      var val = el.value;
      if (el.hasAttribute("required") && !val) {
        setStatus(el.dataset.fieldName + " is required.", "error");
        el.focus();
        return;
      }
      formData.append(el.dataset.fieldName, val);
    }

    // Collect toggles
    for (var j = 0; j < toggleEls.length; j++) {
      formData.append(
        toggleEls[j].dataset.toggleName,
        toggleEls[j].classList.contains("active") ? "true" : "false"
      );
    }

    overlay.classList.add("active");
    processBtn.disabled = true;
    setStatus("");
    cleanupPreview();

    fetch(cfg.endpoint, { method: "POST", body: formData })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (data) { throw new Error(data.error || "Server error"); });
        }
        return res.blob();
      })
      .then(function (blob) {
        overlay.classList.remove("active");

        blobUrl = URL.createObjectURL(blob);

        if (cfg.resultType === "pdf") {
          pdfViewer.src = blobUrl;
          pdfPreview.classList.add("visible");
          pdfPreview.scrollIntoView({ behavior: "smooth" });
          resultFilename = cfg.toolName + "_output.pdf";
          setStatus("Done! Preview your PDF below.", "success");
        } else {
          // Direct download for zip / non-previewable
          var ext = blob.type.indexOf("zip") !== -1 ? ".zip" : ".pdf";
          resultFilename = cfg.toolName + "_output" + ext;
          triggerDownload(blobUrl, resultFilename);
          setStatus("Done! Your download has started.", "success");
        }
      })
      .catch(function (err) {
        overlay.classList.remove("active");
        setStatus(err.message, "error");
      })
      .finally(function () {
        processBtn.disabled = files.length === 0;
      });
  });

  // ============================================================
  // PREVIEW / DOWNLOAD
  // ============================================================

  downloadBtn.addEventListener("click", function () {
    if (blobUrl) {
      triggerDownload(blobUrl, resultFilename);
      setStatus("Downloaded!", "success");
    }
  });

  backBtn.addEventListener("click", function () {
    cleanupPreview();
    setStatus("");
  });

  function cleanupPreview() {
    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
      blobUrl = null;
    }
    pdfViewer.src = "";
    pdfPreview.classList.remove("visible");
  }

  function triggerDownload(url, filename) {
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
  }

  // ============================================================
  // STATUS
  // ============================================================

  function setStatus(msg, type) {
    statusMsg.textContent = msg;
    statusMsg.className = "status-msg" + (type ? " " + type : "");
  }

})();
