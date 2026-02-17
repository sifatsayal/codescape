"""UI generation module - generates HTML visualization."""
import json

def generate_html(data: dict) -> str:
    """Generate the interactive HTML visualization."""
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codescape - ''' + data['rootName'] + '''</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Space Grotesk', sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
            color: #e0e0e0;
            overflow: hidden;
            height: 100vh;
        }
        
        #header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(15, 15, 25, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(100, 100, 150, 0.2);
            display: flex;
            align-items: center;
            padding: 0 24px;
            z-index: 100;
            gap: 24px;
        }
        
        #header h1 {
            font-size: 18px;
            font-weight: 600;
            background: linear-gradient(90deg, #06b6d4, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #888;
        }
        
        .stat {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .stat-value {
            color: #06b6d4;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: #888;
        }
        
        .control-group select {
            background: rgba(30, 30, 50, 0.8);
            border: 1px solid rgba(100, 100, 150, 0.3);
            border-radius: 6px;
            padding: 6px 10px;
            color: #e0e0e0;
            font-size: 12px;
            cursor: pointer;
        }
        
        .control-group select:focus {
            outline: none;
            border-color: #7c3aed;
        }
        
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: auto;
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .breadcrumb-item {
            color: #7c3aed;
            cursor: pointer;
            transition: color 0.2s;
        }
        
        .breadcrumb-item:hover {
            color: #a78bfa;
        }
        
        .breadcrumb-sep {
            color: #444;
        }
        .breadcrumb-file {
            color: #06b6d4;
        }
        
        #graph-container {
            position: fixed;
            top: 60px;
            left: 0;
            right: 380px;
            bottom: 0;
        }

        #sidebar {
            position: fixed;
            top: 60px;
            right: 0;
            width: 380px;
            bottom: 0;
            background: rgba(15, 15, 25, 0.98);
            border-left: 1px solid rgba(100, 100, 150, 0.2);
            overflow-y: auto;
            padding: 16px;
        }
        .sidebar-section {
            margin-bottom: 20px;
        }
        .sidebar-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .card-remove {
            width: 24px;
            height: 24px;
            border: none;
            background: rgba(100, 100, 150, 0.2);
            color: #666;
            font-size: 16px;
            line-height: 1;
            border-radius: 6px;
            cursor: pointer;
            padding: 0;
            flex-shrink: 0;
        }
        .card-remove:hover {
            background: rgba(239, 68, 68, 0.3);
            color: #fca5a5;
        }
        .details-placeholder {
            color: #444;
            font-style: italic;
            padding: 24px 16px;
            text-align: center;
            font-size: 13px;
        }
        .details-repo-stats {
            padding: 20px 16px;
        }
        .details-repo-stats .stats-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #666;
            margin-bottom: 14px;
        }
        .details-repo-stats .stat {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid rgba(100, 100, 150, 0.15);
            font-size: 13px;
            color: #888;
        }
        .details-repo-stats .stat:last-child { border-bottom: none; }
        .details-repo-stats .stat-value {
            color: #06b6d4;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .file-info {
            background: rgba(30, 30, 50, 0.5);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(100, 100, 150, 0.15);
        }
        
        .file-name {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            word-break: break-all;
        }
        .sidebar-icon {
            flex-shrink: 0;
            width: 22px;
            height: 22px;
        }
        
        .file-path {
            font-size: 12px;
            color: #666;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 16px;
            word-break: break-all;
        }

        .folder-count-toggle {
            display: flex;
            gap: 2px;
            margin-bottom: 12px;
            background: rgba(20, 20, 35, 0.6);
            border-radius: 8px;
            padding: 2px;
        }
        .folder-count-toggle button {
            flex: 1;
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: transparent;
            color: #666;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .folder-count-toggle button:hover {
            color: #888;
        }
        .folder-count-toggle button.active {
            background: rgba(124, 58, 237, 0.25);
            color: #a78bfa;
        }
        
        .file-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .file-meta.four-col {
            grid-template-columns: 1fr 1fr 1fr 1fr;
        }
        
        .meta-item {
            background: rgba(20, 20, 35, 0.6);
            padding: 10px 12px;
            border-radius: 8px;
        }
        
        .meta-item.highlight {
            background: rgba(124, 58, 237, 0.15);
            border: 1px solid rgba(124, 58, 237, 0.3);
        }
        .meta-item.highlight-inbound {
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.35);
        }
        .meta-item.highlight-inbound .meta-value {
            color: #22c55e;
        }
        .meta-item.highlight-outbound {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.35);
        }
        .meta-item.highlight-outbound .meta-value {
            color: #f59e0b;
        }
        
        .meta-label {
            font-size: 10px;
            text-transform: uppercase;
            color: #555;
            margin-bottom: 4px;
        }
        
        .meta-value {
            font-size: 14px;
            font-weight: 500;
            color: #888;
        }
        
        .meta-value.file {
            color: #06b6d4;
        }
        
        .meta-value.inbound {
            color: #22c55e;
        }
        
        .meta-value.outbound {
            color: #f59e0b;
        }
        
        .deps-section {
            margin-top: 16px;
        }
        
        .deps-title {
            font-size: 12px;
            color: #888;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .deps-title .count {
            color: #22c55e;
            font-weight: 600;
        }
        
        .dep-item {
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            padding: 8px 12px;
            background: rgba(20, 20, 35, 0.4);
            border-radius: 6px;
            margin-bottom: 4px;
            color: #888;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .dep-item:hover {
            background: rgba(124, 58, 237, 0.2);
            color: #e0e0e0;
        }
        
        .dep-item .arrow {
            font-size: 10px;
            color: #555;
        }
        
        .dep-item.inbound .arrow {
            color: #22c55e;
        }
        
        .dep-item.outbound .arrow {
            color: #f59e0b;
        }
        
        .dep-item .name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .imports-list {
            margin-top: 16px;
        }
        
        .imports-title {
            font-size: 12px;
            color: #f59e0b;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .import-item {
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            padding: 6px 10px;
            border-radius: 6px;
            margin-bottom: 4px;
            color: #fbbf24;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .folder-contents {
            margin-top: 16px;
        }
        
        .folder-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(20, 20, 35, 0.4);
            border-radius: 8px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13px;
        }
        
        .folder-item:hover {
            background: rgba(124, 58, 237, 0.2);
        }
        
        .folder-icon {
            font-size: 14px;
        }
        
        .item-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .item-meta {
            font-size: 11px;
            color: #555;
            font-family: 'JetBrains Mono', monospace;
        }
        
        svg {
            width: 100%;
            height: 100%;
        }
        
        .node {
            cursor: pointer;
        }
        
        .node circle {
            stroke-width: 2px;
            transition: stroke-width 0.05s ease-out;
        }
        
        .node.selected circle {
            stroke-width: 4px;
            filter: brightness(1.3) drop-shadow(0 0 8px currentColor);
            transition: stroke-width 0.05s ease-out;
        }
        
        .node:hover circle {
            filter: brightness(1.3);
        }
        
        .node text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            fill: #999;
            pointer-events: none;
        }
        
        .link {
            fill: none;
            stroke-opacity: 0;
            transition: stroke-opacity 0.3s;
        }
        
        .link.visible {
            stroke-opacity: 0.6;
        }
        
        .link.import {
            stroke: #7c3aed;
        }
        
        .link.inbound {
            stroke: #22c55e;
            stroke-width: 2px;
        }
        
        .link.outbound {
            stroke: #f59e0b;
            stroke-width: 2px;
        }
        
        .link.dep-arrow.visible {
            stroke-dasharray: 8 8;
            animation: dashFlow 0.8s linear infinite;
        }
        
        @keyframes dashFlow {
            to { stroke-dashoffset: -16; }
        }
        
        .link-arrow {
            fill: #7c3aed;
        }
        
        #legend {
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 160px;
            background: rgba(15, 15, 25, 0.95);
            padding: 12px 14px;
            border-radius: 14px;
            border: 1px solid rgba(100, 100, 150, 0.2);
            font-size: 13px;
            transition: width 0.2s ease, padding 0.2s ease;
        }
        #legend.detailed-open {
            width: 260px;
            padding: 18px 12px 18px 18px;
        }
        .legend-simple {
            display: block;
        }
        #legend.detailed-open .legend-simple {
            display: none;
        }
        .legend-detailed {
            display: none;
            margin-top: 12px;
        }
        #legend.detailed-open .legend-detailed {
            display: block;
        }
        .legend-simple-grid {
            display: grid;
            grid-template-columns: 32px 1fr;
            gap: 6px 10px;
            align-items: center;
        }
        .legend-simple-grid .legend-icon { width: 28px; }
        .legend-simple-grid .legend-folder-node { width: 20px; height: 20px; }
        .legend-simple-grid .legend-circle { width: 14px; height: 14px; }
        .legend-simple-grid .legend-arrow { width: 40px; height: 14px; }
        .legend-simple-grid .legend-name {
            font-weight: 600;
            color: #e7e7ee;
            font-size: 12px;
            line-height: 1.2;
        }
        .legend-expand-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: auto;
            height: auto;
            padding: 2px;
            margin-left: auto;
            border: none;
            background: transparent;
            color: #8b8b95;
            cursor: pointer;
            flex-shrink: 0;
            transition: color 0.2s ease, opacity 0.2s ease;
        }
        .legend-expand-btn:hover {
            color: #e7e7ee;
            opacity: 0.9;
        }
        .legend-expand-btn .legend-icon-collapse {
            display: none;
        }
        #legend.detailed-open .legend-expand-btn .legend-icon-expand {
            display: none;
        }
        #legend.detailed-open .legend-expand-btn .legend-icon-collapse {
            display: block;
        }
        .legend-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 10px;
            user-select: none;
        }
        .legend-title {
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #8b8b95;
            margin: 0;
        }
        .legend-section { margin-bottom: 14px; }
        .legend-divider {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(100,100,150,0.2);
        }
        .legend-section-title {
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 10px;
        }
        .legend-grid {
            display: grid;
            grid-template-columns: 44px 1fr;
            gap: 10px 12px;
            align-items: center;
        }
        .legend-icon {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .legend-label .legend-name {
            font-weight: 600;
            color: #e7e7ee;
            line-height: 1.1;
        }
        .legend-caption,
        .legend-caption-top {
            font-size: 11px;
            color: #7b7b87;
            line-height: 1.3;
        }
        .legend-caption-top {
            margin: -2px 0 10px;
            max-width: 200px;
        }
        .legend-circle {
            width: 18px;
            height: 18px;
            border-radius: 50%;
        }
        .legend-folder-node {
            width: 24px;
            height: 24px;
            filter: drop-shadow(0 0 10px rgba(124,58,237,0.15));
        }
        .legend-folder-node circle { fill: #7c3aed; }
        .legend-arrow {
            width: 52px;
            height: 16px;
            display: block;
        }
        .legend-arrow line { fill: none; stroke-width: 2; stroke-dasharray: 8 8; }
        .legend-layer-swatch {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px dashed rgba(180,180,220,0.55);
            background: rgba(124,58,237,0.10);
        }

        
        #help {
            position: fixed;
            bottom: 20px;
            right: 400px;
            background: rgba(15, 15, 25, 0.95);
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid rgba(100, 100, 150, 0.2);
            font-size: 11px;
            color: #666;
        }
        
        .help-key {
            display: inline-block;
            background: rgba(100, 100, 150, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            margin: 0 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .placeholder {
            color: #444;
            font-style: italic;
            padding: 40px;
            text-align: center;
        }
        
        .empty-state {
            color: #555;
            font-size: 12px;
            padding: 12px;
            text-align: center;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>⬡ Codescape</h1>
        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item" onclick="navigateTo('', true)">''' + data['rootName'] + '''</span>
        </div>
    </div>
    
    <div id="graph-container">
        <svg id="graph">
            <defs>
                <linearGradient id="folderSilverGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#e8eef4;stop-opacity:1" />
                    <stop offset="40%" style="stop-color:#c8d4e0;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#a0b0c4;stop-opacity:1" />
                </linearGradient>
                <filter id="folder-glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="1.5" result="blur"/>
                    <feOffset in="blur" dx="0" dy="0" result="offsetBlur"/>
                    <feFlood flood-color="#ffffff" flood-opacity="0.7" result="color"/>
                    <feComposite in="color" in2="offsetBlur" operator="in" result="glow"/>
                    <feMerge>
                        <feMergeNode in="glow"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
                <symbol id="folder-icon" viewBox="0 0 24 24">
                    <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" fill="url(#folderSilverGrad)" filter="url(#folder-glow)"/>
                </symbol>
                <symbol id="file-icon" viewBox="0 0 24 24">
                    <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" fill="url(#folderSilverGrad)" filter="url(#folder-glow)"/>
                </symbol>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#06b6d4"/>
                </marker>
                <marker id="arrowhead-inbound" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e"/>
                </marker>
                <marker id="arrowhead-outbound" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#f59e0b"/>
                </marker>
            </defs>
        </svg>
    </div>
    
    <div id="sidebar">
        <div id="details-panel">
            <div class="details-placeholder">Click a node to view its details</div>
        </div>
    </div>
    
    <div id="legend">
  <div class="legend-header">
    <span class="legend-title">Key</span>
    <button type="button" class="legend-expand-btn" id="legend-expand-btn" title="Expand key">
        <svg class="legend-icon-expand" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M0 0 L8 0 M0 0 L0 8"/><path d="M24 0 L16 0 M24 0 L24 8"/><path d="M24 24 L16 24 M24 24 L24 16"/><path d="M0 24 L0 16 M0 24 L8 24"/></svg>
        <svg class="legend-icon-collapse" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6 L0 6 M6 6 L6 0"/><path d="M18 6 L24 6 M18 6 L18 0"/><path d="M18 18 L24 18 M18 18 L18 24"/><path d="M6 18 L0 18 M6 18 L6 24"/></svg>
      </button>
  </div>
  <div class="legend-simple">
    <div class="legend-simple-grid">
      <div class="legend-icon">
        <svg class="legend-folder-node" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15"></circle>
          <use href="#folder-icon" x="8" y="8" width="20" height="20"></use>
        </svg>
      </div>
      <div class="legend-name">Folder node</div>
      <div class="legend-icon">
        <div class="legend-circle" id="legend-file-circle"></div>
      </div>
      <div class="legend-name">File node</div>
      <div class="legend-icon">
        <svg class="legend-arrow" viewBox="0 0 52 16">
          <line x1="0" y1="8" x2="44" y2="8" stroke="#22c55e" marker-end="url(#arrowhead-inbound)"></line>
        </svg>
      </div>
      <div class="legend-name">Inbound</div>
      <div class="legend-icon">
        <svg class="legend-arrow" viewBox="0 0 52 16">
          <line x1="0" y1="8" x2="44" y2="8" stroke="#f59e0b" marker-end="url(#arrowhead-outbound)"></line>
        </svg>
      </div>
      <div class="legend-name">Outbound</div>
    </div>
  </div>
  <div class="legend-detailed legend-body">
  <div class="legend-section">
    <div class="legend-section-title">Nodes</div>
    <div class="legend-caption-top">Node size: PageRank-derived importance.</div>
    <div class="legend-grid">
      <div class="legend-icon">
        <svg class="legend-folder-node" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15"></circle>
          <use href="#folder-icon" x="8" y="8" width="20" height="20"></use>
        </svg>
      </div>
      <div class="legend-label">
        <div class="legend-name">Folder node</div>
        <div class="legend-caption">Click to open</div>
      </div>

      <div class="legend-icon">
        <div class="legend-circle" id="legend-file-circle-detail"></div>
      </div>
      <div class="legend-label">
        <div class="legend-name">File node</div>
        <div class="legend-caption">Select to show deps</div>
      </div>
    </div>
  </div>

  <div class="legend-section legend-divider">
    <div class="legend-section-title">Dependencies</div>
    <div class="legend-caption-top">A → B means A depends on B. Arrows show when a file is selected.</div>
    <div class="legend-grid">
      <div class="legend-icon">
        <svg class="legend-arrow" viewBox="0 0 52 16">
          <line x1="0" y1="8" x2="44" y2="8" stroke="#22c55e" marker-end="url(#arrowhead-inbound)"></line>
        </svg>
      </div>
      <div class="legend-label">
        <div class="legend-name">Inbound</div>
        <div class="legend-caption">Files that import this file</div>
      </div>

      <div class="legend-icon">
        <svg class="legend-arrow" viewBox="0 0 52 16">
          <line x1="0" y1="8" x2="44" y2="8" stroke="#f59e0b" marker-end="url(#arrowhead-outbound)"></line>
        </svg>
      </div>
      <div class="legend-label">
        <div class="legend-name">Outbound</div>
        <div class="legend-caption">Files this file imports</div>
      </div>
    </div>
  </div>
  </div>
</div>

    <div id="help">
        <span class="help-key">Scroll</span> zoom
        <span class="help-key">Drag</span> pan
        <span class="help-key">Click</span> select & show deps
    </div>

    <script>
        const graphData = ''' + json.dumps(data) + ''';
        
        // Build lookup maps
        const nodesById = new Map(graphData.nodes.map(n => [n.id, n]));
        const linksMap = new Map(); // source -> target -> link
        graphData.links.forEach(l => {
            if (!linksMap.has(l.source)) linksMap.set(l.source, new Map());
            linksMap.get(l.source).set(l.target, l);
        });
        
        let currentPath = '';
        let selectedNode = null;
        let simulation = null;
        let folderCountMode = 'direct';  // 'direct' | 'recursive'

        const FILE_CYAN = '#06b6d4';
        const maxMetrics = graphData.maxMetrics;

        document.getElementById('legend-file-circle').style.background = FILE_CYAN;
        var detailCircle = document.getElementById('legend-file-circle-detail');
        if (detailCircle) detailCircle.style.background = FILE_CYAN;

        document.getElementById('legend-expand-btn').addEventListener('click', function () {
            var legend = document.getElementById('legend');
            legend.classList.toggle('detailed-open');
            this.setAttribute('title', legend.classList.contains('detailed-open') ? 'Collapse key' : 'Expand key');
        });

        const width = document.getElementById('graph-container').clientWidth;
        const height = document.getElementById('graph-container').clientHeight;
        
        const svg = d3.select('#graph')
            .attr('viewBox', [0, 0, width, height]);
            
        const g = svg.append('g');
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
            
        svg.call(zoom);
        
        // Click on background to deselect
        svg.on('click', () => {
            selectedNode = null;
            updateBreadcrumb();
            updateSelection();
            renderSidePanel();
        });
        
        function getNodeColor(node) {
            if (node.type === 'folder') return '#7c3aed';
            return FILE_CYAN;
        }

        function getNodeSize(node) {
            const value = Math.max(node.pagerank || 0, 0.01);
            const maxValue = Math.max(maxMetrics.pagerank || 1, 0.01);
            const normalized = Math.sqrt(value) / Math.sqrt(maxValue);
            // Linear mapping so size differences are obvious: radius 6 (low) to 50 (high)
            const radius = 6 + normalized * 44;
            return Math.max(6, Math.min(50, radius));
        }
        
        function navigateTo(path, clearPanel) {
            if (clearPanel) selectedNode = null;
            currentPath = path;
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
        }
        
        function focusFile(path) {
            const parts = path.split('/');
            parts.pop();
            const parentPath = parts.join('/');
            currentPath = parentPath;
            selectedNode = nodesById.get(path) || null;
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
        }
        function clearSelection() {
            selectedNode = null;
            updateBreadcrumb();
            updateSelection();
            renderSidePanel();
        }
        
        function updateBreadcrumb() {
            const parts = currentPath ? currentPath.split('/') : [];
            let html = `<span class="breadcrumb-item" onclick="navigateTo('', true)">${graphData.rootName}</span>`;
            
            let accumulated = '';
            for (const part of parts) {
                accumulated += (accumulated ? '/' : '') + part;
                const p = accumulated;
                html += `<span class="breadcrumb-sep">/</span>`;
                html += `<span class="breadcrumb-item" onclick="navigateTo('${p}', true)">${escapeAttr(part)}</span>`;
            }
            if (selectedNode && selectedNode.type !== 'folder') {
                html += `<span class="breadcrumb-sep">/</span><span class="breadcrumb-file">${escapeAttr(selectedNode.name)}</span>`;
            }
            
            document.getElementById('breadcrumb').innerHTML = html;
        }
        
        function renderGraph() {
            g.selectAll('*').remove();
            
            // Get current folder
            const currentFolder = nodesById.get(currentPath || 'root');
            if (!currentFolder || !currentFolder.children) return;
            
            // Get visible nodes (children of current folder)
            const visibleNodeIds = new Set(currentFolder.children);
            const visibleNodes = graphData.nodes.filter(n => visibleNodeIds.has(n.id) || visibleNodeIds.has(n.path));
            
            // Get ALL links for visible nodes (we'll show/hide based on selection)
            const visibleLinks = graphData.links.filter(l => 
                (visibleNodeIds.has(l.source) || visibleNodeIds.has(l.source?.id)) &&
                (visibleNodeIds.has(l.target) || visibleNodeIds.has(l.target?.id))
            );
            
            if (visibleNodes.length === 0) {
                g.append('text')
                    .attr('x', width / 2)
                    .attr('y', height / 2)
                    .attr('text-anchor', 'middle')
                    .attr('fill', '#666')
                    .text('Empty folder');
                return;
            }
            
            // Create force simulation
            simulation = d3.forceSimulation(visibleNodes)
                .force('link', d3.forceLink(visibleLinks).id(d => d.id).distance(120).strength(0.3))
                .force('charge', d3.forceManyBody().strength(-400))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 25));
            
            // Draw links (initially hidden, shown based on selection)
            const link = g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(visibleLinks)
                .join('line')
                .attr('class', d => `link ${d.type}`)
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');
            
            // Draw nodes
            const node = g.append('g')
                .attr('class', 'nodes')
                .selectAll('g')
                .data(visibleNodes)
                .join('g')
                .attr('class', d => `node ${selectedNode && d.id === selectedNode.id ? 'selected' : ''}`)
                .attr('data-id', d => d.id)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended))
                .on('click', (event, d) => {
                    event.stopPropagation();
                    selectedNode = d;
                    if (d.type === 'folder') {
                        navigateTo(d.path || d.id);
                    } else {
                        updateBreadcrumb();
                        updateSelection();
                        renderSidePanel();
                    }
                });
            
            node.append('circle')
                .attr('r', d => getNodeSize(d))
                .attr('fill', d => getNodeColor(d))
                .attr('stroke', d => d3.color(getNodeColor(d))?.darker(0.5) || '#333');
            
            node.append('text')
                .attr('dy', d => getNodeSize(d) + 14)
                .attr('text-anchor', 'middle')
                .text(d => d.name.length > 20 ? d.name.slice(0, 18) + '...' : d.name);
            
            // Folder icon: glassy silver icon centered in node (scale then translate so symbol center 12,12 lands at 0,0)
            node.filter(d => d.type === 'folder')
                .append('g')
                .attr('class', 'folder-icon')
                .attr('transform', d => {
                    const s = (1.2 * getNodeSize(d)) / 24;
                    const tx = -12 * s;
                    const ty = -12 * s;
                    return `translate(${tx},${ty}) scale(${s})`;
                })
                .append('use')
                .attr('href', '#folder-icon')
                .attr('x', 0)
                .attr('y', 0)
                .attr('width', 24)
                .attr('height', 24);
            
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => {
                        // Shorten line to not overlap with target node
                        const dx = d.target.x - d.source.x;
                        const dy = d.target.y - d.source.y;
                        const dist = Math.sqrt(dx*dx + dy*dy);
                        const targetR = getNodeSize(d.target);
                        return d.target.x - (dx/dist) * (targetR + 5);
                    })
                    .attr('y2', d => {
                        const dx = d.target.x - d.source.x;
                        const dy = d.target.y - d.source.y;
                        const dist = Math.sqrt(dx*dx + dy*dy);
                        const targetR = getNodeSize(d.target);
                        return d.target.y - (dy/dist) * (targetR + 5);
                    });
                
                node.attr('transform', d => `translate(${d.x},${d.y})`);
            });
            
            // Restore selection visual state
            updateSelection();
            
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
        }
        
        function updateSelection() {
            const sid = selectedNode ? selectedNode.id : null;
            const isFileSelected = selectedNode && selectedNode.type !== 'folder';
            g.selectAll('.node')
                .classed('selected', d => d.id === sid);
            g.selectAll('.link')
                .classed('visible', d => {
                    if (!sid || !isFileSelected) return false;
                    const sourceId = d.source.id || d.source;
                    const targetId = d.target.id || d.target;
                    return sourceId === sid || targetId === sid;
                })
                .classed('inbound', d => isFileSelected && (d.target.id || d.target) === sid)
                .classed('outbound', d => isFileSelected && (d.source.id || d.source) === sid)
                .classed('dep-arrow', isFileSelected)
                .attr('marker-end', d => {
                    if (!isFileSelected) return 'url(#arrowhead)';
                    const sourceId = d.source.id || d.source;
                    const targetId = d.target.id || d.target;
                    if (targetId === sid) return 'url(#arrowhead-inbound)';
                    if (sourceId === sid) return 'url(#arrowhead-outbound)';
                    return 'url(#arrowhead)';
                });
        }

        function escapeAttr(s) {
            return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }
        function escJs(s) {
            return String(s).replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'");
        }

        function setFolderCountMode(mode) {
            folderCountMode = mode;
            renderSidePanel();
        }

        function getCardHTML(node) {
            const esc = escapeAttr;
            if (node.type === 'folder') {
                return `
                    <div class="sidebar-section" data-node-id="${esc(node.id)}">
                        <div class="sidebar-title">
                            <span>Folder</span>
                            <button type="button" class="card-remove" onclick="clearSelection()" aria-label="Clear">×</button>
                        </div>
                        <div class="file-info">
                            <div class="file-name"><svg class="sidebar-icon" viewBox="0 0 24 24"><use href="#folder-icon"/></svg><span>${esc(node.name)}</span></div>
                            <div class="file-path">${esc(node.path || '/')}</div>
                            <div class="folder-count-toggle">
                                <button type="button" class="${folderCountMode === 'direct' ? 'active' : ''}" onclick="setFolderCountMode('direct')">Direct</button>
                                <button type="button" class="${folderCountMode === 'recursive' ? 'active' : ''}" onclick="setFolderCountMode('recursive')">Recursive</button>
                            </div>
                            <div class="file-meta">
                                <div class="meta-item">
                                    <div class="meta-label" style="color:#7c3aed">Subfolders</div>
                                    <div class="meta-value" style="color:#7c3aed">${folderCountMode === 'direct' ? (node.subfolderCount ?? 0) : (node.recursiveSubfolderCount ?? 0)}</div>
                                </div>
                                ${(node.fileCount ?? 0) > 0 ? `
                                <div class="meta-item">
                                    <div class="meta-label" style="color:#06b6d4">Files</div>
                                    <div class="meta-value" style="color:#06b6d4">${folderCountMode === 'direct' ? (node.directFileCount ?? 0) : (node.fileCount ?? 0)}</div>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }
            const dependents = node.dependents || [];
            const dependencies = node.dependencies || [];
            const imports = node.imports || [];
            return `
                <div class="sidebar-section" data-node-id="${esc(node.id)}">
                    <div class="sidebar-title">
                        <span>File</span>
                        <button type="button" class="card-remove" onclick="clearSelection()" aria-label="Clear">×</button>
                    </div>
                    <div class="file-info">
                        <div class="file-name"><svg class="sidebar-icon" viewBox="0 0 24 24"><use href="#file-icon"/></svg><span>${esc(node.name)}</span></div>
                        <div class="file-path">${esc(node.path)}</div>
                        <div class="file-meta four-col">
                            <div class="meta-item">
                                <div class="meta-label">Language</div>
                                <div class="meta-value file">${esc(node.language || '')}</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Lines</div>
                                <div class="meta-value file">${node.loc != null ? node.loc.toLocaleString() : 0}</div>
                            </div>
                            <div class="meta-item highlight-inbound">
                                <div class="meta-label">Fan-In</div>
                                <div class="meta-value">${node.fanIn ?? 0}</div>
                            </div>
                            <div class="meta-item highlight-outbound">
                                <div class="meta-label">Fan-Out</div>
                                <div class="meta-value">${node.fanOut ?? 0}</div>
                            </div>
                        </div>
                        ${dependents.length > 0 ? `
                            <div class="deps-section">
                                <div class="deps-title">
                                    <span style="color:#22c55e">⬅</span>
                                    Files that import this (<span class="count">${dependents.length}</span>)
                                </div>
                                ${dependents.slice(0, 8).map(d => `
                                    <div class="dep-item inbound" onclick="focusFile('${escJs(d)}')">
                                        <span class="arrow">⬅</span>
                                        <span class="name" title="${esc(d)}">${esc(d.split('/').pop())}</span>
                                    </div>
                                `).join('')}
                                ${dependents.length > 8 ? `<div class="empty-state">+${dependents.length - 8} more</div>` : ''}
                            </div>
                        ` : ''}
                        ${dependencies.length > 0 ? `
                            <div class="deps-section">
                                <div class="deps-title">
                                    <span style="color:#f59e0b">➡</span>
                                    Files this imports (<span class="count">${dependencies.length}</span>)
                                </div>
                                ${dependencies.slice(0, 8).map(d => `
                                    <div class="dep-item outbound" onclick="focusFile('${escJs(d)}')">
                                        <span class="arrow">➡</span>
                                        <span class="name" title="${esc(d)}">${esc(d.split('/').pop())}</span>
                                    </div>
                                `).join('')}
                                ${dependencies.length > 8 ? `<div class="empty-state">+${dependencies.length - 8} more</div>` : ''}
                            </div>
                        ` : ''}
                        ${imports.length > 0 && dependencies.length === 0 ? `
                            <div class="imports-list">
                                <div class="imports-title">Raw Imports (${imports.length})</div>
                                ${imports.slice(0, 10).map(i => `<div class="import-item">${esc(i)}</div>`).join('')}
                                ${imports.length > 10 ? `<div class="empty-state">...and ${imports.length - 10} more</div>` : ''}
                            </div>
                        ` : ''}
                        ${dependents.length === 0 && dependencies.length === 0 ? `
                            <div class="empty-state" style="margin-top: 16px;">
                                No resolved dependencies in this view.
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        function renderSidePanel() {
            const panel = document.getElementById('details-panel');
            if (selectedNode) {
                panel.innerHTML = getCardHTML(selectedNode);
                return;
            }
            if (currentPath) {
                const folderNode = nodesById.get(currentPath);
                if (folderNode) {
                    panel.innerHTML = getCardHTML(folderNode);
                    return;
                }
            }
            const s = graphData.stats || {};
            const loc = (s.totalLoc != null) ? s.totalLoc.toLocaleString() : '0';
            panel.innerHTML = `
                <div class="details-repo-stats">
                    <div class="stats-title">Repository</div>
                    <div class="stat"><span>Files</span><span class="stat-value">${s.totalFiles ?? 0}</span></div>
                    <div class="stat"><span>Dependencies</span><span class="stat-value">${s.totalDependencies ?? 0}</span></div>
                    <div class="stat"><span>Lines of code</span><span class="stat-value">${loc}</span></div>
                </div>
            `;
        }
        
        // Initial render
        renderGraph();
    </script>
</body>
</html>'''
    
    return html