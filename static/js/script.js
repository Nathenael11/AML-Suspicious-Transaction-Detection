/**
 * AML Shield - Dashboard Interactivity, Inference API & Batch CSV Processor
 */

document.addEventListener('DOMContentLoaded', () => {
  // ==========================================================================
  // 1. SINGLE TRANSACTION PREDICTION MODULE
  // ==========================================================================
  const form = document.getElementById('aml-form');
  const btnAnalyze = document.getElementById('btn-analyze');
  
  const resultPlaceholder = document.getElementById('result-placeholder');
  const resultContent = document.getElementById('result-content');
  
  const gaugeFill = document.getElementById('gauge-fill');
  const gaugeScoreVal = document.getElementById('gauge-score-val');
  const alertBadge = document.getElementById('alert-badge');
  const recommendationBox = document.getElementById('recommendation-box');
  const recBodyText = document.getElementById('rec-body-text');
  
  const historyTableBody = document.getElementById('history-table-body');
  const btnExportCsv = document.getElementById('btn-export-csv');

  // Single prediction preset scenario buttons
  const btnNormal = document.getElementById('btn-preset-normal');
  const btnSuspicious = document.getElementById('btn-preset-suspicious');
  const btnMismatch = document.getElementById('btn-preset-mismatch');

  if (btnNormal) {
    btnNormal.addEventListener('click', () => {
      document.getElementById('from_bank').value = 'Bank_Alpha';
      document.getElementById('from_account').value = 'ACC_100928';
      document.getElementById('to_bank').value = 'Bank_Alpha';
      document.getElementById('to_account').value = 'ACC_500112';
      document.getElementById('amount_paid').value = '1200.00';
      document.getElementById('amount_received').value = '1200.00';
      document.getElementById('payment_currency').value = 'USD';
      document.getElementById('receiving_currency').value = 'USD';
      document.getElementById('payment_format').value = 'ACH';
    });
  }

  if (btnSuspicious) {
    btnSuspicious.addEventListener('click', () => {
      document.getElementById('from_bank').value = 'Bank_Offshore';
      document.getElementById('from_account').value = 'ACC_HUB_99';
      document.getElementById('to_bank').value = 'Bank_Global';
      document.getElementById('to_account').value = 'ACC_RECV_44';
      document.getElementById('amount_paid').value = '49000.00';
      document.getElementById('amount_received').value = '41500.00';
      document.getElementById('payment_currency').value = 'USD';
      document.getElementById('receiving_currency').value = 'EUR';
      document.getElementById('payment_format').value = 'Wire';
    });
  }

  if (btnMismatch) {
    btnMismatch.addEventListener('click', () => {
      document.getElementById('from_bank').value = 'Bank_Beta';
      document.getElementById('from_account').value = 'ACC_3301';
      document.getElementById('to_bank').value = 'Bank_Gamma';
      document.getElementById('to_account').value = 'ACC_4402';
      document.getElementById('amount_paid').value = '25000.00';
      document.getElementById('amount_received').value = '25000.00';
      document.getElementById('payment_currency').value = 'USD';
      document.getElementById('receiving_currency').value = 'JPY';
      document.getElementById('payment_format').value = 'Cheque';
    });
  }

  if (historyTableBody) {
    loadHistory();
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      const payload = {
        from_bank: formData.get('from_bank'),
        from_account: formData.get('from_account'),
        to_bank: formData.get('to_bank'),
        to_account: formData.get('to_account'),
        amount_paid: parseFloat(formData.get('amount_paid')),
        payment_currency: formData.get('payment_currency'),
        amount_received: parseFloat(formData.get('amount_received')),
        receiving_currency: formData.get('receiving_currency'),
        payment_format: formData.get('payment_format'),
        timestamp: formData.get('timestamp')
      };

      btnAnalyze.disabled = true;
      btnAnalyze.innerHTML = '<div class="spinner"></div><span>Running Inference...</span>';

      try {
        const response = await fetch('/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const resData = await response.json();

        if (response.ok && resData.success) {
          displayResults(resData.prediction);
          if (resData.audit_entry) {
            prependHistoryRow(resData.audit_entry);
          }
        } else {
          alert(`Prediction Error: ${resData.error || 'Unknown error occurred'}`);
        }
      } catch (err) {
        console.error('API call failed:', err);
        alert(`Network error contacting prediction endpoint: ${err.message}`);
      } finally {
        btnAnalyze.disabled = false;
        btnAnalyze.innerHTML = `
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          <span>Run Risk Inference</span>
        `;
      }
    });
  }

  function displayResults(pred) {
    if (!resultPlaceholder || !resultContent) return;
    resultPlaceholder.style.display = 'none';
    resultContent.style.display = 'flex';

    const score = pred.risk_score;
    const alertLevel = pred.alert_level;

    const maxOffset = 440;
    const targetOffset = maxOffset - (score * maxOffset);

    let strokeColor = 'var(--risk-low-border)';
    if (alertLevel === 'High') {
      strokeColor = 'var(--risk-high-border)';
    } else if (alertLevel === 'Medium') {
      strokeColor = 'var(--risk-med-border)';
    }

    gaugeFill.style.stroke = strokeColor;
    gaugeFill.style.strokeDashoffset = targetOffset;

    animateScoreCounter(score);

    alertBadge.className = `alert-badge alert-${alertLevel.toLowerCase()}`;
    alertBadge.innerHTML = `<span>${alertLevel} Risk ${pred.is_suspicious ? '(SUSPICIOUS)' : '(NORMAL)'}</span>`;

    recommendationBox.className = `recommendation-box ${alertLevel.toLowerCase()}`;
    recBodyText.textContent = pred.action_recommendation;
  }

  function animateScoreCounter(targetVal) {
    let startVal = 0.0;
    const duration = 600;
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentVal = startVal + progress * (targetVal - startVal);
      if (gaugeScoreVal) gaugeScoreVal.textContent = currentVal.toFixed(2);

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        if (gaugeScoreVal) gaugeScoreVal.textContent = targetVal.toFixed(2);
      }
    }
    requestAnimationFrame(updateCounter);
  }

  async function loadHistory() {
    try {
      const response = await fetch('/api/history?limit=100');
      const data = await response.json();

      if (data.success && data.history && data.history.length > 0) {
        historyTableBody.innerHTML = '';
        data.history.forEach(row => {
          appendHistoryRow(row);
        });
      }
    } catch (err) {
      console.warn('Could not load history table:', err);
    }
  }

  function appendHistoryRow(row) {
    const tr = createRowElement(row);
    historyTableBody.appendChild(tr);
  }

  function prependHistoryRow(row) {
    if (historyTableBody.children.length === 1 && historyTableBody.children[0].cells.length === 1) {
      historyTableBody.innerHTML = '';
    }
    const tr = createRowElement(row);
    historyTableBody.insertBefore(tr, historyTableBody.firstChild);
  }

  function createRowElement(row) {
    const tr = document.createElement('tr');
    const alertClass = row.alert_level ? row.alert_level.toLowerCase() : 'low';
    const isSuspicious = row.is_suspicious === true || row.is_suspicious === 'True' || row.is_suspicious === 'true';

    tr.innerHTML = `
      <td>${row.timestamp || ''}</td>
      <td>${row.from_bank || ''}:${row.from_account || ''}</td>
      <td>${row.to_bank || ''}:${row.to_account || ''}</td>
      <td>$${parseFloat(row.amount_paid || 0).toLocaleString()} ${row.payment_currency || ''}</td>
      <td>$${parseFloat(row.amount_received || 0).toLocaleString()} ${row.receiving_currency || ''}</td>
      <td>${row.payment_format || ''}</td>
      <td><strong>${parseFloat(row.risk_score || 0).toFixed(4)}</strong></td>
      <td><span class="alert-badge alert-${alertClass}" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;">${row.alert_level || 'Low'}</span></td>
      <td style="font-weight: 600; color: ${isSuspicious ? 'var(--risk-high-border)' : 'var(--risk-low-border)'}">
        ${isSuspicious ? 'SUSPICIOUS' : 'NORMAL'}
      </td>
    `;
    return tr;
  }

  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      window.location.href = `/export-csv?ts=${Date.now()}`;
    });
  }

  // ==========================================================================
  // 2. BATCH CSV PREDICTION MODULE
  // ==========================================================================
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('batch-file-input');
  const browseTrigger = document.getElementById('browse-trigger');
  
  const fileInfoBox = document.getElementById('file-info-box');
  const fileNameEl = document.getElementById('file-name');
  const fileMetaEl = document.getElementById('file-meta');
  const btnRemoveFile = document.getElementById('btn-remove-file');
  
  const previewContainer = document.getElementById('preview-container');
  const previewThead = document.getElementById('preview-thead');
  const previewTbody = document.getElementById('preview-tbody');
  
  const btnProcessBatch = document.getElementById('btn-process-batch');
  
  const batchProgressCard = document.getElementById('batch-progress-card');
  const batchProgressFill = document.getElementById('batch-progress-fill');
  const batchProgressPercent = document.getElementById('batch-progress-percent');
  const batchProgressText = document.getElementById('batch-progress-text');
  
  const batchSummaryGrid = document.getElementById('batch-summary-grid');
  const statTotal = document.getElementById('stat-total');
  const statTime = document.getElementById('stat-time');
  const statHigh = document.getElementById('stat-high');
  const statHighPct = document.getElementById('stat-high-pct');
  const statMed = document.getElementById('stat-med');
  const statLow = document.getElementById('stat-low');
  const statAvg = document.getElementById('stat-avg');
  
  const batchResultsCard = document.getElementById('batch-results-card');
  const batchResultsTbody = document.getElementById('batch-results-tbody');
  const btnExportBatchCsv = document.getElementById('btn-export-batch-csv');

  const thSortScore = document.getElementById('th-sort-score');
  const thSortAlert = document.getElementById('th-sort-alert');

  let selectedFile = null;
  let batchPredictionsData = [];
  let sortDirectionScore = 'desc';
  let sortDirectionAlert = 'desc';

  if (dropzone && fileInput) {
    // Browse trigger
    browseTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropzone.addEventListener('click', () => {
      fileInput.click();
    });

    // Drag & Drop events
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
      }
    });
  }

  if (btnRemoveFile) {
    btnRemoveFile.addEventListener('click', () => {
      resetBatchSelection();
    });
  }

  function handleFileSelection(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Invalid file format. Please select a CSV file (.csv).');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('File size exceeds 10MB limit. Please upload a smaller file.');
      return;
    }

    selectedFile = file;
    fileNameEl.textContent = file.name;
    const sizeKb = (file.size / 1024).toFixed(1);

    // Read CSV for preview & line count
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split(/\r\n|\n/).filter(line => line.trim().length > 0);
      const rowCount = Math.max(0, lines.length - 1); // Exclude header

      if (rowCount > 10000) {
        alert(`CSV file contains ${rowCount} rows, exceeding the 10,000 row batch limit.`);
        resetBatchSelection();
        return;
      }

      fileMetaEl.textContent = `${sizeKb} KB • ${rowCount.toLocaleString()} Rows detected`;
      fileInfoBox.style.display = 'flex';
      btnProcessBatch.disabled = false;

      // Render 5-row preview
      renderDataPreview(lines);
    };
    reader.readAsText(file);
  }

  function renderDataPreview(lines) {
    if (lines.length === 0) return;

    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    const previewRows = lines.slice(1, 6).map(line => line.split(',').map(cell => cell.trim().replace(/^"|"$/g, '')));

    previewThead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    previewTbody.innerHTML = previewRows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('');

    previewContainer.style.display = 'block';
  }

  function resetBatchSelection() {
    selectedFile = null;
    if (fileInput) fileInput.value = '';
    if (fileInfoBox) fileInfoBox.style.display = 'none';
    if (previewContainer) previewContainer.style.display = 'none';
    if (btnProcessBatch) btnProcessBatch.disabled = true;
    if (batchProgressCard) batchProgressCard.style.display = 'none';
    if (batchSummaryGrid) batchSummaryGrid.style.display = 'none';
    if (batchResultsCard) batchResultsCard.style.display = 'none';
  }

  // Process Batch Submit Handler
  if (btnProcessBatch) {
    btnProcessBatch.addEventListener('click', async () => {
      if (!selectedFile) return;

      btnProcessBatch.disabled = true;
      btnProcessBatch.innerHTML = '<div class="spinner"></div><span>Uploading & Analyzing Batch...</span>';

      batchProgressCard.style.display = 'block';
      batchSummaryGrid.style.display = 'none';
      batchResultsCard.style.display = 'none';

      // Animate progress bar simulation
      animateProgressBar(0, 85, 2000);

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const response = await fetch('/api/batch-predict', {
          method: 'POST',
          body: formData
        });

        const resData = await response.json();

        if (response.ok && resData.success) {
          animateProgressBar(85, 100, 300, () => {
            batchProgressCard.style.display = 'none';
            renderBatchResults(resData.summary, resData.predictions);
          });
        } else {
          batchProgressCard.style.display = 'none';
          alert(`Batch Processing Error: ${resData.error || 'Unknown error'}`);
        }
      } catch (err) {
        console.error('Batch upload error:', err);
        batchProgressCard.style.display = 'none';
        alert(`Network error uploading batch file: ${err.message}`);
      } finally {
        btnProcessBatch.disabled = false;
        btnProcessBatch.innerHTML = `
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
          </svg>
          <span>Execute Batch Risk Inference</span>
        `;
      }
    });
  }

  function animateProgressBar(startPercent, endPercent, duration, callback) {
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentPercent = Math.round(startPercent + progress * (endPercent - startPercent));

      batchProgressFill.style.width = `${currentPercent}%`;
      batchProgressPercent.textContent = `${currentPercent}%`;

      if (currentPercent < 50) {
        batchProgressText.textContent = 'Parsing transaction rows & checking features schema...';
      } else if (currentPercent < 90) {
        batchProgressText.textContent = 'Running 56-feature XGBoost inference matrix...';
      } else {
        batchProgressText.textContent = 'Computing batch risk metrics & audit logs...';
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      } else if (callback) {
        callback();
      }
    }
    requestAnimationFrame(update);
  }

  function renderBatchResults(summary, predictions) {
    batchPredictionsData = predictions;

    // Render summary metrics
    statTotal.textContent = summary.total_transactions.toLocaleString();
    statTime.textContent = `Completed in ${summary.processing_time_seconds}s`;
    
    statHigh.textContent = summary.high_risk_count.toLocaleString();
    statHighPct.textContent = `${summary.high_risk_percentage}% of batch`;
    
    statMed.textContent = summary.medium_risk_count.toLocaleString();
    statLow.textContent = summary.low_risk_count.toLocaleString();
    statAvg.textContent = summary.average_risk_score.toFixed(4);

    batchSummaryGrid.style.display = 'grid';

    // Render Table
    renderBatchTable(batchPredictionsData);
    batchResultsCard.style.display = 'block';

    batchResultsCard.scrollIntoView({ behavior: 'smooth' });
  }

  function renderBatchTable(data) {
    batchResultsTbody.innerHTML = data.map(item => {
      const alertClass = item.alert_level ? item.alert_level.toLowerCase() : 'low';
      return `
        <tr>
          <td><strong>#${item.row_number}</strong></td>
          <td>${item.from_account}</td>
          <td>${item.to_account}</td>
          <td>$${parseFloat(item.amount_paid).toLocaleString()} ${item.payment_currency}</td>
          <td>$${parseFloat(item.amount_received).toLocaleString()} ${item.receiving_currency}</td>
          <td>${item.payment_format}</td>
          <td><strong>${item.risk_score.toFixed(4)}</strong></td>
          <td><span class="alert-badge alert-${alertClass}" style="padding: 0.2rem 0.6rem; font-size: 0.75rem;">${item.alert_level}</span></td>
          <td style="font-size: 0.8rem; max-width: 280px; white-space: normal;">${item.action_recommendation}</td>
        </tr>
      `;
    }).join('');
  }

  // Table Sorting logic
  if (thSortScore) {
    thSortScore.addEventListener('click', () => {
      sortDirectionScore = sortDirectionScore === 'desc' ? 'asc' : 'desc';
      thSortScore.querySelector('.sort-icon').textContent = sortDirectionScore === 'desc' ? '▼' : '▲';
      
      batchPredictionsData.sort((a, b) => {
        return sortDirectionScore === 'desc' ? b.risk_score - a.risk_score : a.risk_score - b.risk_score;
      });
      renderBatchTable(batchPredictionsData);
    });
  }

  if (thSortAlert) {
    thSortAlert.addEventListener('click', () => {
      sortDirectionAlert = sortDirectionAlert === 'desc' ? 'asc' : 'desc';
      thSortAlert.querySelector('.sort-icon').textContent = sortDirectionAlert === 'desc' ? '▼' : '▲';

      const rankMap = { 'High': 3, 'Medium': 2, 'Low': 1 };
      batchPredictionsData.sort((a, b) => {
        const rankA = rankMap[a.alert_level] || 0;
        const rankB = rankMap[b.alert_level] || 0;
        return sortDirectionAlert === 'desc' ? rankB - rankA : rankA - rankB;
      });
      renderBatchTable(batchPredictionsData);
    });
  }

  // Export Batch Results CSV
  if (btnExportBatchCsv) {
    btnExportBatchCsv.addEventListener('click', () => {
      if (!batchPredictionsData || batchPredictionsData.length === 0) return;

      const headers = ['Row', 'From_Account', 'To_Account', 'Amount_Paid', 'Payment_Currency', 'Amount_Received', 'Receiving_Currency', 'Payment_Format', 'Risk_Score', 'Alert_Level', 'Action_Recommendation'];
      const rows = batchPredictionsData.map(item => [
        item.row_number,
        `"${item.from_account}"`,
        `"${item.to_account}"`,
        item.amount_paid,
        `"${item.payment_currency}"`,
        item.amount_received,
        `"${item.receiving_currency}"`,
        `"${item.payment_format}"`,
        item.risk_score,
        `"${item.alert_level}"`,
        `"${item.action_recommendation.replace(/"/g, '""')}"`
      ]);

      const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `aml_batch_results_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }
});
