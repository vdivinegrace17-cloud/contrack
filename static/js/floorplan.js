/**
 * floorplan.js — ConTrack Floor Plan (Leaflet.js)
 * ================================================
 * Loaded by two templates:
 *
 *   booth_tagger.html  (organizer) — can ADD, MOVE, DELETE booth markers
 *   floor_plan.html    (merchant)  — READ-ONLY, can click to open apply form
 *
 * Both templates must set window.CONTRACK before this script runs:
 *
 *   <script>
 *     window.CONTRACK = {
 *       floorPlanUrl:  "{{ floor_plan.image.url }}",
 *       floorPlanW:    {{ floor_plan.natural_width }},
 *       floorPlanH:    {{ floor_plan.natural_height }},
 *       booths:        {{ booths_json|safe }},
 *       mode:          "tagger",   // or "viewer"
 *       saveUrl:       "{% url 'booths:save_booth' event.slug %}",    // tagger only
 *       deleteUrl:     "/booths/delete/",                             // tagger only
 *       csrfToken:     "{{ csrf_token }}",
 *     };
 *   </script>
 *
 * Leaflet is loaded via CDN in base.html — no npm or build step needed.
 */

(function () {
  "use strict";

  const cfg = window.CONTRACK;
  if (!cfg) {
    console.error("ConTrack: window.CONTRACK config not found.");
    return;
  }

  // ── 1. Set up Leaflet with a simple (image) CRS ────────────────────────────
  //
  // L.CRS.Simple treats coordinates as plain [y, x] pixel values.
  // We map the floor plan image to bounds [[0,0], [H, W]].
  const H = cfg.floorPlanH;
  const W = cfg.floorPlanW;

  const map = L.map("floor-plan-map", {
    crs:              L.CRS.Simple,
    minZoom:          -2,
    maxZoom:          3,
    zoomSnap:         0.25,
    attributionControl: false,
  });

  // Image overlay — the floor plan image IS the map background
  const bounds = [[0, 0], [H, W]];
  L.imageOverlay(cfg.floorPlanUrl, bounds).addTo(map);
  map.fitBounds(bounds);

  // ── 2. Marker color helper ─────────────────────────────────────────────────
  const STATUS_COLORS = {
    AVAILABLE:   "#22c55e",   // green
    PENDING:     "#f97316",   // orange
    RESERVED:    "#ef4444",   // red
    UNAVAILABLE: "#9ca3af",   // gray
  };

  function makeIcon(color) {
    // Creates a simple colored circle icon — no external image needed
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
        <circle cx="14" cy="14" r="11" fill="${color}" stroke="white" stroke-width="2.5"/>
      </svg>`;
    return L.divIcon({
      html:        svg,
      className:   "",          // clear Leaflet's default white box
      iconSize:    [28, 28],
      iconAnchor:  [14, 14],
      popupAnchor: [0, -16],
    });
  }

  // ── 3. Convert between % coords and Leaflet [lat, lng] ────────────────────
  //
  // We store booth positions as percentages (0–100) of the image dimensions.
  // Leaflet CRS.Simple uses [y_px, x_px] — note Y is inverted for images.
  function percentToLatLng(xPct, yPct) {
    return [(1 - yPct / 100) * H, (xPct / 100) * W];
  }

  function latLngToPercent(latlng) {
    return {
      x_percent: (latlng.lng / W) * 100,
      y_percent: (1 - latlng.lat / H) * 100,
    };
  }

  // ── 4. Render existing booths ──────────────────────────────────────────────
  const markerMap = {};  // booth.id → Leaflet marker

  function renderBooth(booth) {
    const color  = STATUS_COLORS[booth.status] || "#9ca3af";
    const latlng = percentToLatLng(booth.x_percent, booth.y_percent);
    const marker = L.marker(latlng, {
      icon:      makeIcon(color),
      draggable: cfg.mode === "tagger",  // only organizer can drag
    }).addTo(map);

    // Popup content differs by mode
    if (cfg.mode === "tagger") {
      marker.bindPopup(buildTaggerPopup(booth));
    } else {
      marker.bindPopup(buildViewerPopup(booth));
    }

    // Save position after drag (tagger mode only)
    if (cfg.mode === "tagger") {
      marker.on("dragend", function (e) {
        const pct = latLngToPercent(e.target.getLatLng());
        saveBooth({ ...booth, ...pct });
      });
    }

    markerMap[booth.id] = marker;
  }

  cfg.booths.forEach(renderBooth);

  // ── 5. Tagger: click empty space to add a new booth ───────────────────────
  if (cfg.mode === "tagger") {
    map.on("click", function (e) {
      // Only add booth if click wasn't on an existing marker
      showAddBoothDialog(e.latlng);
    });
  }

  // ── 6. Popup builders ─────────────────────────────────────────────────────
  function buildViewerPopup(booth) {
    const applyBtn = booth.status === "AVAILABLE"
      ? `<a href="/reservations/apply/${booth.id}/"
            class="btn btn-sm btn-success mt-2 w-100">Apply for this booth</a>`
      : `<span class="badge bg-secondary mt-2">${booth.status}</span>`;

    return `
      <div style="min-width:180px">
        <strong>${booth.label || "Booth " + booth.booth_number}</strong><br>
        <small class="text-muted">${booth.category}</small><br>
        <span class="fw-bold">₱${booth.price}</span>
        ${applyBtn}
      </div>`;
  }

  function buildTaggerPopup(booth) {
    return `
      <div style="min-width:200px">
        <strong>${booth.label || "Booth " + booth.booth_number}</strong><br>
        <small>${booth.category} — ₱${booth.price}</small>
        <div class="mt-2 d-flex gap-1">
          <button class="btn btn-sm btn-outline-primary" onclick="editBooth(${booth.id})">Edit</button>
          <button class="btn btn-sm btn-outline-danger"  onclick="deleteBooth(${booth.id})">Delete</button>
        </div>
      </div>`;
  }

  // ── 7. Add-booth dialog (tagger mode) ─────────────────────────────────────
  function showAddBoothDialog(latlng) {
    const pct = latLngToPercent(latlng);

    // Simple prompt-based input; replace with a Bootstrap modal in production
    const boothNumber = prompt("Booth number (e.g. A1, Table-3):");
    if (!boothNumber) return;

    const label    = prompt("Display name (optional):", "") || "";
    const price    = parseFloat(prompt("Price (₱):", "0") || "0");
    const category = prompt("Category (FOOD / MERCH / ARTS / SERV / COLL / OTHER):", "OTHER") || "OTHER";

    saveBooth({
      booth_number: boothNumber,
      label:        label,
      price:        price,
      category:     category.toUpperCase(),
      x_percent:    pct.x_percent,
      y_percent:    pct.y_percent,
    });
  }

  // ── 8. AJAX: save booth to Django backend ─────────────────────────────────
  function saveBooth(data) {
    fetch(cfg.saveUrl, {
      method:  "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken":  cfg.csrfToken,
      },
      body: JSON.stringify(data),
    })
      .then((r) => r.json())
      .then((res) => {
        if (res.success) {
          // Refresh page to re-render updated markers
          // TODO: for a smoother UX, update the marker in-place instead
          location.reload();
        } else {
          alert("Save failed: " + res.error);
        }
      })
      .catch((err) => console.error("Save error:", err));
  }

  // ── 9. AJAX: delete booth ─────────────────────────────────────────────────
  window.deleteBooth = function (boothId) {
    if (!confirm("Delete this booth?")) return;
    fetch(`${cfg.deleteUrl}${boothId}/`, {
      method:  "POST",
      headers: { "X-CSRFToken": cfg.csrfToken },
    })
      .then((r) => r.json())
      .then((res) => { if (res.success) location.reload(); })
      .catch((err) => console.error("Delete error:", err));
  };

  // ── 10. Edit booth (stub — wire to a modal form in production) ────────────
  window.editBooth = function (boothId) {
    // TODO: open a Bootstrap modal pre-filled with booth data
    alert(`Edit booth ${boothId} — implement modal form here.`);
  };

})();
