/**
 * grid_builder.js — Interactive floor plan builder (Canvas 2D)
 *
 * Globals required (set in grid_builder.html before this script):
 *   LAYOUT_DATA, SAVE_URL, DELETE_URL, CLEAR_URL, POLL_URL, CSRF_TOKEN, FP_COLS, FP_ROWS
 */
(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  var canvas, ctx, cellW, cellH;
  var items      = [];
  var undoStack  = [];
  var activeTool = 'pointer';   // 'pointer' | {kind, slotType?, landmarkType?}
  var unsaved    = false;
  var tempIdCtr  = 0;
  var editingTempId    = null;
  var contextTempId    = null;
  var reservedClickItem = null;  // booth clicked while reserved/pending — show info panel

  // Drag existing item
  var isDragging    = false;
  var dragItem      = null;
  var dragMoved     = false;
  var dragOffsetCol = 0, dragOffsetRow = 0;
  var dragCurCol    = 0, dragCurRow    = 0;

  // Draw new item
  var isDrawing   = false;
  var drawStartC  = 0, drawStartR = 0;
  var drawEndC    = 0, drawEndR   = 0;

  // ── Item + landmark colour maps ────────────────────────────────────────────
  var SLOT_COLORS = {
    available:   '#22c55e',
    pending:     '#f97316',
    reserved:    '#ef4444',
    unavailable: '#9ca3af',
  };
  var LANDMARK_COLORS = {
    entrance:       '#0d9488',
    exit:           '#ea580c',
    stage:          '#7c3aed',
    restroom:       '#60a5fa',
    food_court:     '#f59e0b',
    emergency_exit: '#dc2626',
    info_desk:      '#0f766e',
    parking:        '#475569',
    custom:         '#374151',
  };

  // ── Bootstrap modal helper ─────────────────────────────────────────────────
  function getModal() {
    return bootstrap.Modal.getOrCreateInstance(document.getElementById('fpItemModal'));
  }

  // ── Canvas init + resize ───────────────────────────────────────────────────
  function initCanvas() {
    canvas = document.getElementById('fpCanvas');
    if (!canvas) { console.error('[FP] #fpCanvas not found'); return; }
    ctx = canvas.getContext('2d');
    console.log('[FP] canvas found, FP_COLS=' + FP_COLS + ' FP_ROWS=' + FP_ROWS);
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
  }

  function resizeCanvas() {
    var wrap = document.getElementById('fpCanvasWrap');
    if (!wrap) return;
    var w = wrap.clientWidth;
    if (w < 10) {
      // Layout not computed yet — defer one animation frame
      requestAnimationFrame(resizeCanvas);
      return;
    }
    canvas.width  = w;
    canvas.height = Math.min(620, Math.max(360, w * FP_ROWS / FP_COLS));
    console.log('[FP] canvas sized ' + canvas.width + 'x' + canvas.height);
    recalcCells();
    drawGrid();
  }

  function recalcCells() {
    cellW = canvas.width  / FP_COLS;
    cellH = canvas.height / FP_ROWS;
  }

  // ── Drawing ────────────────────────────────────────────────────────────────
  function drawGrid() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Grey background
    ctx.fillStyle = '#e5e7eb';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // White cells
    for (var r = 0; r < FP_ROWS; r++) {
      for (var c = 0; c < FP_COLS; c++) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(c * cellW + 0.5, r * cellH + 0.5, cellW - 1, cellH - 1);
      }
    }

    // Grid lines
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth   = 0.5;
    for (var ci = 0; ci <= FP_COLS; ci++) { ctxLine(ci * cellW, 0, ci * cellW, canvas.height); }
    for (var ri = 0; ri <= FP_ROWS; ri++) { ctxLine(0, ri * cellH, canvas.width, ri * cellH); }

    // Placed items (except item being dragged)
    items.forEach(function (it) {
      if (!isDragging || !dragItem || it.tempId !== dragItem.tempId) {
        drawItem(it, false);
      }
    });

    // Draw-new preview rectangle
    if (isDrawing) { drawPreview(); }

    // Dragged item rendered on top (ghost)
    if (isDragging && dragItem) {
      var ghost = shallowCopy(dragItem);
      ghost.grid_x = Math.max(0, Math.min(FP_COLS - dragItem.grid_w, dragCurCol - dragOffsetCol));
      ghost.grid_y = Math.max(0, Math.min(FP_ROWS - dragItem.grid_h, dragCurRow - dragOffsetRow));
      drawItem(ghost, true);
    }
  }

  function drawItem(item, ghost) {
    var x = item.grid_x * cellW, y = item.grid_y * cellH;
    var w = item.grid_w * cellW, h = item.grid_h * cellH;
    var isLm = item.isLandmark || item.is_landmark;

    ctx.save();
    if (ghost) ctx.globalAlpha = 0.60;

    // Fill colour
    if (isLm) {
      ctx.fillStyle = item.color || LANDMARK_COLORS[item.landmarkType || item.landmark_type] || '#374151';
    } else {
      ctx.fillStyle = SLOT_COLORS[(item.status || 'available').toLowerCase()] || '#22c55e';
    }
    roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.fill();

    // Border
    ctx.strokeStyle = 'rgba(0,0,0,0.18)';
    ctx.lineWidth = 1;
    roundRect(x + 1, y + 1, w - 2, h - 2, 3);
    ctx.stroke();

    // Label text
    var fs = Math.min(11, Math.max(7, cellH * 0.33));
    var statusLower = (item.status || '').toLowerCase();
    var hasSubLabel = !isLm && (statusLower === 'reserved' || statusLower === 'pending');
    var labelY = hasSubLabel ? y + h / 2 - fs * 0.6 : y + h / 2;
    ctx.fillStyle     = isLm ? 'white' : (statusLower === 'pending' ? '#1a1a1a' : 'white');
    ctx.font          = 'bold ' + fs + 'px system-ui,sans-serif';
    ctx.textAlign     = 'center';
    ctx.textBaseline  = 'middle';
    var lbl = item.label ||
      (isLm ? capFirst(item.landmarkType || item.landmark_type || 'Custom') : 'Slot');
    ctx.fillText(lbl, x + w / 2, labelY, Math.max(4, w - 4));

    // Secondary status label for reserved/pending slots
    if (hasSubLabel) {
      var subFs = Math.max(6, Math.min(cellW, cellH) * 0.22);
      ctx.font      = subFs + 'px sans-serif';
      ctx.fillStyle = statusLower === 'reserved' ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.65)';
      ctx.fillText(
        statusLower === 'reserved' ? 'RESERVED' : 'PENDING',
        x + w / 2,
        y + h / 2 + cellH * 0.22,
        Math.max(4, w - 4)
      );
    }

    ctx.restore();
  }

  function drawPreview() {
    var x = Math.min(drawStartC, drawEndC) * cellW;
    var y = Math.min(drawStartR, drawEndR) * cellH;
    var w = (Math.abs(drawEndC - drawStartC) + 1) * cellW;
    var h = (Math.abs(drawEndR - drawStartR) + 1) * cellH;
    ctx.save();
    ctx.fillStyle   = 'rgba(59,130,246,0.22)'; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);
    ctx.restore();
  }

  function roundRect(x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y,     x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x,     y + h, r);
    ctx.arcTo(x,     y + h, x,     y,     r);
    ctx.arcTo(x,     y,     x + w, y,     r);
    ctx.closePath();
  }

  function ctxLine(x1, y1, x2, y2) {
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  }

  // ── Tool selection ─────────────────────────────────────────────────────────
  window.selectTool = function (kind, typeVal) {
    document.querySelectorAll('.fp-tool').forEach(function (b) {
      b.classList.remove('fp-tool-active');
    });
    var id = kind === 'pointer' ? 'tool-pointer' : 'tool-' + (typeVal || '').toLowerCase();
    var btn = document.getElementById(id);
    if (btn) btn.classList.add('fp-tool-active');

    if (kind === 'pointer') {
      activeTool = 'pointer';
      if (canvas) canvas.style.cursor = 'default';
    } else {
      activeTool = { kind: kind, slotType: kind === 'slot' ? typeVal : null, landmarkType: kind === 'landmark' ? typeVal : null };
      if (canvas) canvas.style.cursor = 'crosshair';
    }
  };

  // ── Mouse coordinates → grid ───────────────────────────────────────────────
  function pixelToGrid(e) {
    var r = canvas.getBoundingClientRect();
    return {
      col: Math.max(0, Math.min(FP_COLS - 1, Math.floor((e.clientX - r.left) / cellW))),
      row: Math.max(0, Math.min(FP_ROWS - 1, Math.floor((e.clientY - r.top)  / cellH))),
    };
  }

  // ── Hit testing ────────────────────────────────────────────────────────────
  function itemAt(col, row) {
    for (var i = items.length - 1; i >= 0; i--) {
      var it = items[i];
      if (col >= it.grid_x && col < it.grid_x + it.grid_w &&
          row >= it.grid_y && row < it.grid_y + it.grid_h) return it;
    }
    return null;
  }

  // ── Collision detection ────────────────────────────────────────────────────
  function isOccupied(x, y, w, h, excludeTempId) {
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (it.tempId === excludeTempId) continue;
      if (x < it.grid_x + it.grid_w && x + w > it.grid_x &&
          y < it.grid_y + it.grid_h && y + h > it.grid_y) return true;
    }
    return false;
  }

  function flashOccupied(x, y, w, h) {
    if (!ctx) return;
    ctx.save();
    ctx.fillStyle = 'rgba(239,68,68,0.45)';
    ctx.fillRect(x * cellW, y * cellH, w * cellW, h * cellH);
    ctx.restore();
    setTimeout(drawGrid, 450);
  }

  // ── Mouse event handlers ───────────────────────────────────────────────────
  function attachCanvasEvents() {
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseup',   onMouseUp);
    canvas.addEventListener('mouseleave', function () {
      reservedClickItem = null;
      if (isDragging || isDrawing) {
        isDragging = false; isDrawing = false; dragItem = null;
        drawGrid();
      }
    });
    canvas.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      var g = pixelToGrid(e);
      var hit = itemAt(g.col, g.row);
      if (hit) showContextMenu(e, hit.tempId);
    });
  }

  function isProtected(item) {
    var st = (item.status || '').toLowerCase();
    return !item.isLandmark && !item.is_landmark && (st === 'reserved' || st === 'pending');
  }

  function onMouseDown(e) {
    if (e.button !== 0) return;
    var g = pixelToGrid(e);
    if (activeTool === 'pointer') {
      var hit = itemAt(g.col, g.row);
      if (hit) {
        if (isProtected(hit)) {
          reservedClickItem = hit;
          return;
        }
        isDragging    = true;
        dragMoved     = false;
        dragItem      = hit;
        dragOffsetCol = g.col - hit.grid_x;
        dragOffsetRow = g.row - hit.grid_y;
        dragCurCol    = g.col;
        dragCurRow    = g.row;
        canvas.style.cursor = 'grabbing';
      }
    } else {
      isDrawing   = true;
      drawStartC  = drawEndC = g.col;
      drawStartR  = drawEndR = g.row;
    }
  }

  function onMouseMove(e) {
    var g = pixelToGrid(e);
    if (isDragging) {
      dragMoved  = true;
      dragCurCol = g.col;
      dragCurRow = g.row;
      drawGrid();
      return;
    }
    if (isDrawing) {
      drawEndC = g.col;
      drawEndR = g.row;
      drawGrid();
      return;
    }
    // Cursor hint (no drag in progress)
    if (activeTool === 'pointer') {
      var hovered = itemAt(g.col, g.row);
      if (!hovered) {
        canvas.style.cursor = 'default';
      } else if (isProtected(hovered)) {
        canvas.style.cursor = 'pointer';
      } else {
        canvas.style.cursor = 'grab';
      }
    } else {
      canvas.style.cursor = 'crosshair';
    }
  }

  function onMouseUp(e) {
    if (e.button !== 0) return;

    if (reservedClickItem) {
      var rItem = reservedClickItem;
      reservedClickItem = null;
      openReservedInfo(rItem);
      return;
    }

    if (isDragging && dragItem) {
      var captured = dragItem;   // capture before clearing
      var newX = Math.max(0, Math.min(FP_COLS - captured.grid_w, dragCurCol - dragOffsetCol));
      var newY = Math.max(0, Math.min(FP_ROWS - captured.grid_h, dragCurRow - dragOffsetRow));

      isDragging = false;
      dragItem   = null;
      canvas.style.cursor = 'default';

      if (!dragMoved) {
        // Click without movement → open edit
        drawGrid();
        openEditModal(captured);
        return;
      }
      if (!isOccupied(newX, newY, captured.grid_w, captured.grid_h, captured.tempId)) {
        pushUndo();
        captured.grid_x = newX;
        captured.grid_y = newY;
        markUnsaved();
      } else {
        flashOccupied(newX, newY, captured.grid_w, captured.grid_h);
      }
      drawGrid();
      return;
    }

    if (isDrawing) {
      isDrawing  = false;
      var x = Math.min(drawStartC, drawEndC);
      var y = Math.min(drawStartR, drawEndR);
      var w = Math.abs(drawEndC - drawStartC) + 1;
      var h = Math.abs(drawEndR - drawStartR) + 1;
      if (isOccupied(x, y, w, h, null)) {
        flashOccupied(x, y, w, h);
        drawGrid();
        return;
      }
      openCreateModal(x, y, w, h);
      drawGrid();
    }
  }

  // ── Keyboard shortcuts ─────────────────────────────────────────────────────
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { selectTool('pointer', null); }
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undoLast(); }
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveLayout(); }
  });

  // ── Open create modal ──────────────────────────────────────────────────────
  function openCreateModal(x, y, w, h) {
    var isLm = activeTool !== 'pointer' && activeTool.kind === 'landmark';
    editingTempId = null;
    document.getElementById('fpItemModalLabel').textContent = isLm ? 'Add Landmark' : 'Add Slot';
    document.getElementById('fpItemError').classList.add('d-none');
    document.getElementById('fpDeleteBtn').classList.add('d-none');
    document.getElementById('fpSlotFields').classList.toggle('d-none', isLm);
    document.getElementById('fpLandmarkFields').classList.toggle('d-none', !isLm);

    if (!isLm) {
      document.getElementById('fp_label').value       = '';
      document.getElementById('fp_slot_type').value   = activeTool.slotType || 'BOOTH';
      document.getElementById('fp_category').value    = 'OTHER';
      document.getElementById('fp_price').value       = '0';
      document.getElementById('fp_status').value      = 'AVAILABLE';
      document.getElementById('fp_description').value = '';
      document.getElementById('fp_size_display').value = w + '×' + h + ' cells';
    } else {
      var lt = activeTool.landmarkType || 'custom';
      document.getElementById('fp_lm_label').value = capFirst(lt.replace(/_/g, ' '));
      document.getElementById('fp_lm_type').value  = lt;
      document.getElementById('fp_lm_color').value = '#374151';
      document.getElementById('fp_lm_size_display').value = w + '×' + h + ' cells';
      document.getElementById('fp_lm_color_row').classList.toggle('d-none', lt !== 'custom');
    }

    canvas._pendingCreate = { x: x, y: y, w: w, h: h };
    getModal().show();
  }

  // ── Open edit modal ────────────────────────────────────────────────────────
  function openEditModal(item) {
    if (isProtected(item)) { openReservedInfo(item); return; }
    editingTempId = item.tempId;
    var isLm = item.isLandmark || item.is_landmark;
    document.getElementById('fpItemModalLabel').textContent = isLm ? 'Edit Landmark' : 'Edit Slot';
    document.getElementById('fpItemError').classList.add('d-none');
    document.getElementById('fpDeleteBtn').classList.remove('d-none');
    document.getElementById('fpSlotFields').classList.toggle('d-none', isLm);
    document.getElementById('fpLandmarkFields').classList.toggle('d-none', !isLm);

    if (!isLm) {
      document.getElementById('fp_label').value       = item.label || '';
      document.getElementById('fp_slot_type').value   = item.slotType || item.booth_type || 'BOOTH';
      document.getElementById('fp_category').value    = item.category || 'OTHER';
      document.getElementById('fp_price').value       = item.price != null ? item.price : '0';
      document.getElementById('fp_status').value      = item.status || 'AVAILABLE';
      document.getElementById('fp_description').value = item.description || '';
      document.getElementById('fp_size_display').value = item.grid_w + '×' + item.grid_h + ' cells';
    } else {
      var lt = item.landmarkType || item.landmark_type || 'custom';
      document.getElementById('fp_lm_label').value = item.label || '';
      document.getElementById('fp_lm_type').value  = lt;
      document.getElementById('fp_lm_color').value = item.color || '#374151';
      document.getElementById('fp_lm_size_display').value = item.grid_w + '×' + item.grid_h + ' cells';
      document.getElementById('fp_lm_color_row').classList.toggle('d-none', lt !== 'custom');
    }
    getModal().show();
  }

  window.onLmTypeChange = function () {
    var v = document.getElementById('fp_lm_type').value;
    document.getElementById('fp_lm_color_row').classList.toggle('d-none', v !== 'custom');
  };

  // ── Save modal item ────────────────────────────────────────────────────────
  window.saveModalItem = function () {
    var errDiv = document.getElementById('fpItemError');
    errDiv.classList.add('d-none');

    var isLm = !document.getElementById('fpLandmarkFields').classList.contains('d-none');

    if (editingTempId !== null) {
      var existing = items.find(function (i) { return i.tempId === editingTempId; });
      if (!existing) { getModal().hide(); return; }
      pushUndo();
      if (!isLm) {
        existing.label       = document.getElementById('fp_label').value.trim();
        existing.slotType    = document.getElementById('fp_slot_type').value;
        existing.booth_type  = existing.slotType;
        existing.category    = document.getElementById('fp_category').value;
        existing.price       = parseFloat(document.getElementById('fp_price').value) || 0;
        existing.status      = document.getElementById('fp_status').value;
        existing.description = document.getElementById('fp_description').value.trim();
      } else {
        existing.label        = document.getElementById('fp_lm_label').value.trim();
        existing.landmarkType = document.getElementById('fp_lm_type').value;
        existing.landmark_type = existing.landmarkType;
        existing.color        = existing.landmarkType === 'custom'
          ? document.getElementById('fp_lm_color').value : '';
      }
      markUnsaved();
      drawGrid();
      getModal().hide();
      return;
    }

    // New item
    var pending = canvas._pendingCreate;
    if (!pending) return;
    pushUndo();

    var newItem = {
      tempId:       ++tempIdCtr,
      id:           null,
      booth_number: null,
      isLandmark:   isLm,
      is_landmark:  isLm,
      grid_x: pending.x, grid_y: pending.y,
      grid_w: pending.w, grid_h: pending.h,
    };

    if (!isLm) {
      newItem.label        = document.getElementById('fp_label').value.trim();
      newItem.slotType     = document.getElementById('fp_slot_type').value;
      newItem.booth_type   = newItem.slotType;
      newItem.category     = document.getElementById('fp_category').value;
      newItem.price        = parseFloat(document.getElementById('fp_price').value) || 0;
      newItem.status       = document.getElementById('fp_status').value;
      newItem.description  = document.getElementById('fp_description').value.trim();
      newItem.landmarkType = '';
      newItem.landmark_type = '';
      newItem.color        = '';
    } else {
      newItem.label         = document.getElementById('fp_lm_label').value.trim();
      newItem.landmarkType  = document.getElementById('fp_lm_type').value;
      newItem.landmark_type = newItem.landmarkType;
      newItem.color         = newItem.landmarkType === 'custom'
        ? document.getElementById('fp_lm_color').value : '';
      newItem.slotType      = 'BOOTH';
      newItem.booth_type    = 'BOOTH';
      newItem.category      = 'OTHER';
      newItem.price         = 0;
      newItem.status        = 'AVAILABLE';
      newItem.description   = '';
    }

    items.push(newItem);
    markUnsaved();
    drawGrid();
    getModal().hide();
  };

  // ── Delete item ────────────────────────────────────────────────────────────
  window.deleteCurrentItem = function () {
    if (editingTempId === null) return;
    var item = items.find(function (i) { return i.tempId === editingTempId; });
    if (!item) return;
    if (isProtected(item)) {
      document.getElementById('fpItemError').textContent = 'This booth has an active reservation and cannot be deleted. Manage it through Reservations.';
      document.getElementById('fpItemError').classList.remove('d-none');
      return;
    }
    pushUndo();
    items = items.filter(function (i) { return i.tempId !== editingTempId; });
    markUnsaved();
    drawGrid();
    getModal().hide();
  };

  // ── Reserved / Pending booth info panel ───────────────────────────────────
  function openReservedInfo(item) {
    var statusLower = (item.status || '').toLowerCase();
    var modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('fpReservedModal'));

    // Booth header
    document.getElementById('ri_header_label').textContent = statusLower === 'pending' ? 'Booth Pending Reservation' : 'Booth Reserved';
    document.getElementById('ri_booth_label').textContent  = item.label || 'Booth';
    document.getElementById('ri_booth_type').textContent   = capFirst(item.slotType || item.booth_type || 'Booth');
    document.getElementById('ri_booth_price').textContent  = '₱' + parseFloat(item.price || 0).toLocaleString('en-PH', { minimumFractionDigits: 2 });

    var statusBadge = document.getElementById('ri_booth_status');
    statusBadge.textContent = statusLower === 'pending' ? 'Pending' : 'Reserved';
    statusBadge.className   = 'badge ' + (statusLower === 'pending' ? 'bg-warning text-dark' : 'bg-danger');

    document.getElementById('ri_merchant_section').innerHTML = '<div class="text-muted" style="font-size:0.85rem;">Loading…</div>';
    document.getElementById('ri_view_btn').classList.add('d-none');

    modal.show();

    if (!item.id) {
      document.getElementById('ri_merchant_section').innerHTML = '<div class="text-muted" style="font-size:0.85rem;">No reservation data (unsaved booth).</div>';
      return;
    }

    fetch(BOOTH_INFO_URL.replace('/0/', '/' + item.id + '/'), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var html = '';
      if (d.application_pk) {
        html += '<div class="fw-semibold">' + esc(d.merchant_name || '—') + '</div>';
        if (d.merchant_phone)    html += '<div class="text-muted" style="font-size:0.85rem;">📞 ' + esc(d.merchant_phone) + '</div>';
        if (d.merchant_email)    html += '<div class="text-muted" style="font-size:0.85rem;">✉ ' + esc(d.merchant_email) + '</div>';
        if (d.merchant_facebook) html += '<div style="font-size:0.85rem;"><a href="' + esc(d.merchant_facebook) + '" target="_blank" class="text-muted">🔗 Facebook Profile</a></div>';
        html += '<hr class="my-2">';
        html += '<dl class="row mb-0" style="font-size:0.8rem;">';
        html += '<dt class="col-5 text-muted">Submitted</dt><dd class="col-7">' + esc(d.applied_at || '—') + '</dd>';
        if (d.confirmed_at) {
          html += '<dt class="col-5 text-muted">Approved</dt><dd class="col-7">' + esc(d.confirmed_at) + '</dd>';
        } else {
          html += '<dt class="col-5 text-muted">Approved</dt><dd class="col-7"><em class="text-muted">Awaiting approval</em></dd>';
        }
        html += '<dt class="col-5 text-muted">Payment</dt><dd class="col-7">' + (d.payment_option === 'half' ? '50/50' : 'Full') + '</dd>';
        html += '<dt class="col-5 text-muted">Pay Status</dt><dd class="col-7">' + esc(d.payment_status || '—') + '</dd>';
        if (d.admin_notes) {
          html += '<dt class="col-5 text-muted">Admin Notes</dt><dd class="col-7">' + esc(d.admin_notes) + '</dd>';
        }
        html += '</dl>';

        var viewBtn = document.getElementById('ri_view_btn');
        viewBtn.href = APP_DETAIL_URL.replace('/0/', '/' + d.application_pk + '/');
        viewBtn.classList.remove('d-none');
      } else {
        html = '<div class="text-muted" style="font-size:0.85rem;">No active reservation found for this booth.</div>';
      }
      document.getElementById('ri_merchant_section').innerHTML = html;
    })
    .catch(function () {
      document.getElementById('ri_merchant_section').innerHTML = '<div class="text-danger" style="font-size:0.85rem;">Failed to load reservation info.</div>';
    });
  }

  function esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Undo ───────────────────────────────────────────────────────────────────
  function pushUndo() {
    undoStack.push(JSON.stringify(items));
    if (undoStack.length > 50) undoStack.shift();
  }

  window.undoLast = function () {
    if (!undoStack.length) { showToast('Nothing to undo.', 'secondary'); return; }
    items = JSON.parse(undoStack.pop()).map(function (d) { return shallowCopy(d); });
    markUnsaved();
    drawGrid();
  };

  // ── Unsaved indicator ──────────────────────────────────────────────────────
  function markUnsaved() {
    unsaved = true;
    var badge = document.getElementById('fpUnsavedBadge');
    if (badge) badge.classList.remove('d-none');
  }

  function markSaved() {
    unsaved = false;
    var badge = document.getElementById('fpUnsavedBadge');
    if (badge) badge.classList.add('d-none');
  }

  window.addEventListener('beforeunload', function (e) {
    if (unsaved) { e.preventDefault(); e.returnValue = ''; }
  });

  // ── Clear All ──────────────────────────────────────────────────────────────
  window.clearAll = function () {
    if (!confirm('Remove everything from the floor plan? You can Undo to recover.')) return;
    pushUndo();
    items = [];
    markUnsaved();
    drawGrid();
  };

  // ── Grid size update ───────────────────────────────────────────────────────
  window.updateGridSize = function () {
    var newCols = Math.max(5, Math.min(60, parseInt(document.getElementById('fp-cols').value) || 24));
    var newRows = Math.max(5, Math.min(40, parseInt(document.getElementById('fp-rows').value) || 18));
    var outside = items.filter(function (it) {
      return it.grid_x + it.grid_w > newCols || it.grid_y + it.grid_h > newRows;
    });
    if (outside.length) {
      if (!confirm(outside.length + ' item(s) fall outside the new grid bounds. Remove them?')) return;
      pushUndo();
      items = items.filter(function (it) {
        return it.grid_x + it.grid_w <= newCols && it.grid_y + it.grid_h <= newRows;
      });
    }
    FP_COLS = newCols;
    FP_ROWS = newRows;
    document.getElementById('fp-cols').value = FP_COLS;
    document.getElementById('fp-rows').value = FP_ROWS;
    resizeCanvas();
    markUnsaved();
  };

  // ── Save Layout ────────────────────────────────────────────────────────────
  window.saveLayout = function () {
    var btn = document.getElementById('btnSave');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving…'; }

    var payload = {
      grid_columns: FP_COLS,
      grid_rows:    FP_ROWS,
      items: items.map(function (i) {
        return {
          id:            i.id   || null,
          booth_number:  i.booth_number || null,
          label:         i.label        || '',
          description:   i.description  || '',
          is_landmark:   i.isLandmark   || i.is_landmark || false,
          landmark_type: i.landmarkType || i.landmark_type || '',
          color:         i.color        || '',
          booth_type:    i.slotType     || i.booth_type   || 'BOOTH',
          category:      i.category     || 'OTHER',
          price:         i.price        || 0,
          status:        i.status       || 'AVAILABLE',
          grid_x:        i.grid_x,
          grid_y:        i.grid_y,
          grid_w:        i.grid_w,
          grid_h:        i.grid_h,
        };
      }),
    };

    fetch(SAVE_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
      body:    JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-floppy me-1"></i>Save Layout'; }
      if (res.success) {
        // Update local items with server-assigned IDs
        if (res.items) {
          res.items.forEach(function (srv) {
            var local = items.find(function (i) {
              return i.grid_x === srv.grid_x && i.grid_y === srv.grid_y &&
                     i.grid_w === srv.grid_w && i.grid_h === srv.grid_h;
            });
            if (local) { local.id = srv.id; local.booth_number = srv.booth_number; }
          });
        }
        markSaved();
        showToast('Layout saved!', 'success');
        if (res.warning) { showToast(res.warning, 'warning'); }
      } else {
        showToast(res.error || 'Save failed.', 'danger');
      }
    })
    .catch(function () {
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-floppy me-1"></i>Save Layout'; }
      showToast('Network error. Please try again.', 'danger');
    });
  };

  // ── Context menu ───────────────────────────────────────────────────────────
  var ctxMenu = document.getElementById('fpContextMenu');

  function showContextMenu(e, tempId) {
    contextTempId = tempId;
    ctxMenu.style.left = e.clientX + 'px';
    ctxMenu.style.top  = e.clientY + 'px';
    ctxMenu.classList.remove('d-none');
  }

  function hideContextMenu() { ctxMenu.classList.add('d-none'); }

  document.addEventListener('click', hideContextMenu);

  window.ctxEdit = function () {
    hideContextMenu();
    var item = items.find(function (i) { return i.tempId === contextTempId; });
    if (!item) return;
    if (isProtected(item)) {
      openReservedInfo(item);
      return;
    }
    openEditModal(item);
  };

  window.ctxDelete = function () {
    hideContextMenu();
    var item = items.find(function (i) { return i.tempId === contextTempId; });
    if (!item) return;
    if (isProtected(item)) {
      showToast('This booth has an active reservation and cannot be deleted. Manage it through Reservations.', 'danger');
      return;
    }
    pushUndo();
    items = items.filter(function (i) { return i.tempId !== contextTempId; });
    markUnsaved();
    drawGrid();
  };

  // ── Polling (15 s — sync statuses changed by reservations) ────────────────
  function startPolling() {
    setInterval(function () {
      fetch(POLL_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.items) return;
          var changed = false;
          data.items.forEach(function (srv) {
            var local = items.find(function (i) { return i.id && i.id === srv.id; });
            if (local && local.status !== srv.status) {
              local.status = srv.status;
              changed = true;
            }
          });
          if (changed) drawGrid();
        })
        .catch(function () {});
    }, 15000);
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function showToast(msg, type) {
    var t = document.createElement('div');
    t.className = 'alert alert-' + (type || 'info') + ' position-fixed bottom-0 end-0 m-3 shadow';
    t.style.zIndex  = '9999';
    t.style.maxWidth = '340px';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 3500);
  }

  function capFirst(s) {
    return String(s || '').replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  function shallowCopy(o) {
    return Object.assign({}, o);
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  window.addEventListener('load', function () {
    console.log('[FP] window.load fired');
    initCanvas();
    if (!canvas) return;
    attachCanvasEvents();

    items = LAYOUT_DATA.map(function (d) {
      return Object.assign({}, d, {
        tempId:       ++tempIdCtr,
        isLandmark:   d.is_landmark,
        slotType:     d.booth_type,
        landmarkType: d.landmark_type,
      });
    });

    selectTool('pointer', null);
    drawGrid();
    startPolling();
  });

})();
