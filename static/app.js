const STATUS_LABELS = {
  draft: 'Черновик',
  qualified: 'Квалифицированный',
  ready_for_publication: 'Готов к публикации',
  sent_to_yulia: 'Отправлен Юлии',
  archived: 'Архив',
};

const CHANNEL_LABELS = {
  telegram: '✈ Telegram',
  whatsapp: '💬 WhatsApp',
  max: '⚡ MAX',
};

let allLots = [];

async function fetchDashboard() {
  try {
    const resp = await fetch('/api/dashboard/');
    const data = await resp.json();
    updateStats(data.stats);
    allLots = data.recent_lots || [];
    renderLots(allLots);
    renderPending(data.pending_replies || []);
    document.getElementById('last-update').textContent =
      'Обновлено: ' + new Date().toLocaleTimeString('ru-RU');
  } catch (e) {
    console.error('Ошибка загрузки дашборда:', e);
  }
}

function updateStats(stats) {
  document.getElementById('stat-contacts-today').textContent = stats.new_contacts_today ?? '—';
  document.getElementById('stat-contacts-total').textContent = stats.total_contacts ?? '—';
  document.getElementById('stat-lots-total').textContent = stats.total_lots ?? '—';
  document.getElementById('stat-lots-draft').textContent = stats.lots_draft ?? '—';
  document.getElementById('stat-lots-qualified').textContent = stats.lots_qualified ?? '—';
  document.getElementById('stat-lots-ready').textContent = stats.lots_ready ?? '—';
  document.getElementById('stat-lots-no-indicators').textContent = stats.lots_without_indicators ?? '—';
  document.getElementById('stat-lots-sent').textContent = stats.lots_sent_to_yulia ?? '—';
}

function filterLots() {
  const status = document.getElementById('filter-status').value;
  const filtered = status ? allLots.filter(l => l.status === status) : allLots;
  renderLots(filtered);
}

function renderLots(lots) {
  const tbody = document.getElementById('lots-tbody');
  if (!lots.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty">Лотов пока нет</td></tr>';
    return;
  }
  tbody.innerHTML = lots.map(lot => {
    const culture = lot.culture
      ? (lot.quality_type ? `${lot.culture} (${lot.quality_type})` : lot.culture)
      : '<span style="color:#a0aec0">—</span>';
    const volume = lot.volume ? `${lot.volume} т` : '—';
    const region = lot.region || '—';
    const contact = lot.contact
      ? `<strong>${lot.contact.name || '—'}</strong>${lot.contact.phone ? '<br><small>' + lot.contact.phone + '</small>' : ''}`
      : '—';
    const channel = lot.contact?.last_channel
      ? `<span class="channel ch-${lot.contact.last_channel}">${CHANNEL_LABELS[lot.contact.last_channel] || lot.contact.last_channel}</span>`
      : '—';
    const status = lot.status
      ? `<span class="status status-${lot.status}">${STATUS_LABELS[lot.status] || lot.status}</span>`
      : '—';
    const date = lot.created_at
      ? new Date(lot.created_at).toLocaleDateString('ru-RU', {day:'2-digit', month:'2-digit', year:'2-digit'})
      : '—';
    return `<tr>
      <td><small style="color:#a0aec0">#${lot.id}</small></td>
      <td>${culture}</td>
      <td>${volume}</td>
      <td>${region}</td>
      <td>${contact}</td>
      <td>${channel}</td>
      <td>${status}</td>
      <td style="white-space:nowrap">${date}</td>
      <td><button class="link-btn" onclick="openLot(${lot.id})">Подробнее</button></td>
    </tr>`;
  }).join('');
}

function renderPending(contacts) {
  const section = document.getElementById('pending-section');
  const list = document.getElementById('pending-list');
  const badge = document.getElementById('pending-count');
  if (!contacts.length) {
    section.style.display = 'none';
    return;
  }
  section.style.display = '';
  badge.textContent = contacts.length;
  list.innerHTML = contacts.map(c => {
    const ch = c.last_channel ? `<span class="channel ch-${c.last_channel}">${CHANNEL_LABELS[c.last_channel] || c.last_channel}</span>` : '';
    return `<li>👤 <strong>${c.name || 'Без имени'}</strong>${c.phone ? ' · ' + c.phone : ''} ${ch}</li>`;
  }).join('');
}

async function openLot(lotId) {
  try {
    const [lotResp, adResp] = await Promise.all([
      fetch(`/api/lots/${lotId}`),
      fetch(`/api/lots/${lotId}/ad-text`)
    ]);
    const lot = await lotResp.json();
    const adData = await adResp.json();

    const fields = [
      ['Культура', lot.culture],
      ['Тип качества', lot.quality_type],
      ['Объём', lot.volume ? `${lot.volume} т` : null],
      ['Регион', lot.region],
      ['Район', lot.district],
      ['Влажность', lot.humidity != null ? `${lot.humidity}%` : null],
      ['Сорность', lot.weed != null ? `${lot.weed}%` : null],
      ['Зерн. примесь', lot.grain_impurity != null ? `${lot.grain_impurity}%` : null],
      ['Натура', lot.nature != null ? `${lot.nature} г/л` : null],
      ['Масличность', lot.oil_content != null ? `${lot.oil_content}%` : null],
      ['Протеин', lot.protein != null ? `${lot.protein}%` : null],
      ['Кислотное число', lot.acid_value],
      ['НДС', lot.vat_type],
      ['Цена', lot.price ? `${lot.price} руб/т` : null],
      ['Статус', STATUS_LABELS[lot.status] || lot.status],
    ];

    const fieldsHtml = fields
      .filter(([, v]) => v != null)
      .map(([label, value]) =>
        `<div class="modal-field"><span class="label">${label}</span><span class="value">${value}</span></div>`
      ).join('');

    document.getElementById('modal-title').textContent = `Лот #${lot.id}`;
    document.getElementById('modal-body').innerHTML = fieldsHtml +
      `<h3 style="margin:16px 0 8px;font-size:.9rem;color:#718096">📢 Текст объявления</h3>
       <div class="modal-ad">${adData.ad_text || '—'}</div>`;
    document.getElementById('modal-overlay').style.display = 'flex';
  } catch (e) {
    console.error('Ошибка загрузки лота:', e);
  }
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
}

document.getElementById('manual-submit').addEventListener('click', async () => {
  const channel = document.getElementById('manual-channel').value;
  const senderId = document.getElementById('manual-sender-id').value.trim();
  const name = document.getElementById('manual-name').value.trim();
  const text = document.getElementById('manual-text').value.trim();

  if (!senderId || !text) {
    alert('Заполните ID/телефон и текст сообщения');
    return;
  }

  const btn = document.getElementById('manual-submit');
  btn.disabled = true;
  btn.textContent = 'Отправка...';

  try {
    const resp = await fetch('/api/messages/manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        channel,
        sender_id: senderId,
        name: name || null,
        phone: senderId.startsWith('+') ? senderId : null,
        text,
      }),
    });
    const data = await resp.json();
    const replyBox = document.getElementById('manual-reply');
    replyBox.style.display = 'block';
    replyBox.textContent = '🤖 ' + (data.reply || 'Сообщение обработано');
    document.getElementById('manual-text').value = '';
    await fetchDashboard();
  } catch (e) {
    alert('Ошибка: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Отправить';
  }
});

fetchDashboard();
setInterval(fetchDashboard, 30000);
