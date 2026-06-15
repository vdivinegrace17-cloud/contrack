/**
 * booth_map.js — Merchant floor plan with 3-step reservation modal
 *
 * Globals (set in booth_map.html before this script):
 *   LAYOUT_DATA, APPLY_URL_BASE, CSRF_TOKEN, GRID_COLS, GRID_ROWS,
 *   PAYMENT_SETTINGS, PAYMENT_METHODS, USER_PROFILE
 */
(function () {
  'use strict';

  var canvas, ctx, cellW, cellH;
  var items = [];
  var currentStep  = 1;
  var selectedItem = null;

  var SLOT_COLORS = {
    available:   '#22c55e',
    pending:     '#f97316',
    reserved:    '#ef4444',
    unavailable: '#9ca3af',
  };
  var LANDMARK_COLORS = {
    entrance: '#0d9488', exit: '#ea580c', stage: '#7c3aed',
    restroom: '#60a5fa', food_court: '#f59e0b', emergency_exit: '#dc2626',
    info_desk: '#0f766e', parking: '#475569', custom: '#374151',
  };

  // ── Canvas ────────────────────────────────────────────────────────────────
  function initCanvas() {
    canvas = document.getElementById('fpCanvas');
    if (!canvas) { console.error('[BM] #fpCanvas not found'); return false; }
    ctx = canvas.getContext('2d');
    console.log('[BM] canvas found, GRID_COLS=' + GRID_COLS + ' GRID_ROWS=' + GRID_ROWS);
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return true;
  }

  function resizeCanvas() {
    var wrap = document.getElementById('boothMapGrid');
    if (!wrap) return;
    var w = wrap.clientWidth;
    if (w < 10) { requestAnimationFrame(resizeCanvas); return; }
    canvas.width  = w;
    canvas.height = Math.min(560, Math.max(320, w * GRID_ROWS / GRID_COLS));
    console.log('[BM] canvas sized ' + canvas.width + 'x' + canvas.height);
    cellW = canvas.width  / GRID_COLS;
    cellH = canvas.height / GRID_ROWS;
    drawAll();
  }

  // ── Drawing ────────────────────────────────────────────────────────────────
  function drawAll() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#e5e7eb';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (var r = 0; r < GRID_ROWS; r++) {
      for (var c = 0; c < GRID_COLS; c++) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(c * cellW + 0.5, r * cellH + 0.5, cellW - 1, cellH - 1);
      }
    }
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth   = 0.5;
    for (var ci = 0; ci <= GRID_COLS; ci++) { ctxLine(ci * cellW, 0, ci * cellW, canvas.height); }
    for (var ri = 0; ri <= GRID_ROWS; ri++) { ctxLine(0, ri * cellH, canvas.width, ri * cellH); }
    items.forEach(drawItem);
  }

  function drawItem(item) {
    var x = item.grid_x * cellW, y = item.grid_y * cellH;
    var w = item.grid_w * cellW, h = item.grid_h * cellH;
    var isLm = item.is_landmark;
    ctx.save();
    if (isLm) {
      ctx.fillStyle = item.color || LANDMARK_COLORS[item.landmark_type] || '#374151';
    } else {
      ctx.fillStyle = SLOT_COLORS[(item.status || 'available').toLowerCase()] || '#22c55e';
    }
    roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.18)';
    ctx.lineWidth = 1;
    roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.stroke();
    var fs = Math.min(11, Math.max(7, cellH * 0.33));
    ctx.fillStyle    = 'white';
    ctx.font         = 'bold ' + fs + 'px system-ui,sans-serif';
    ctx.textAlign    = 'center';
    ctx.textBaseline = 'middle';
    var lbl = item.label || (isLm ? capFirst(item.landmark_type || 'Landmark') : 'Slot');
    ctx.fillText(lbl, x + w / 2, y + h / 2, Math.max(4, w - 4));
    ctx.restore();
  }

  function roundRect(x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function ctxLine(x1, y1, x2, y2) {
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }

  // ── Hit testing ────────────────────────────────────────────────────────────
  function itemAt(px, py) {
    var col = Math.floor(px / cellW);
    var row = Math.floor(py / cellH);
    for (var i = items.length - 1; i >= 0; i--) {
      var it = items[i];
      if (col >= it.grid_x && col < it.grid_x + it.grid_w &&
          row >= it.grid_y && row < it.grid_y + it.grid_h) return it;
    }
    return null;
  }

  // ── Empty state ────────────────────────────────────────────────────────────
  function updateEmptyState() {
    var slots = items.filter(function (i) { return !i.is_landmark; });
    var emptyDiv = document.getElementById('boothMapEmpty');
    var gridDiv  = document.getElementById('boothMapGrid');
    if (!emptyDiv || !gridDiv) return;
    if (slots.length === 0) {
      emptyDiv.classList.remove('d-none');
      gridDiv.classList.add('d-none');
    } else {
      emptyDiv.classList.add('d-none');
      gridDiv.classList.remove('d-none');
      resizeCanvas();
    }
  }

  // ── Canvas click ───────────────────────────────────────────────────────────
  function onCanvasClick(e) {
    var r   = canvas.getBoundingClientRect();
    var hit = itemAt(e.clientX - r.left, e.clientY - r.top);
    if (hit && !hit.is_landmark && hit.status === 'AVAILABLE') {
      openReserveModal(hit);
    }
  }

  function updateCursor(e) {
    var r   = canvas.getBoundingClientRect();
    var hit = itemAt(e.clientX - r.left, e.clientY - r.top);
    canvas.style.cursor = (hit && !hit.is_landmark && hit.status === 'AVAILABLE') ? 'pointer' : 'default';
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  window.addEventListener('load', function () {
    console.log('[BM] window.load fired');
    if (!initCanvas()) return;
    items = LAYOUT_DATA.slice();
    updateEmptyState();
    drawAll();

    canvas.addEventListener('click', onCanvasClick);
    canvas.addEventListener('mousemove', updateCursor);

    setInterval(function () {
      fetch(location.href, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.items) return;
          items = data.items;
          updateEmptyState();
          drawAll();
        })
        .catch(function () {});
    }, 5000);
  });

  // ── Open modal ─────────────────────────────────────────────────────────────
  window.openReserveModal = function (item) {
    selectedItem = item;
    currentStep  = 1;
    clearErrors();

    document.getElementById('reserve_booth_id').value              = item.id;
    document.getElementById('reserve_booth_label').textContent     = item.label || 'Slot';
    document.getElementById('reserve_booth_category').textContent  = capFirst(item.category || '');
    document.getElementById('reserve_booth_type').textContent      = capFirst(item.booth_type || '');
    document.getElementById('reserve_booth_price').textContent     = '₱' + parseFloat(item.price || 0).toLocaleString('en-PH', {minimumFractionDigits: 2});

    buildPaymentOptions(item);
    buildTermsBox();
    document.getElementById('tcAgree').checked = false;
    document.getElementById('btnNext').disabled = true;

    prefillContact();

    buildPaymentMethodsList();
    document.getElementById('receipt_image_1').value = '';

    showStep(1);
    new bootstrap.Modal(document.getElementById('reserveModal')).show();
  };

  // ── Build payment option UI ────────────────────────────────────────────────
  function buildPaymentOptions(item) {
    var ps     = PAYMENT_SETTINGS || {};
    var option = ps.payment_option || 'full_only';
    var price  = parseFloat(item.price || 0);
    var section = document.getElementById('paymentOptionSection');
    var radios  = document.getElementById('paymentOptionRadios');
    var infoBox = document.getElementById('halfHalfInfo');
    var infoTxt = document.getElementById('halfHalfText');

    if (option === 'full_only') {
      section.classList.add('d-none');
      radios.innerHTML = '<input type="radio" name="payOpt" value="full" checked class="d-none">';
      infoBox.classList.add('d-none');
      return;
    }

    section.classList.remove('d-none');
    radios.innerHTML = '';

    function makeRadio(val, label) {
      var div = document.createElement('div');
      div.className = 'form-check';
      var inp = document.createElement('input');
      inp.className = 'form-check-input';
      inp.type = 'radio';
      inp.name = 'payOpt';
      inp.id   = 'payOpt_' + val;
      inp.value = val;
      inp.addEventListener('change', function () { updateHalfHalfInfo(price); });
      var lbl = document.createElement('label');
      lbl.className   = 'form-check-label';
      lbl.htmlFor     = 'payOpt_' + val;
      lbl.textContent = label;
      div.appendChild(inp);
      div.appendChild(lbl);
      radios.appendChild(div);
    }

    if (option === 'half_half') {
      makeRadio('half', '50/50 — ₱' + (price / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' now, ₱' + (price / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' later');
      radios.querySelector('input[type=radio]').checked = true;
    } else {
      makeRadio('full', 'Full Payment — ₱' + price.toLocaleString('en-PH', {minimumFractionDigits:2}));
      makeRadio('half', '50/50 — ₱' + (price / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' now, ₱' + (price / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' later');
      radios.querySelector('input[type=radio]').checked = true;
    }

    updateHalfHalfInfo(price);

    function updateHalfHalfInfo(p) {
      var sel = radios.querySelector('input[name=payOpt]:checked');
      if (sel && sel.value === 'half') {
        var days = (ps.second_payment_deadline_days || 14);
        infoBox.classList.remove('d-none');
        infoTxt.textContent = 'Pay ₱' + (p / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' now to secure your slot. The remaining ₱' + (p / 2).toLocaleString('en-PH', {minimumFractionDigits:2}) + ' is due ' + days + ' days before the event.';
      } else {
        infoBox.classList.add('d-none');
      }
    }
  }

  function buildTermsBox() {
    var tc = (PAYMENT_SETTINGS && PAYMENT_SETTINGS.terms_and_conditions) ||
      'By proceeding, you agree to the event organizer\'s terms and conditions for booth reservations.';
    document.getElementById('tcBox').textContent = tc;
  }

  function prefillContact() {
    var p = USER_PROFILE || {};
    document.getElementById('contact_name').value     = p.name     || '';
    document.getElementById('contact_phone').value    = p.phone    || '';
    document.getElementById('contact_email').value    = p.email    || '';
    document.getElementById('contact_facebook').value = p.facebook || '';
    document.getElementById('contact_products').value = '';
    document.getElementById('contact_special').value  = '';
  }

  function buildPaymentMethodsList() {
    var container = document.getElementById('paymentMethodsList');
    container.innerHTML = '';
    var methods = PAYMENT_METHODS || [];
    if (!methods.length) {
      container.innerHTML = '<p class="text-muted" style="font-size:0.85rem;">No payment methods configured. Contact the organizer directly.</p>';
      return;
    }
    methods.forEach(function (m) {
      var card = document.createElement('div');
      card.className = 'ct-card p-3 mb-2';
      var html = '<div class="d-flex align-items-start gap-3">';
      if (m.qr_code_url) {
        html += '<img src="' + m.qr_code_url + '" alt="QR" style="width:80px;height:80px;object-fit:contain;border:1px solid #dee2e6;border-radius:6px;cursor:pointer;" onclick="window.open(\'' + m.qr_code_url + '\',\'_blank\')">';
      }
      html += '<div>';
      html += '<div class="fw-bold">' + (m.name || '') + '</div>';
      if (m.account_name)   html += '<div style="font-size:0.85rem;">' + m.account_name + '</div>';
      if (m.account_number) html += '<div style="font-size:0.85rem;color:var(--ct-purple);">' + m.account_number + '</div>';
      html += '</div></div>';
      card.innerHTML = html;
      container.appendChild(card);
    });
  }

  // ── Step navigation ────────────────────────────────────────────────────────
  function showStep(n) {
    currentStep = n;
    document.getElementById('step1').classList.toggle('d-none', n !== 1);
    document.getElementById('step2').classList.toggle('d-none', n !== 2);
    document.getElementById('step3').classList.toggle('d-none', n !== 3);
    document.getElementById('btnNext').classList.toggle('d-none', n !== 1);
    document.getElementById('btnNextStep2').classList.toggle('d-none', n !== 2);
    document.getElementById('btnSubmit').classList.toggle('d-none', n !== 3);
    document.getElementById('reserveStepIndicator').textContent = 'Step ' + n + ' of 3';
    clearErrors();
  }

  window.onTcChange = function () {
    document.getElementById('btnNext').disabled = !document.getElementById('tcAgree').checked;
  };

  window.goNext = function () {
    if (!document.getElementById('tcAgree').checked) return;
    showStep(2);
  };

  window.goToStep3 = function () {
    var name  = document.getElementById('contact_name').value.trim();
    var phone = document.getElementById('contact_phone').value.trim();
    var email = document.getElementById('contact_email').value.trim();
    if (!name)  { showError('Full name is required.'); return; }
    if (!phone) { showError('Phone number is required.'); return; }
    if (!email) { showError('Email address is required.'); return; }
    showStep(3);
  };

  window.goBack = function () {
    if (currentStep > 1) showStep(currentStep - 1);
  };

  // ── Submit ─────────────────────────────────────────────────────────────────
  window.submitReservation = function () {
    clearErrors();

    var receipt = document.getElementById('receipt_image_1');
    if (!receipt.files || !receipt.files[0]) {
      showError('Please upload your payment receipt.');
      return;
    }
    if (receipt.files[0].size > 5 * 1024 * 1024) {
      showError('File is too large. Maximum size is 5MB.');
      return;
    }

    var boothId = document.getElementById('reserve_booth_id').value;
    var selOpt  = document.querySelector('input[name="payOpt"]:checked');
    var payOpt  = selOpt ? selOpt.value : 'full';

    var fd = new FormData();
    fd.append('payment_option',      payOpt);
    fd.append('merchant_name',       document.getElementById('contact_name').value.trim());
    fd.append('merchant_phone',      document.getElementById('contact_phone').value.trim());
    fd.append('merchant_email',      document.getElementById('contact_email').value.trim());
    fd.append('merchant_facebook',   document.getElementById('contact_facebook').value.trim());
    fd.append('product_description', document.getElementById('contact_products').value.trim());
    fd.append('special_requests',    document.getElementById('contact_special').value.trim());
    fd.append('receipt_image_1',     receipt.files[0]);
    fd.append('csrfmiddlewaretoken', CSRF_TOKEN);

    var btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Submitting…';

    fetch(APPLY_URL_BASE + boothId + '/', {
      method:  'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body:    fd,
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Submit Reservation';
      if (data.success) {
        bootstrap.Modal.getInstance(document.getElementById('reserveModal')).hide();
        var it = items.find(function (i) { return String(i.id) === String(boothId); });
        if (it) { it.status = 'PENDING'; drawAll(); }
        showToast('Reservation submitted! Awaiting organizer review.', 'success');
      } else {
        showError(data.error || 'Failed to submit. Please try again.');
      }
    })
    .catch(function () {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Submit Reservation';
      showError('Network error. Please check your connection and try again.');
    });
  };

  // ── Helpers ────────────────────────────────────────────────────────────────
  function showError(msg) {
    var errDiv = document.getElementById('reserveError');
    errDiv.textContent = msg;
    errDiv.classList.remove('d-none');
  }

  function clearErrors() {
    document.getElementById('reserveError').classList.add('d-none');
  }

  function capFirst(s) {
    return String(s || '').replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  // Global toast used by both this file and base.html's showToast if present
  window.showToast = window.showToast || function (msg, type) {
    var cls = 'alert-' + (type || 'success');
    var t   = document.createElement('div');
    t.className = 'alert ' + cls + ' position-fixed bottom-0 end-0 m-3 shadow';
    t.style.zIndex   = '9999';
    t.style.maxWidth = '360px';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 4000);
  };

})();
