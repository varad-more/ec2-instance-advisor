import re

with open('docs/index.html', 'r') as f:
    content = f.read()

render_table_old = """    /* ── Table ──────────────────────────────────────────────── */
    function renderTable(rows, query = '') {
      const q = query.toLowerCase().trim();
      const filtered = q ? rows.filter(r =>
        r.instance_type.toLowerCase().includes(q) ||
        r.instance_category.toLowerCase().includes(q) ||
        r.region.toLowerCase().includes(q)) : rows;
      const lim = state.tableLimit || 30;
      const shown = filtered.slice(0, lim);
      el('tableCount').textContent = q
        ? `\\${shown.length} of \\${filtered.length} match`
        : `Showing \\${shown.length} of \\${rows.length} `;
      const lmw = el('tableLoadMoreWrap');
      if (!shown.length) {
        el('table').innerHTML = `<tbody><tr><td colspan="10" style="text-align:center;padding:24px;color:var(--muted)">No instances match "${query}"</td></tr></tbody>`;
        if (lmw) lmw.innerHTML = '';
        return;
      }
      el('table').innerHTML =
        `<thead><tr><th>#</th><th>Instance</th><th>Category</th><th>Region</th><th>vCPU</th><th>Mem (GiB)</th><th>GPU</th><th>Net</th><th>$/hr</th><th>Score</th></tr>
     <tr><td colspan="10" style="font-size:10px;color:var(--muted);padding:4px 10px 5px;background:#fafbff;font-weight:600">💡 Click any row to compare specs &amp; scores vs the top pick</td></tr></thead>` +
        `<tbody>\\${shown.map((r, shownIdx) => {
          const cc = CAT_COLOR[r.instance_category] || '#6b7280';
          const cbg = CAT_BG[r.instance_category] || '#f9fafb';
          // globalIdx → used for click handler (state.scoredRows lookup) and top-pick badge
          const globalIdx = rows.indexOf(r);
          // shownIdx+1 → always sequential (1, 2, 3…) within the current view/filter
          const serialNum = shownIdx + 1;
          return `<tr class="\\${globalIdx === 0 ? 'rank-1' : ''}" style="cursor:pointer" onclick="handleRowClick(\\${globalIdx})">
        <td style="color:var(--muted);font-weight:800;font-size:11px">\\${globalIdx === 0 ? '🥇' : serialNum}</td>
        <td style="font-weight:700">\\${r.instance_type}</td>
        <td><span class="cat-pill" style="background:\\${cbg};color:\\${cc}">\\${r.instance_category}</span></td>
        <td>\\${r.region}</td><td>\\${r.vcpus}</td><td>\\${r.memory_gib}</td>
        <td>\\${r.gpu_count}</td><td>\\${r.network_score}</td>
        <td>$\\${r.price_usd_hour.toFixed(4)}</td>
        <td><div class="score-cell"><div class="score-bar" style="width:\\${(r.composite * 58).toFixed(0)}px;background:\\${cc}"></div><span class="score-num">\\${r.composite.toFixed(3)}</span></div></td>
      </tr>`;
        }).join('')
        }</tbody>`;
      /* ── Load more button ── */
      if (lmw) {
        if (filtered.length > shown.length) {
          const rem = Math.min(filtered.length - shown.length, 30);
          lmw.innerHTML = `<button class="load-more-btn" onclick="tableLoadMore()"> Show \\${rem} more (\\${filtered.length - shown.length} remaining) ↓</button > `;
        } else {
          lmw.innerHTML = '';
        }
      }
    }"""

render_table_new = """    /* ── Floating Compare Bar ───────────────────────────────── */
    function renderCompareBar() {
      let bar = el('compareActionBar');
      if (!bar) {
        bar = document.createElement('div');
        bar.id = 'compareActionBar';
        bar.className = 'compare-action-bar';
        document.body.appendChild(bar);
      }
      const count = state.compareSelection.size;
      const countText = count === 1 ? '1 instance selected' : count + ' instances selected';
      if (count > 0) {
        bar.innerHTML = `<div class="cab-inner">
          <span class="cab-count">\\${countText}</span>
          <div class="cab-actions">
            <button class="cab-btn cab-btn-clear" onclick="clearCompareSelection()">✕ Clear</button>
            <button class="cab-btn cab-btn-primary" onclick="openMultiCompare()" \\${count < 2 ? 'disabled' : ''}>Compare \\${count} →</button>
          </div>
        </div>`;
        bar.classList.add('cab-visible');
      } else {
        bar.classList.remove('cab-visible');
      }
    }

    function toggleCompareSelection(e, globalIdx) {
      e.stopPropagation(); // prevent row click
      const row = state.scoredRows[globalIdx];
      if (!row) return;
      if (state.compareSelection.has(row.instance_type)) {
        state.compareSelection.delete(row.instance_type);
      } else {
        state.compareSelection.add(row.instance_type);
      }
      renderTable(state.scoredRows, el('tableSearch').value);
      renderCompareBar();
    }

    function clearCompareSelection() {
      state.compareSelection.clear();
      renderTable(state.scoredRows, el('tableSearch').value);
      renderCompareBar();
    }

    /* ── Table ──────────────────────────────────────────────── */
    function renderTable(rows, query = '') {
      const q = query.toLowerCase().trim();
      const filtered = q ? rows.filter(r =>
        r.instance_type.toLowerCase().includes(q) ||
        r.instance_category.toLowerCase().includes(q) ||
        r.region.toLowerCase().includes(q)) : rows;
      const lim = state.tableLimit || 30;
      const shown = filtered.slice(0, lim);
      el('tableCount').textContent = q
        ? `\\${shown.length} of \\${filtered.length} match`
        : `Showing \\${shown.length} of \\${rows.length} `;
      const lmw = el('tableLoadMoreWrap');
      if (!shown.length) {
        el('table').innerHTML = `<tbody><tr><td colspan="11" style="text-align:center;padding:24px;color:var(--muted)">No instances match "${query}"</td></tr></tbody>`;
        if (lmw) lmw.innerHTML = '';
        return;
      }
      el('table').innerHTML =
        `<thead><tr>
          <th style="width: 44px; text-align: center;"></th>
          <th>#</th><th>Instance</th><th>Category</th><th>Region</th><th>vCPU</th><th>Mem (GiB)</th><th>GPU</th><th>Net</th><th>$/hr</th><th>Score</th>
        </tr>
     <tr><td colspan="11" style="font-size:10px;color:var(--muted);padding:4px 10px 5px;background:#fafbff;font-weight:600">💡 Click any row to view its details, or use checkboxes for multi-comparison.</td></tr></thead>` +
        `<tbody>\\${shown.map((r, shownIdx) => {
          const cc = CAT_COLOR[r.instance_category] || '#6b7280';
          const cbg = CAT_BG[r.instance_category] || '#f9fafb';
          // globalIdx → used for click handler (state.scoredRows lookup) and top-pick badge
          const globalIdx = rows.indexOf(r);
          // shownIdx+1 → always sequential (1, 2, 3…) within the current view/filter
          const serialNum = shownIdx + 1;
          const isSelected = state.compareSelection.has(r.instance_type);
          return `<tr class="\\${globalIdx === 0 ? 'rank-1' : ''} \\${isSelected ? 'row-selected' : ''}" style="cursor:pointer" onclick="handleRowClick(\\${globalIdx})">
        <td style="text-align: center; width: 44px;" onclick="toggleCompareSelection(event, \\${globalIdx})">
          <div class="compare-checkbox-wrap">
            <input type="checkbox" class="compare-checkbox" \\${isSelected ? 'checked' : ''} onclick="event.stopPropagation()" onchange="toggleCompareSelection(event, \\${globalIdx})">
          </div>
        </td>
        <td style="color:var(--muted);font-weight:800;font-size:11px">\\${globalIdx === 0 ? '🥇' : serialNum}</td>
        <td style="font-weight:700">\\${r.instance_type}</td>
        <td><span class="cat-pill" style="background:\\${cbg};color:\\${cc}">\\${r.instance_category}</span></td>
        <td>\\${r.region}</td><td>\\${r.vcpus}</td><td>\\${r.memory_gib}</td>
        <td>\\${r.gpu_count}</td><td>\\${r.network_score}</td>
        <td>$\\${r.price_usd_hour.toFixed(4)}</td>
        <td><div class="score-cell"><div class="score-bar" style="width:\\${(r.composite * 58).toFixed(0)}px;background:\\${cc}"></div><span class="score-num">\\${r.composite.toFixed(3)}</span></div></td>
      </tr>`;
        }).join('')
        }</tbody>`;
      /* ── Load more button ── */
      if (lmw) {
        if (filtered.length > shown.length) {
          const rem = Math.min(filtered.length - shown.length, 30);
          lmw.innerHTML = `<button class="load-more-btn" onclick="tableLoadMore()"> Show \\${rem} more (\\${filtered.length - shown.length} remaining) ↓</button > `;
        } else {
          lmw.innerHTML = '';
        }
      }
    }"""

content = content.replace(render_table_old, render_table_new)

with open('docs/index.html', 'w') as f:
    f.write(content)
