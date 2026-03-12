import re

with open('docs/index.html', 'r') as f:
    content = f.read()

cmp_panel_old = """    /* ── Instance compare panel ─────────────────────────────── */
    function renderInstanceCompare(row) {
      const best = state.scoredRows[0];
      if (!best || row.instance_type === best.instance_type) { closeCompare(); return; }
      el('cmpTitle').textContent = row.instance_type;
      el('cmpSub').textContent = `${row.instance_category} · ${row.region} · vs.top pick ${best.instance_type} `;
      el('cmpSpecs').innerHTML = [
        { lbl: 'Price/hr', val: `$${row.price_usd_hour.toFixed(4)} `, sub: `vs $${best.price_usd_hour.toFixed(4)} ` },
        { lbl: 'vCPUs', val: row.vcpus, sub: `vs ${best.vcpus} ` },
        { lbl: 'Memory', val: `${row.memory_gib} GiB`, sub: `vs ${best.memory_gib} GiB` },
        { lbl: 'GPU Count', val: row.gpu_count > 0 ? row.gpu_count : '—', sub: `vs ${best.gpu_count > 0 ? best.gpu_count : '—'} ` },
        { lbl: 'Network', val: `${row.network_score} /5`, sub: `vs ${best.network_score}/5` },
        { lbl: 'Score', val: (row.composite * 100).toFixed(1) + '%', sub: `vs ${(best.composite * 100).toFixed(1)}% ` },
      ].map(s => `<div class="cmp-spec-item"><div class="cmp-spec-lbl">${s.lbl}</div><div class="cmp-spec-val">${s.val}</div><div class="cmp-spec-sub">${s.sub}</div></div>`).join('');
      const dims = ['Price Eff.', 'CPU', 'Memory', 'Network', 'GPU'];
      const catC = CAT_COLOR[row.instance_category] || '#4f46e5';
      const topC = CAT_COLOR[best.instance_category] || '#4f46e5';
      Plotly.react('cmpChart', [
        { name: row.instance_type, type: 'bar', x: dims, y: [row.scoreP, row.scoreC, row.scoreM, row.scoreN, row.scoreG], marker: { color: catC, opacity: .85 }, hovertemplate: '%{x}: %{y:.2f}<extra>' + row.instance_type + '</extra>' },
        { name: best.instance_type + ' (top)', type: 'bar', x: dims, y: [best.scoreP, best.scoreC, best.scoreM, best.scoreN, best.scoreG], marker: { color: topC, opacity: .5, pattern: { shape: '/' } }, hovertemplate: '%{x}: %{y:.2f}<extra>' + best.instance_type + '</extra>' },
      ], {
        ...PLOTLY_BASE, barmode: 'group',
        yaxis: { range: [0, 1], gridcolor: '#e2e8f0', zeroline: false, title: 'Normalized score' },
        xaxis: { gridcolor: '#e2e8f0' },
        legend: { orientation: 'h', y: -0.26, x: 0, font: { size: 11 } },
        margin: { t: 10, r: 12, b: 60, l: 50 },
      }, { responsive: true, displayModeBar: false });
      el('comparePanel').classList.add('visible');
    }
    function closeCompare() { el('comparePanel').classList.remove('visible'); }"""

cmp_panel_new = """    /* ── Instance compare panel ─────────────────────────────── */
    function renderInstanceCompare(row) {
      if (state.compareSelection.size > 0) return; // don't ruin multi-compare session
      const best = state.scoredRows[0];
      if (!best || row.instance_type === best.instance_type) { closeCompare(); return; }
      el('cmpTitle').textContent = row.instance_type;
      el('cmpSub').textContent = `vs. top pick ${best.instance_type}`;
      
      const dims = ['Price Eff.', 'CPU', 'Memory', 'Network', 'GPU'];
      const catC = CAT_COLOR[row.instance_category] || '#4f46e5';
      const topC = CAT_COLOR[best.instance_category] || '#4f46e5';
      
      el('cmpSpecs').className = 'cmp-specs'; // standard 1v1 grid
      el('cmpSpecs').innerHTML = [
        { lbl: 'Price/hr', val: `$${row.price_usd_hour.toFixed(4)}`, sub: `vs $${best.price_usd_hour.toFixed(4)}` },
        { lbl: 'vCPUs', val: row.vcpus, sub: `vs ${best.vcpus}` },
        { lbl: 'Memory', val: `${row.memory_gib} GiB`, sub: `vs ${best.memory_gib} GiB` },
        { lbl: 'GPU Count', val: row.gpu_count > 0 ? row.gpu_count : '—', sub: `vs ${best.gpu_count > 0 ? best.gpu_count : '—'}` },
        { lbl: 'Network', val: `${row.network_score} / 5`, sub: `vs ${best.network_score} / 5` },
        { lbl: 'Score', val: (row.composite * 100).toFixed(1) + '%', sub: `vs ${(best.composite * 100).toFixed(1)}%` },
      ].map(s => `<div class="cmp-spec-item"><div class="cmp-spec-lbl">${s.lbl}</div><div class="cmp-spec-val">${s.val}</div><div class="cmp-spec-sub">${s.sub}</div></div>`).join('');

      Plotly.react('cmpChart', [
        { name: row.instance_type, type: 'bar', x: dims, y: [row.scoreP, row.scoreC, row.scoreM, row.scoreN, row.scoreG], marker: { color: catC, opacity: .85 }, hovertemplate: '%{x}: %{y:.2f}<extra>' + row.instance_type + '</extra>' },
        { name: best.instance_type + ' (top)', type: 'bar', x: dims, y: [best.scoreP, best.scoreC, best.scoreM, best.scoreN, best.scoreG], marker: { color: topC, opacity: .5, pattern: { shape: '/' } }, hovertemplate: '%{x}: %{y:.2f}<extra>' + best.instance_type + '</extra>' },
      ], {
        ...PLOTLY_BASE, barmode: 'group',
        yaxis: { range: [0, 1], gridcolor: '#e2e8f0', zeroline: false, title: 'Normalized score' },
        xaxis: { gridcolor: '#e2e8f0' },
        legend: { orientation: 'h', y: -0.26, x: 0, font: { size: 11 } },
        margin: { t: 10, r: 12, b: 60, l: 50 },
      }, { responsive: true, displayModeBar: false });
      el('comparePanel').classList.add('visible');
    }
    
    function openMultiCompare() {
      if (state.compareSelection.size < 2) return;
      
      const instances = Array.from(state.compareSelection);
      const rows = instances.map(type => state.scoredRows.find(r => r.instance_type === type)).filter(Boolean);
      
      el('cmpTitle').textContent = `Comparing ${rows.length} Instances`;
      el('cmpSub').textContent = instances.join(', ');
      
      // Build a multi-column flex layout for the text specs
      el('cmpSpecs').className = 'cmp-specs cmp-multi';
      let html = `<div class="cmp-multi-wrap" style="display:flex; gap:16px; overflow-x:auto; padding-bottom:8px;">`;
      rows.forEach(r => {
        const cc = CAT_COLOR[r.instance_category] || '#4f46e5';
        html += `<div style="flex:1; min-width:140px; border:1px solid #e2e8f0; border-radius:8px; padding:12px; background:#fff;">
          <div style="font-weight:700; color:${cc}; margin-bottom:12px; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:8px;">${r.instance_type}</div>
          <div style="margin-bottom:8px"><div style="font-size:11px;color:#64748b">Price/hr</div><div style="font-weight:600;font-size:13px">$${r.price_usd_hour.toFixed(4)}</div></div>
          <div style="margin-bottom:8px"><div style="font-size:11px;color:#64748b">vCPUs</div><div style="font-weight:600;font-size:13px">${r.vcpus}</div></div>
          <div style="margin-bottom:8px"><div style="font-size:11px;color:#64748b">Memory</div><div style="font-weight:600;font-size:13px">${r.memory_gib} GiB</div></div>
          <div style="margin-bottom:8px"><div style="font-size:11px;color:#64748b">GPU Count</div><div style="font-weight:600;font-size:13px">${r.gpu_count > 0 ? r.gpu_count : '—'}</div></div>
          <div style="margin-bottom:8px"><div style="font-size:11px;color:#64748b">Network</div><div style="font-weight:600;font-size:13px">${r.network_score} / 5</div></div>
          <div><div style="font-size:11px;color:#64748b">Score</div><div style="font-weight:600;font-size:13px">${(r.composite * 100).toFixed(1)}%</div></div>
        </div>`;
      });
      html += `</div>`;
      el('cmpSpecs').innerHTML = html;
      
      const dims = ['Price Eff.', 'CPU', 'Memory', 'Network', 'GPU'];
      const traces = rows.map((r, i) => {
        // use alternating palette for multi-compare if categories are same, else use category color
        const cc = CAT_COLOR[r.instance_category] || '#4f46e5';
        // if multiple instances have the same category, tint them slightly differently
        const palette = ['#4f46e5', '#10b981', '#f59e0b', '#ec4899', '#0ea5e9', '#8b5cf6'];
        const color = rows.length > 2 && new Set(rows.map(x=>x.instance_category)).size === 1 ? palette[i % palette.length] : cc;
        
        return {
          name: r.instance_type,
          type: 'bar',
          x: dims,
          y: [r.scoreP, r.scoreC, r.scoreM, r.scoreN, r.scoreG],
          marker: { color: color, opacity: .85 + (i * 0.05) },
          hovertemplate: '%{x}: %{y:.2f}<extra>' + r.instance_type + '</extra>'
        };
      });

      Plotly.react('cmpChart', traces, {
        ...PLOTLY_BASE, barmode: 'group',
        yaxis: { range: [0, 1], gridcolor: '#e2e8f0', zeroline: false, title: 'Normalized score' },
        xaxis: { gridcolor: '#e2e8f0' },
        legend: { orientation: 'h', y: -0.26, x: 0, font: { size: 11 } },
        margin: { t: 10, r: 12, b: 60, l: 50 },
      }, { responsive: true, displayModeBar: false });
      
      el('comparePanel').classList.add('visible');
    }

    function closeCompare() {
      el('comparePanel').classList.remove('visible');
    }"""

content = content.replace(cmp_panel_old, cmp_panel_new)

with open('docs/index.html', 'w') as f:
    f.write(content)
