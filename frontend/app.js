// Professional Mining Dashboard - Main Application Logic
document.addEventListener('DOMContentLoaded', function() {
  const statusEl = document.getElementById('hashrate');
  const balanceEl = document.getElementById('balance');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const form = document.getElementById('withdrawForm');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  if (!statusEl || !balanceEl || !startBtn || !stopBtn || !form) {
    console.error('Required elements not found');
    return;
  }

  // Update mining status indicator
  function updateMiningStatus(running) {
    if (statusDot && statusText) {
      if (running) {
        statusDot.classList.add('active');
        statusText.textContent = 'Mining Active';
      } else {
        statusDot.classList.remove('active');
        statusText.textContent = 'Mining Stopped';
      }
    }
  }

  // Connect to SSE
  let evtSource = null;
  
  function connectSSE() {
    if (evtSource) {
      evtSource.close();
    }
    
    evtSource = new EventSource('/api/stream');
    
    evtSource.onopen = () => {
      console.log('SSE connection opened');
    };
    
    evtSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        console.log('SSE data received:', data);
        
        // Update display values
        if (statusEl) {
          const hashrate = data.hashrate || 0;
          // Format large numbers (convert to Th/s if > 1 trillion)
          if (hashrate >= 1000000000000) {
            const th = hashrate / 1000000000000;
            statusEl.textContent = (th % 1 === 0 ? th.toFixed(0) : th.toFixed(2)) + 'Th/s';
          } else if (hashrate >= 1000000000) {
            const gh = hashrate / 1000000000;
            statusEl.textContent = (gh % 1 === 0 ? gh.toFixed(0) : gh.toFixed(2)) + 'Gh/s';
          } else if (hashrate >= 1000000) {
            const mh = hashrate / 1000000;
            statusEl.textContent = (mh % 1 === 0 ? mh.toFixed(0) : mh.toFixed(2)) + 'Mh/s';
          } else if (hashrate >= 1000) {
            const kh = hashrate / 1000;
            statusEl.textContent = (kh % 1 === 0 ? kh.toFixed(0) : kh.toFixed(2)) + 'Kh/s';
          } else {
            statusEl.textContent = hashrate.toLocaleString() + 'H/s';
          }
        }
        if (balanceEl) {
          const balance = data.balance || 0;
          balanceEl.textContent = balance.toFixed(8);
        }
        
        // Update mining status
        updateMiningStatus(data.running || false);
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };
    
    evtSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      // Try to reconnect after 3 seconds
      setTimeout(() => {
        if (evtSource && evtSource.readyState === EventSource.CLOSED) {
          console.log('Attempting to reconnect SSE...');
          connectSSE();
        }
      }, 3000);
    };
  }
  
  // Initial connection
  connectSSE();

  // Start Mining
  startBtn.onclick = async () => {
    try {
      startBtn.disabled = true;
      startBtn.innerHTML = '<span class="spinner"></span> Starting...';
      
      const resp = await fetch('/api/start', {method:'POST'});
      const data = await resp.json();
      
      if (data.ok) {
        console.log('Mining started');
        updateMiningStatus(true);
        startBtn.innerHTML = '<span>▶</span> Start Mining';
      } else {
        showAlert('Error: ' + (data.error || 'Failed to start mining'), 'error');
        startBtn.innerHTML = '<span>▶</span> Start Mining';
      }
    } catch (err) {
      console.error('Error starting mining:', err);
      showAlert('Error starting mining: ' + err.message, 'error');
      startBtn.innerHTML = '<span>▶</span> Start Mining';
    } finally {
      startBtn.disabled = false;
    }
  };

  // Stop Mining
  stopBtn.onclick = async () => {
    try {
      stopBtn.disabled = true;
      stopBtn.innerHTML = '<span class="spinner"></span> Stopping...';
      
      const resp = await fetch('/api/stop', {method:'POST'});
      const data = await resp.json();
      
      if (data.ok) {
        console.log('Mining stopped');
        updateMiningStatus(false);
        stopBtn.innerHTML = '<span>⏹</span> Stop Mining';
      } else {
        showAlert('Error: ' + (data.error || 'Failed to stop mining'), 'error');
        stopBtn.innerHTML = '<span>⏹</span> Stop Mining';
      }
    } catch (err) {
      console.error('Error stopping mining:', err);
      showAlert('Error stopping mining: ' + err.message, 'error');
      stopBtn.innerHTML = '<span>⏹</span> Stop Mining';
    } finally {
      stopBtn.disabled = false;
    }
  };

  // Withdraw Form
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const to = document.getElementById('toAddress').value.trim();
    const amount = parseFloat(document.getElementById('amount').value);
    
    // Validation
    if (!to || !amount || amount <= 0) {
      showAlert('Please enter a valid address and amount', 'error');
      return;
    }
    
    if (amount < 0.00000001) {
      showAlert('Minimum withdrawal amount is 0.00000001 BTC', 'error');
      return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
      
      const resp = await fetch('/api/withdraw', {
        method:'POST', 
        headers:{'Content-Type':'application/json'}, 
        body: JSON.stringify({currency:'BTC', amount: amount, to_address: to})
      });
      
      const j = await resp.json();
      
      if (j.ok) {
        const message = j.txid 
          ? `Withdrawal successful! Transaction ID: ${j.txid.substring(0, 16)}...`
          : `Withdrawal requested. ID: ${j.id.substring(0, 8)}... (Pending admin processing)`;
        showAlert(message, 'success');
        form.reset();
      } else {
        showAlert('Error: ' + (j.error || 'Failed to process withdrawal'), 'error');
      }
    } catch (err) {
      console.error('Error submitting withdrawal:', err);
      showAlert('Error submitting withdrawal: ' + err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });

  // Alert system
  function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existing = document.querySelector('.alert');
    if (existing) {
      existing.remove();
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
      <span>${getAlertIcon(type)}</span>
      <span>${message}</span>
      <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; font-size: 20px; cursor: pointer; opacity: 0.7;">&times;</button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alert.parentElement) {
        alert.remove();
      }
    }, 5000);
  }
  
  function getAlertIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }
  
  // Make functions globally available (but don't override if already set)
  if (!window.updateMiningStatus) {
    window.updateMiningStatus = updateMiningStatus;
  }
  window.showAlert = showAlert;
});
