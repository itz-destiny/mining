const statusEl = document.getElementById('hashrate');
const balanceEl = document.getElementById('balance');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const form = document.getElementById('withdrawForm');

// Connect to SSE
const evtSource = new EventSource('/api/stream');
evtSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  statusEl.textContent = data.hashrate;
  balanceEl.textContent = data.balance;
};

startBtn.onclick = async () => {
  await fetch('/api/start', {method:'POST'});
};
stopBtn.onclick = async () => {
  await fetch('/api/stop', {method:'POST'});
};

form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const to = document.getElementById('toAddress').value;
  const amount = document.getElementById('amount').value;
  const resp = await fetch('/api/withdraw', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({currency:'BTC', amount: amount, to_address: to})});
  const j = await resp.json();
  if (j.ok) {
    alert('Withdraw requested. id=' + j.id + (j.txid ? '\nTx: ' + j.txid : '\nPending admin processing'));
  } else {
    alert('Error: ' + JSON.stringify(j));
  }
});
