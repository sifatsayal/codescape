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
            background: #0d0d12;
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
            cursor: pointer;
            transition: color 0.2s;
        }
        .breadcrumb-folder {
            color: #6b7280;
        }
        .breadcrumb-folder:hover {
            color: #6b7280;
        }
        .breadcrumb-sep {
            color: #6b7280;
        }
        .breadcrumb-file {
            color: #06b6d4;
        }

        .search-clear-btn {
            position: absolute;
            top: 50%;
            right: 8px;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            border-radius: 999px;
            border: none;
            background: transparent;
            color: #6b7280;
            cursor: pointer;
            font-size: 13px;
            line-height: 1;
            padding: 0;
        }
        .search-clear-btn:hover {
            color: #e5e7eb;
            background: rgba(55, 65, 81, 0.6);
        }
        .search-clear-btn:focus-visible {
            outline: 2px solid #06b6d4;
            outline-offset: 1px;
        }
        .header-tour-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 500;
            color: #a78bfa;
            background: transparent;
            border: 1px solid rgba(124, 58, 237, 0.5);
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s, color 0.2s, box-shadow 0.2s;
            box-shadow: 0 0 12px rgba(124, 58, 237, 0.25);
        }
        .header-tour-btn:hover {
            background: rgba(124, 58, 237, 0.2);
            color: #e0e0e0;
            box-shadow: 0 0 16px rgba(124, 58, 237, 0.4);
        }
        .search-results {
            position: absolute;
            top: 30px;
            left: 0;
            right: 0;
            max-height: 260px;
            overflow-y: auto;
            margin-top: 6px;
            padding: 6px 0;
            background: rgba(12, 12, 22, 0.98);
            border-radius: 8px;
            border: 1px solid rgba(100, 100, 150, 0.4);
            box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6);
            z-index: 120;
            display: none;
        }
        .node-tooltip {
            position: fixed;
            max-width: 280px;
            background: rgba(15, 15, 25, 0.97);
            color: #e5e7eb;
            border-radius: 8px;
            border: 1px solid rgba(100, 100, 150, 0.5);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
            padding: 8px 10px;
            font-size: 11px;
            z-index: 160;
            pointer-events: auto;
            line-height: 1.35;
        }
        .node-tooltip-header {
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 2px;
            color: #e5e7eb;
        }
        .node-tooltip-type-path {
            font-size: 10px;
            color: #9ca3af;
            margin-bottom: 6px;
            font-family: 'JetBrains Mono', monospace;
            word-break: break-all;
        }
        .node-tooltip-meta-row {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            font-size: 10px;
            color: #9ca3af;
        }
        .node-tooltip-meta-row + .node-tooltip-meta-row {
            margin-top: 1px;
        }
        .node-tooltip-divider {
            margin: 5px 0;
            height: 1px;
            background: rgba(55, 65, 81, 0.9);
        }
        .node-tooltip-summary {
            font-size: 11px;
            color: #d1d5db;
            line-height: 1.3;
            word-wrap: break-word;
        }
        .node-tooltip-summary-loading {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 10px;
            color: #9ca3af;
        }
        .node-tooltip-spinner {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            border: 2px solid #4b5563;
            border-top-color: #e5e7eb;
            animation: nodeTooltipSpin 0.8s linear infinite;
        }
        @keyframes nodeTooltipSpin {
            to { transform: rotate(360deg); }
        }
        .search-result-item {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 6px 10px;
            cursor: pointer;
            font-size: 12px;
        }
        .search-result-item:hover {
            background: rgba(37, 99, 235, 0.35);
        }
        .search-result-icon {
            font-size: 13px;
            margin-top: 2px;
        }
        .search-result-text {
            flex: 1;
            min-width: 0;
        }
        .search-result-name {
            color: #e5e7eb;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .search-result-path {
            color: #9ca3af;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .search-result-meta {
            margin-top: 2px;
            color: #6b7280;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        #graph-container {
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            bottom: 0;
            background: #0a0a12;
        }

        #right-rail {
            position: fixed;
            top: 60px;
            right: 0;
            bottom: 0;
            display: flex;
            flex-direction: row-reverse;
            align-items: stretch;
            z-index: 30;
            pointer-events: none;
        }
        #right-rail > * { pointer-events: auto; }
        .panel-toggle-btns {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 12px 8px;
            background: rgba(15, 15, 25, 0.95);
            border-left: 1px solid rgba(100, 100, 150, 0.2);
            align-items: center;
        }
        .panel-toggle-btn {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: none;
            border-radius: 10px;
            background: rgba(100, 100, 150, 0.2);
            color: #9ca3af;
            cursor: pointer;
            transition: background 0.2s, color 0.2s, transform 0.15s;
        }
        .panel-toggle-btn:hover {
            background: rgba(124, 58, 237, 0.3);
            color: #e0e0e0;
        }
        .panel-toggle-btn.active {
            background: rgba(124, 58, 237, 0.4);
            color: #c4b5fd;
        }
        .panel-toggle-btn svg {
            width: 22px;
            height: 22px;
        }
        #file-info-panel, #changes-panel, #search-panel {
            width: 0;
            overflow: hidden;
            transition: width 0.25s ease;
            background: rgba(15, 15, 25, 0.98);
            border-left: 1px solid rgba(100, 100, 150, 0.2);
            display: flex;
            flex-direction: column;
        }
        #file-info-panel.open, #changes-panel.open, #search-panel.open {
            width: 380px;
        }
        #file-info-panel .panel-inner, #changes-panel .panel-inner, #search-panel .panel-inner {
            width: 380px;
            min-width: 380px;
            height: 100%;
            overflow-y: auto;
            padding: 16px;
        }
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: #e5e7eb;
            text-align: center;
            margin: 0 0 14px 0;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(100, 100, 150, 0.2);
        }
        .search-panel-search {
            position: relative;
            margin-bottom: 12px;
        }
        .search-panel-search input {
            width: 100%;
            box-sizing: border-box;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 8px 28px 8px 10px;
            border-radius: 6px;
            border: 1px solid rgba(100, 100, 150, 0.3);
            background: rgba(20, 20, 35, 0.9);
            color: #e0e0e0;
        }
        .search-panel-search input::placeholder { color: #666; }
        .search-panel-search input:focus {
            outline: none;
            border-color: #06b6d4;
            box-shadow: 0 0 0 1px rgba(6, 182, 212, 0.6);
        }
        .search-panel-search .search-clear-btn {
            position: absolute;
            top: 50%;
            right: 8px;
            transform: translateY(-50%);
        }
        #search-panel .search-results {
            position: static;
            margin-top: 0;
            max-height: min(400px, 50vh);
            border-radius: 6px;
        }
        #file-info-panel.tour-sidebar-highlight .panel-inner {
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.6), 0 0 24px rgba(124, 58, 237, 0.4);
            animation: tour-sidebar-glow 1.5s ease-in-out infinite;
        }
        @keyframes tour-sidebar-glow {
            0%, 100% { box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.6), 0 0 24px rgba(124, 58, 237, 0.4); }
            50% { box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.9), 0 0 32px rgba(124, 58, 237, 0.6); }
        }
        .sidebar-nav {
            display: flex;
            align-items: center;
            gap: 4px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(100, 100, 150, 0.2);
        }
        .sidebar-nav-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 28px;
            padding: 0;
            border: none;
            border-radius: 6px;
            background: rgba(100, 100, 150, 0.2);
            color: #888;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .sidebar-nav-btn:hover:not(:disabled) {
            background: rgba(124, 58, 237, 0.3);
            color: #e0e0e0;
        }
        .sidebar-nav-btn:disabled {
            opacity: 0.4;
            cursor: default;
        }
        .sidebar-nav-btn svg {
            width: 16px;
            height: 16px;
        }
        .sidebar-section {
            margin-bottom: 20px;
        }
        .sidebar-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #9ca3af;
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
        .recent-changes-panel {
            padding-top: 0;
        }
        #changes-panel .panel-inner .recent-changes-panel {
            margin-top: 0;
        }
        .recent-changes-panel.tour-changes-highlight {
            border: 3px solid #06b6d4;
            border-radius: 10px;
            padding: 16px;
            margin-top: 24px;
            box-shadow: 0 0 0 3px #06b6d4, 0 0 20px #06b6d4;
            animation: tour-changes-glow 1.2s ease-in-out infinite;
        }
        @keyframes tour-changes-glow {
            0%, 100% { box-shadow: 0 0 0 3px #06b6d4, 0 0 20px #06b6d4; border-color: #06b6d4; }
            50% { box-shadow: 0 0 0 4px #06b6d4, 0 0 32px #06b6d4, 0 0 48px rgba(6, 182, 212, 0.5); border-color: #22d3ee; }
        }
        .recent-changes-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #9ca3af;
            margin-bottom: 8px;
        }
        .recent-changes-muted, .recent-changes-list {
            color: #9ca3af;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.5;
        }
        .last-save-box {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            color: #e5e7eb;
            background: rgba(107, 114, 128, 0.25);
            border: 1px solid rgba(107, 114, 128, 0.35);
        }
        .last-save-box.recent {
            background: rgba(234, 179, 8, 0.25);
            border-color: rgba(234, 179, 8, 0.5);
            color: #fef08a;
        }
        .recent-changes-list {
            max-height: 200px;
            overflow-y: auto;
        }
        .recent-changes-list .change-line {
            margin-bottom: 4px;
            word-break: break-all;
        }
        .recent-changes-git-section {
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid rgba(100, 100, 150, 0.2);
        }
        .recent-changes-git-section .recent-changes-title {
            margin-bottom: 6px;
        }
        .git-status-line {
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 4px;
            word-break: break-all;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .git-status-badge {
            flex-shrink: 0;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .git-status-badge.modified { background: rgba(245, 158, 11, 0.25); color: #fbbf24; }
        .git-status-badge.added { background: rgba(34, 197, 94, 0.25); color: #4ade80; }
        .git-status-badge.deleted { background: rgba(239, 68, 68, 0.25); color: #f87171; }
        .git-status-badge.renamed { background: rgba(59, 130, 246, 0.25); color: #60a5fa; }
        .git-status-ai-btn {
            font-size: 10px;
            padding: 3px 8px;
            border: 1px solid rgba(59, 130, 246, 0.5);
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 6px;
            flex-shrink: 0;
        }
        .git-status-ai-btn:hover { background: rgba(59, 130, 246, 0.35); }
        .git-status-ai-summary {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 6px;
            padding: 8px;
            background: rgba(20, 20, 35, 0.6);
            border-radius: 6px;
            border-left: 2px solid #60a5fa;
        }
        .change-line-with-desc {
            margin-bottom: 12px;
        }
        .change-line-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 2px;
        }
        .change-line-with-desc .change-line-text {
            flex: 1;
            min-width: 0;
            font-weight: 500;
            color: #e5e7eb;
            word-break: break-all;
        }
        .change-desc-toggle {
            flex-shrink: 0;
            width: 22px;
            height: 22px;
            padding: 0;
            border: none;
            background: none;
            color: #9ca3af;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .change-desc-toggle:hover {
            color: #d1d5db;
        }
        .change-desc-toggle:disabled {
            opacity: 0.7;
            cursor: wait;
        }
        .change-description {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 6px;
            padding: 8px;
            background: rgba(20, 20, 35, 0.6);
            border-radius: 6px;
            border-left: 2px solid #6b7280;
            line-height: 1.4;
        }
        .details-placeholder {
            color: #888;
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
            color: #9ca3af;
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
            color: #d1d5db;
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
        .file-name span {
            color: #9ca3af;
        }
        .file-name-folder span {
            color: #6b7280;
        }
        .sidebar-icon {
            flex-shrink: 0;
            width: 22px;
            height: 22px;
        }
        
        .file-path {
            font-size: 12px;
            color: #9ca3af;
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
            flex-wrap: wrap;
        }
        
        .deps-title .count {
            color: #22c55e;
            font-weight: 600;
        }
        .deps-section.outbound .deps-title .count {
            color: #f59e0b;
        }
        
        .deps-title-info {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            padding: 0;
            border: none;
            border-radius: 50%;
            background: rgba(100, 100, 150, 0.3);
            color: #888;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .deps-title-info:hover {
            background: rgba(124, 58, 237, 0.3);
            color: #a78bfa;
        }
        .deps-tooltip {
            display: none;
            width: 100%;
            margin-top: 6px;
            padding: 10px 12px;
            font-size: 11px;
            line-height: 1.4;
            color: #aaa;
            background: rgba(20, 20, 35, 0.95);
            border: 1px solid rgba(100, 100, 150, 0.25);
            border-radius: 8px;
        }
        .deps-tooltip.show {
            display: block;
        }
        .deps-tooltip .filename {
            color: #06b6d4;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
        }
        
        .ai-summary-section {
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid rgba(100, 100, 150, 0.2);
        }
        .ai-summary-section.tour-ai-summary-highlight {
            border: 3px solid #06b6d4;
            border-radius: 10px;
            padding: 14px;
            margin-top: 20px;
            margin-left: -3px;
            margin-right: -3px;
            box-shadow: 0 0 0 3px #06b6d4, 0 0 20px #06b6d4;
            animation: tour-ai-summary-glow 1.2s ease-in-out infinite;
        }
        @keyframes tour-ai-summary-glow {
            0%, 100% { box-shadow: 0 0 0 3px #06b6d4, 0 0 20px #06b6d4; border-color: #06b6d4; }
            50% { box-shadow: 0 0 0 4px #06b6d4, 0 0 32px #06b6d4, 0 0 48px rgba(6, 182, 212, 0.5); border-color: #22d3ee; }
        }
        .ai-summary-section .sidebar-title {
            margin-bottom: 10px;
        }
        .ai-summary-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 12px;
        }
        .ai-summary-tab {
            padding: 6px 10px;
            font-size: 11px;
            border: none;
            border-radius: 6px;
            background: rgba(100, 100, 150, 0.2);
            color: #9ca3af;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .ai-summary-tab:hover {
            background: rgba(124, 58, 237, 0.25);
            color: #e0e0e0;
        }
        .ai-summary-tab.active {
            background: #7c3aed;
            color: #fff;
        }
        .ai-summary-content {
            min-height: 60px;
            font-size: 12px;
            line-height: 1.5;
            color: #d1d5db;
            background: rgba(20, 20, 35, 0.5);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid rgba(100, 100, 150, 0.2);
        }
        .ai-summary-loading {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #9ca3af;
        }
        .ai-summary-loading::before {
            content: '';
            width: 18px;
            height: 18px;
            border: 2px solid rgba(124, 58, 237, 0.4);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: ai-summary-spin 0.8s linear infinite;
        }
        @keyframes ai-summary-spin {
            to { transform: rotate(360deg); }
        }
        .ai-summary-text {
            white-space: pre-wrap;
            word-break: break-word;
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
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }
        
        .dep-item:hover {
            background: rgba(124, 58, 237, 0.2);
            color: #e0e0e0;
        }
        
        .dep-item .dep-item-icon {
            font-size: 12px;
            flex-shrink: 0;
        }
        
        .dep-item.inbound .dep-item-icon {
            color: #22c55e;
        }
        
        .dep-item.outbound .dep-item-icon {
            color: #f59e0b;
        }
        
        .dep-item.dep-item-outside .dep-item-icon {
            color: #a855f7;
        }
        
        .dep-item.dep-item-outside.inbound .dep-item-icon,
        .dep-item.dep-item-outside.outbound .dep-item-icon {
            color: #a855f7;
        }
        
        .dep-item .name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .dep-item.inbound .name {
            color: #22c55e;
        }
        
        .dep-item.outbound .name {
            color: #f59e0b;
        }
        
        .dep-item-location-wrap {
            display: flex;
            align-items: center;
            margin-left: auto;
            flex-shrink: 0;
        }
        
        .dep-item-path-toggle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            padding: 0;
            border: none;
            border-radius: 4px;
            background: rgba(100, 100, 150, 0.25);
            color: #a78bfa;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
        }
        .dep-item-path-toggle:hover {
            background: rgba(124, 58, 237, 0.4);
            color: #e0e0e0;
        }
        .dep-item-path-toggle svg {
            width: 12px;
            height: 12px;
        }
        .dep-item-path-toggle-chevron {
            display: inline-block;
            font-size: 8px;
            margin-left: 1px;
            opacity: 0.9;
        }
        .dep-item.show-full-path .dep-item-path-toggle-chevron {
            transform: rotate(180deg);
        }
        .dep-item-full-path {
            display: none;
            flex-basis: 100%;
            width: 100%;
            margin-top: 6px;
            margin-left: 0;
            order: 10;
            padding: 6px 8px;
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            word-break: break-all;
            line-height: 1.35;
            background: rgba(0, 0, 0, 0.25);
            border-radius: 4px;
            border-left: 2px solid rgba(124, 58, 237, 0.6);
        }
        .dep-item.show-full-path .dep-item-full-path {
            display: block;
        }
        .dep-item-full-path .dep-item-path-folder {
            color: #7c3aed;
        }
        .dep-item-full-path .dep-item-path-file {
            color: #06b6d4;
        }
        .dep-item-full-path .dep-item-path-sep {
            color: #444;
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
            filter: url(#node-glow);
        }
        
        .node.folder circle {
            fill: #6b7280;
            stroke: #111;
        }
        
        .node.file circle {
            stroke: rgba(0, 0, 0, 0.4);
        }
        
        .node.selected circle {
            stroke-width: 4px;
            filter: url(#node-glow) brightness(1.2) drop-shadow(0 0 10px currentColor);
            transition: stroke-width 0.05s ease-out;
        }
        
        .node:hover circle {
            filter: url(#node-glow) brightness(1.15);
        }
        
        .node.changed circle {
            stroke: #f59e0b;
            stroke-width: 3px;
            filter: url(#node-glow) drop-shadow(0 0 8px #f59e0b);
        }
        .node.has-changed-child circle {
            stroke: #f59e0b;
            stroke-width: 2px;
            filter: url(#node-glow) drop-shadow(0 0 6px rgba(245, 158, 11, 0.6));
        }
        
        .node text {
            font-family: 'JetBrains Mono', monospace;
            fill: #e7e7ee;
            pointer-events: none;
        }
        
        .node text.node-label-outside {
            font-size: 12px;
            fill: #e7e7ee;
            text-anchor: middle;
        }
        
        .node text.node-label-inside {
            font-size: 12px;
            fill: #e7e7ee;
            text-anchor: middle;
            dominant-baseline: central;
        }
        
        .link {
            fill: none;
            stroke-opacity: 0;
            transition: stroke-opacity 0.3s;
        }
        
        .link.visible {
            stroke-opacity: 0.75;
            filter: drop-shadow(0 0 2px currentColor);
        }
        
        .link.import {
            stroke: #6b7280;
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
        
        .link.cross-level {
            stroke-width: 2px;
            cursor: pointer;
        }
        
        .link.cross-level.visible {
            stroke-opacity: 0.85;
            stroke-dasharray: 8 8;
            animation: dashFlow 0.8s linear infinite;
        }
        
        .link.cross-level:hover {
            stroke-opacity: 1;
            stroke-width: 2.5px;
        }
        
        @keyframes dashFlow {
            to { stroke-dashoffset: -16; }
        }
        
        .link-arrow {
            fill: #6b7280;
        }
        
        .container-circle {
            pointer-events: all;
        }
        
        .folder-preview-overlay {
            pointer-events: none;
            opacity: 0.92;
        }
        
        .folder-preview-overlay .folder-preview-dot {
            stroke: none;
            filter: none;
        }
        
        #legend {
            position: fixed;
            top: 70px;
            left: 20px;
            width: 180px;
            max-height: calc(100vh - 100px);
            overflow-y: auto;
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
        .legend-types {
            margin-bottom: 10px;
        }
        .legend-type-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 12px;
        }
        .legend-swatch {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .legend-arrow-icon {
            width: 36px;
            height: 14px;
            flex-shrink: 0;
        }
        .legend-arrow-icon line { stroke-width: 2; }
        .legend-arrow-icon path { stroke: none; }
        .legend-ext {
            font-family: 'JetBrains Mono', monospace;
            color: #e7e7ee;
            font-weight: 500;
        }
        .legend-count {
            color: #d1d5db;
            margin-left: auto;
            font-weight: 600;
        }
        .legend-deps-compact {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(100,100,150,0.2);
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
            color: #e7e7ee;
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
            color: #9ca3af;
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
            color: #9ca3af;
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
            color: #9ca3af;
        }
        
        .help-key {
            display: inline-block;
            background: rgba(100, 100, 150, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            margin: 0 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        #tour-overlay {
            position: fixed;
            left: 0;
            top: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 50;
        }
        #tour-overlay.active {
            pointer-events: auto;
        }
        #tour-overlay.active.tour-overlay-allow-graph-click {
            pointer-events: none;
        }
        #tour-overlay.active.tour-overlay-allow-graph-click #tour-panel {
            pointer-events: auto;
        }
        #tour-overlay-backdrop {
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.35);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        #tour-overlay.active #tour-overlay-backdrop {
            opacity: 1;
        }
        #tour-panel {
            position: fixed;
            left: 24px;
            bottom: 72px;
            min-width: 380px;
            width: 380px;
            max-width: calc(100vw - 48px);
            border-radius: 16px;
            padding: 1px;
            background: linear-gradient(135deg, #06b6d4, #7c3aed);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transform: translateY(120%);
            opacity: 0;
            transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
            z-index: 51;
        }
        #tour-overlay.active #tour-panel {
            transform: translateY(0);
            opacity: 1;
        }
        #tour-panel-inner {
            background: rgba(15, 15, 25, 0.98);
            border-radius: 15px;
            padding: 24px 28px;
            transition: opacity 0.15s ease;
        }
        #tour-panel-inner.tour-content-fade-out {
            opacity: 0;
        }
        .tour-step-progress {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #6b7280;
            margin-bottom: 6px;
        }
        .tour-progress-bar {
            height: 3px;
            background: rgba(100, 100, 150, 0.25);
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 14px;
        }
        .tour-progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #06b6d4, #7c3aed);
            border-radius: 2px;
            transition: width 0.25s ease;
        }
        .tour-step-title {
            font-size: 22px;
            font-weight: 700;
            background: linear-gradient(90deg, #06b6d4, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
            transition: opacity 0.15s ease;
        }
        .tour-step-body {
            font-size: 13px;
            line-height: 1.6;
            color: #d1d5db;
            margin-bottom: 20px;
        }
        .tour-progress-dots {
            display: flex;
            gap: 6px;
            align-items: center;
            margin-bottom: 18px;
        }
        .tour-progress-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: rgba(30, 30, 50, 0.9);
            transition: width 0.2s ease, background 0.2s ease, border-radius 0.2s ease;
        }
        .tour-progress-dot.active {
            width: 20px;
            height: 6px;
            border-radius: 3px;
            background: #06b6d4;
        }
        .tour-pro-tip {
            margin-top: 8px;
            margin-bottom: 18px;
            padding: 10px 12px;
            border-radius: 10px;
            background: rgba(30, 30, 40, 0.95);
            border: 1px solid rgba(161, 98, 7, 0.5);
            display: none;
            font-size: 11px;
            line-height: 1.5;
            color: #fbbf24;
            display: none;
        }
        .tour-pro-tip-icon {
            margin-right: 6px;
        }
        .tour-pro-tip-text {
            color: #facc15;
        }
        .tour-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .tour-actions button {
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 500;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s ease, color 0.2s ease, opacity 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .tour-actions .tour-btn-back {
            background: transparent;
            color: #e0e0e0;
            border: 1px solid rgba(100, 100, 150, 0.4);
        }
        .tour-actions .tour-btn-back:hover:not(:disabled) {
            background: rgba(100, 100, 150, 0.15);
            border-color: rgba(124, 58, 237, 0.5);
        }
        .tour-actions .tour-btn-back:disabled {
            opacity: 0.4;
            cursor: default;
        }
        .tour-actions .tour-btn-next {
            background: #7c3aed;
            color: #fff;
            border: 1px solid transparent;
            box-shadow: 0 0 14px rgba(124, 58, 237, 0.4);
        }
        .tour-actions .tour-btn-next:hover:not(:disabled) {
            background: #8b5cf6;
            box-shadow: 0 0 18px rgba(124, 58, 237, 0.5);
        }
        .tour-actions .tour-btn-next:disabled {
            opacity: 0.5;
            cursor: default;
        }
        .tour-actions .tour-btn-exit {
            margin-left: auto;
            background: transparent;
            color: #9ca3af;
            border: 1px solid rgba(100, 100, 150, 0.4);
        }
        .tour-actions .tour-btn-exit:hover {
            color: #e0e0e0;
            border-color: rgba(124, 58, 237, 0.5);
            background: rgba(100, 100, 150, 0.1);
        }
        .tour-intro-screen {
            position: relative;
            padding-top: 8px;
        }
        .tour-intro-close {
            position: absolute;
            top: 0;
            right: 0;
            width: 28px;
            height: 28px;
            padding: 0;
            font-size: 16px;
            line-height: 1;
            color: #9ca3af;
            background: transparent;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: color 0.2s ease, background 0.2s ease;
        }
        .tour-intro-close:hover {
            color: #e0e0e0;
            background: rgba(100, 100, 150, 0.2);
        }
        .tour-intro-title {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(90deg, #06b6d4, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 12px 0;
            padding-right: 32px;
        }
        .tour-intro-subtitle {
            font-size: 14px;
            line-height: 1.55;
            color: #9ca3af;
            margin: 0 0 16px 0;
        }
        .tour-intro-stat {
            font-size: 12px;
            color: #6b7280;
            margin: 0 0 24px 0;
        }
        .tour-intro-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 16px;
            color: #9ca3af;
            font-size: 13px;
            margin-bottom: 16px;
        }
        .tour-intro-loading::before {
            content: '';
            width: 18px;
            height: 18px;
            border: 2px solid rgba(124, 58, 237, 0.3);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: tour-glow-pulse-spin 0.8s linear infinite;
        }
        .tour-intro-go {
            display: block;
            width: 100%;
            padding: 12px 20px;
            font-size: 15px;
            font-weight: 600;
            color: #fff;
            background: #7c3aed;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0 0 14px rgba(124, 58, 237, 0.4);
            transition: background 0.2s ease, box-shadow 0.2s ease;
        }
        .tour-intro-go:hover:not(:disabled) {
            background: #8b5cf6;
            box-shadow: 0 0 18px rgba(124, 58, 237, 0.5);
        }
        .tour-intro-go:disabled {
            opacity: 0.7;
            cursor: wait;
        }
        .node.tour-dimmed {
            opacity: 0.2;
        }
        @keyframes tour-glow-pulse-spin {
            to { transform: rotate(360deg); }
        }
        .placeholder {
            color: #888;
            font-style: italic;
            padding: 40px;
            text-align: center;
        }
        
        .empty-state {
            color: #888;
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
        <button type="button" id="tour-start-btn" class="header-tour-btn" title="Start Virtual Guide">✦ Start Virtual Guide</button>
        <div class="breadcrumb" id="breadcrumb">
            <span class="breadcrumb-item breadcrumb-folder" onclick="navigateTo('', true)">''' + data['rootName'] + '''</span>
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
                <filter id="node-glow" x="-80%" y="-80%" width="260%" height="260%">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
                    <feMerge>
                        <feMergeNode in="blur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
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
                <!-- Arrowheads at 0.7x size (7x4.9) for all nodes -->
                <marker id="arrowhead" markerWidth="7" markerHeight="4.9" refX="7" refY="2.45" orient="auto">
                    <polygon points="0 0, 7 2.45, 0 4.9" fill="#6b7280"/>
                </marker>
                <marker id="arrowhead-inbound" markerWidth="7" markerHeight="4.9" refX="7" refY="2.45" orient="auto">
                    <polygon points="0 0, 7 2.45, 0 4.9" fill="#22c55e"/>
                </marker>
                <marker id="arrowhead-outbound" markerWidth="7" markerHeight="4.9" refX="7" refY="2.45" orient="auto">
                    <polygon points="0 0, 7 2.45, 0 4.9" fill="#f59e0b"/>
                </marker>
                <!-- Purple arrowhead for cross-level dependencies -->
                <marker id="arrowhead-cross-level" markerWidth="7" markerHeight="4.9" refX="7" refY="2.45" orient="auto">
                    <polygon points="0 0, 7 2.45, 0 4.9" fill="#22c55e"/>
                </marker>
            </defs>
        </svg>
    </div>
    
    <div id="right-rail">
        <div class="panel-toggle-btns">
            <button type="button" id="panel-toggle-file-btn" class="panel-toggle-btn" title="Selection Information" aria-label="Selection Information"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></button>
            <button type="button" id="panel-toggle-changes-btn" class="panel-toggle-btn" title="Change Panel" aria-label="Change Panel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
            <button type="button" id="panel-toggle-search-btn" class="panel-toggle-btn" title="Search" aria-label="Search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></button>
        </div>
        <div id="file-info-panel">
            <div class="panel-inner">
                <h2 class="panel-title">Selection Information</h2>
                <div id="sidebar-nav" class="sidebar-nav">
                    <button type="button" id="sidebar-back-btn" class="sidebar-nav-btn" title="Back" aria-label="Back" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg></button>
                    <button type="button" id="sidebar-forward-btn" class="sidebar-nav-btn" title="Forward" aria-label="Forward" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></button>
                </div>
                <div id="details-panel">
                    <div class="details-placeholder">Click a node to view its details</div>
                </div>
            </div>
        </div>
        <div id="changes-panel">
            <div class="panel-inner">
                <h2 class="panel-title">Change Panel</h2>
                <div id="recent-changes-panel" class="recent-changes-panel">
                    <div id="recent-changes-title" class="recent-changes-title">Changes from Recent Save</div>
                    <div id="recent-changes-last-send" class="last-save-box">—</div>
                    <div id="recent-changes-list" class="recent-changes-list"></div>
                    <div id="recent-changes-git-section" class="recent-changes-git-section">
                        <div id="recent-changes-git-title" class="recent-changes-title">Changes from Previous Saves</div>
                        <div id="recent-changes-git-list" class="recent-changes-list"></div>
                    </div>
                </div>
            </div>
        </div>
        <div id="search-panel">
            <div class="panel-inner">
                <h2 class="panel-title">Search</h2>
                <div class="search-panel-search">
                    <input type="text" id="search-input" placeholder="Search files and folders…" autocomplete="off" />
                    <button type="button" id="search-clear-btn" class="search-clear-btn" title="Clear search">×</button>
                </div>
                <div id="search-results" class="search-results"></div>
            </div>
        </div>
    </div>
    
    <div id="tour-overlay">
        <div id="tour-overlay-backdrop"></div>
        <div id="tour-panel">
            <div id="tour-panel-inner">
                <div id="tour-intro" class="tour-intro-screen" style="display: none;">
                    <button type="button" id="tour-intro-close" class="tour-intro-close" title="Close">✕</button>
                    <h2 class="tour-intro-title">Your Codebase Tour</h2>
                    <p class="tour-intro-subtitle">We'll walk you through the 5 most important files in this codebase, explain how the graph works, and show you where to start.</p>
                    <p class="tour-intro-stat" id="tour-intro-stat">📁 Analyzing 0 files across 0 folders</p>
                    <div class="tour-intro-loading" id="tour-intro-loading" style="display: none;">Preparing your tour…</div>
                    <button type="button" id="tour-intro-go" class="tour-intro-go">Let's go →</button>
                </div>
                <div id="tour-step-view" class="tour-step-view">
                    <div class="tour-step-progress" id="tour-step-progress">Step 1 of 5</div>
                    <div class="tour-progress-bar"><div class="tour-progress-bar-fill" id="tour-progress-bar-fill" style="width: 20%;"></div></div>
                    <h2 class="tour-step-title" id="tour-step-title">Main Entry Point</h2>
                    <p class="tour-step-body" id="tour-step-body">Placeholder explanation for this step. The Virtual Guide will highlight key nodes and explain the codebase structure.</p>
                    <div class="tour-progress-dots" id="tour-progress-dots"></div>
                    <div class="tour-pro-tip" id="tour-pro-tip">
                        <span class="tour-pro-tip-icon">💡</span>
                        <span class="tour-pro-tip-text">Pro tip: Hover over any file or folder to see its details at a glance — no clicking needed.</span>
                    </div>
                    <div class="tour-actions">
                        <button type="button" class="tour-btn-back" id="tour-btn-back" disabled>Back</button>
                        <button type="button" class="tour-btn-next" id="tour-btn-next">Next</button>
                        <button type="button" class="tour-btn-exit" id="tour-btn-exit">Exit</button>
                    </div>
                </div>
            </div>
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
    <div class="legend-section-title">Scripting languages</div>
    <div id="legend-file-types" class="legend-types"></div>
    <div class="legend-deps-compact">
      <div class="legend-type-row">
        <svg class="legend-arrow-icon" viewBox="0 0 36 14" aria-hidden="true">
          <line x1="0" y1="7" x2="24" y2="7" stroke="#06b6d4"/>
          <path d="M24 2 L34 7 L24 12 Z" fill="#06b6d4"/>
        </svg>
        <span class="legend-ext">Import (A → B)</span>
      </div>
      <div class="legend-type-row">
        <svg class="legend-arrow-icon" viewBox="0 0 36 14" aria-hidden="true">
          <line x1="0" y1="7" x2="24" y2="7" stroke="#22c55e"/>
          <path d="M24 2 L34 7 L24 12 Z" fill="#22c55e"/>
        </svg>
        <span class="legend-ext">Inbound</span>
      </div>
      <div class="legend-type-row">
        <svg class="legend-arrow-icon" viewBox="0 0 36 14" aria-hidden="true">
          <line x1="0" y1="7" x2="24" y2="7" stroke="#f59e0b"/>
          <path d="M24 2 L34 7 L24 12 Z" fill="#f59e0b"/>
        </svg>
        <span class="legend-ext">Outbound</span>
      </div>
      <div class="legend-type-row">
        <div class="legend-swatch legend-swatch-changed" style="background:#1a1a24; border:2px solid #f59e0b; box-shadow:0 0 8px #f59e0b;"></div>
        <span class="legend-ext">Changed (working branch)</span>
      </div>
    </div>
  </div>
  <div class="legend-detailed legend-body">
    <div class="legend-section-title">Scripting languages</div>
    <div id="legend-file-types-detail" class="legend-types"></div>
    <div class="legend-section legend-divider">
      <div class="legend-section-title">Dependencies</div>
      <div class="legend-caption-top">A → B means A depends on B. Arrows show when a file is selected.</div>
      <div class="legend-grid">
        <div class="legend-icon">
          <svg class="legend-arrow" viewBox="0 0 52 16">
            <line x1="0" y1="8" x2="44" y2="8" stroke="#06b6d4" marker-end="url(#arrowhead)"></line>
          </svg>
        </div>
        <div class="legend-label">
          <div class="legend-name">Import (A → B)</div>
          <div class="legend-caption">Dependency link between files</div>
        </div>
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
        <div class="legend-icon">
          <div class="legend-circle" style="background:#1a1a24; border:2px solid #f59e0b; box-shadow:0 0 6px rgba(245,158,11,0.6);"></div>
        </div>
        <div class="legend-label">
          <div class="legend-name">Changed (working branch)</div>
          <div class="legend-caption">File or folder with unsaved or recent changes</div>
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
        let graphData = ''' + json.dumps(data) + ''';
        
        // Build lookup maps (rebuilt when loading a new repo)
        let nodesById = new Map(graphData.nodes.map(n => [n.id, n]));
        let linksMap = new Map(); // source -> target -> link
        function rebuildLinksMap() {
            linksMap.clear();
            graphData.links.forEach(l => {
                if (!linksMap.has(l.source)) linksMap.set(l.source, new Map());
                linksMap.get(l.source).set(l.target, l);
            });
        }
        rebuildLinksMap();
        
        let currentPath = '';
        let selectedNode = null;
        let simulation = null;
        let folderCountMode = 'direct';  // 'direct' | 'recursive'
        let selectionHistory = [];
        let historyIndex = -1;
        let lastChangesData = { lastSendTimestamp: null, changes: [], batches: [] };
        let gitStatusData = { modified: [], added: [], deleted: [], renamed: [] };

        const FOLDER_COLOR = '#7c3aed';
        const EXTENSION_PALETTE = [
            '#ec4899', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444', '#14b8a6',
            '#8b5cf6', '#84cc16', '#f43f5e', '#0ea5e9', '#eab308', '#a855f7',
            '#10b981', '#6366f1', '#78716c'
        ];
        const EXTENSION_FALLBACK = '#64748b';
        let extensionColorMap = {};  // extension -> hex, computed from graphData.nodes
        const fileSummaryCache = new Map();  // path -> { summary: string, loading: boolean }
        const aiSummaryCache = {};  // path::mode -> { result: string } or { loading: true }
        window._tourActive = false;
        window._tourStepIndex = 0;
        window._tourSteps = [];
        let nodeTooltipEl = null;
        let nodeTooltipTimer = null;
        let nodeTooltipNodeId = null;

        function computeExtensionColors(nodes) {
            const exts = [...new Set(nodes.filter(n => n.type === 'file').map(n => n.extension || '').filter(Boolean))].sort();
            const map = {};
            exts.forEach((ext, i) => { map[ext] = EXTENSION_PALETTE[i % EXTENSION_PALETTE.length]; });
            return map;
        }

        let maxMetrics = graphData.maxMetrics;
        extensionColorMap = computeExtensionColors(graphData.nodes);

        function updateGraphData(newData) {
            graphData = newData;
            maxMetrics = graphData.maxMetrics || {};
            nodesById = new Map(graphData.nodes.map(n => [n.id, n]));
            extensionColorMap = computeExtensionColors(graphData.nodes);
            rebuildLinksMap();
            currentPath = '';
            selectedNode = null;
            selectionHistory = [];
            historyIndex = -1;
            updateLegend();
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
            updateSidebarNav();
        }

        function ensureNodeTooltipElement() {
            if (nodeTooltipEl) return nodeTooltipEl;
            const el = document.createElement('div');
            el.className = 'node-tooltip';
            el.style.display = 'none';
            el.addEventListener('mouseenter', () => {
                cancelNodeTooltipTimer();
            });
            el.addEventListener('mouseleave', (e) => {
                hideNodeTooltip();
            });
            document.body.appendChild(el);
            nodeTooltipEl = el;
            return el;
        }
        function hideNodeTooltip() {
            if (nodeTooltipEl) {
                nodeTooltipEl.style.display = 'none';
            }
            nodeTooltipNodeId = null;
        }
        function cancelNodeTooltipTimer() {
            if (nodeTooltipTimer) {
                clearTimeout(nodeTooltipTimer);
                nodeTooltipTimer = null;
            }
        }
        async function fetchFileSummary(path) {
            try {
                const resp = await fetch(window.location.origin + '/api/summarize_file?path=' + encodeURIComponent(path));
                const data = await resp.json();
                if (data && typeof data.summary === 'string') {
                    return data.summary;
                }
            } catch (e) {
                // ignore
            }
            return 'No summary available.';
        }
        function firstSentence(s) {
            if (typeof s !== 'string' || !s.trim()) return '';
            const trimmed = s.trim();
            const match = trimmed.match(/^[^.!?]+[.!?]?/);
            return (match ? match[0] : trimmed).trim();
        }
        function buildTooltipHTMLForNode(node, summaryState) {
            const isFile = node.type === 'file';
            const name = escapeAttr(node.name || 'Unknown');
            const path = (node.path || node.id || '').trim();
            const pathDisplay = path ? escapeAttr(path) : '—';
            const typeLabel = isFile ? 'File' : 'Folder';
            let html = `<div class="node-tooltip-header">${name}</div>`;
            html += `<div class="node-tooltip-type-path">${typeLabel} · ${pathDisplay}</div>`;
            if (isFile) {
                const loc = node.loc != null ? node.loc.toLocaleString() : '—';
                const inbound = Array.isArray(node.dependents) ? node.dependents.length : '—';
                const outbound = Array.isArray(node.dependencies) ? node.dependencies.length : '—';
                html += `<div class="node-tooltip-meta-row"><span>Lines</span><span>${loc}</span></div>`;
                html += `<div class="node-tooltip-meta-row"><span>Inbound</span><span>${inbound}</span></div>`;
                html += `<div class="node-tooltip-meta-row"><span>Outbound</span><span>${outbound}</span></div>`;
                html += `<div class="node-tooltip-divider"></div>`;
                const hasSummary = summaryState && typeof summaryState.summary === 'string' && summaryState.summary.trim() !== '';
                const oneLine = hasSummary ? firstSentence(summaryState.summary) : '';
                if (hasSummary && oneLine) {
                    html += `<div id="node-tooltip-summary" class="node-tooltip-summary" title="${escapeAttr(summaryState.summary)}">${escapeAttr(oneLine)}</div>`;
                } else if (summaryState && summaryState.loading) {
                    html += `<div id="node-tooltip-summary" class="node-tooltip-summary node-tooltip-summary-loading">
                        <span class="node-tooltip-spinner"></span>
                        <span>Generating AI summary…</span>
                    </div>`;
                } else {
                    html += `<div id="node-tooltip-summary" class="node-tooltip-summary">—</div>`;
                }
            } else {
                const directFiles = node.directFileCount != null ? node.directFileCount : '—';
                const subfolders = node.subfolderCount != null ? node.subfolderCount : '—';
                html += `<div class="node-tooltip-meta-row"><span>Direct files</span><span>${directFiles}</span></div>`;
                html += `<div class="node-tooltip-meta-row"><span>Subfolders</span><span>${subfolders}</span></div>`;
            }
            return html;
        }
        function showNodeTooltipForNode(node, event) {
            const el = ensureNodeTooltipElement();
            nodeTooltipNodeId = node.id;
            const isFile = node.type === 'file';
            const path = node.path || node.id || '';
            let summaryState = isFile && path ? fileSummaryCache.get(path) : null;
            const needFetch = isFile && path && (!summaryState || !summaryState.summary);
            if (needFetch) {
                fileSummaryCache.set(path, { summary: '', loading: true });
                summaryState = fileSummaryCache.get(path);
            }
            el.innerHTML = buildTooltipHTMLForNode(node, summaryState);
            const offset = 14;
            const x = (event.clientX || 0) + offset;
            const y = (event.clientY || 0) + offset;
            el.style.left = x + 'px';
            el.style.top = y + 'px';
            el.style.display = 'block';
            if (needFetch) {
                (async () => {
                    const summary = await fetchFileSummary(path);
                    fileSummaryCache.set(path, { summary, loading: false });
                    if (nodeTooltipNodeId === node.id && nodeTooltipEl) {
                        const summaryEl = nodeTooltipEl.querySelector('#node-tooltip-summary');
                        if (summaryEl) {
                            summaryEl.classList.remove('node-tooltip-summary-loading');
                            summaryEl.innerText = firstSentence(summary) || '—';
                            summaryEl.title = summary;
                        }
                    }
                })();
            }
        }
        function handleNodeMouseOver(event, node) {
            cancelNodeTooltipTimer();
            nodeTooltipTimer = setTimeout(() => {
                showNodeTooltipForNode(node, event);
            }, 600);
        }
        function handleNodeMouseOut(event, node) {
            cancelNodeTooltipTimer();
            const rt = event.relatedTarget;
            if (nodeTooltipEl && rt && nodeTooltipEl.contains(rt)) {
                return;
            }
            if (nodeTooltipNodeId === node.id) {
                hideNodeTooltip();
            }
        }

        async function loadRepo(pathFromUrl) {
            const path = (pathFromUrl && pathFromUrl.trim()) ? pathFromUrl.trim() : '';
            if (!path) return;
            try {
                const resp = await fetch('/api/load?path=' + encodeURIComponent(path));
                const data = await resp.json();
                if (data.error) { alert(data.error); return; }
                updateGraphData(data);
            } catch (e) {
                alert('Failed to load repo: ' + e.message);
            }
        }

        function updateLegend() {
            const nodes = graphData.nodes || [];
            const fileCountByExt = {};
            let folderCount = 0;
            nodes.forEach(n => {
                if (n.type === 'folder') folderCount++;
                else if (n.type === 'file') {
                    const ext = n.extension || '';
                    fileCountByExt[ext] = (fileCountByExt[ext] || 0) + 1;
                }
            });
            const extEntries = Object.entries(fileCountByExt)
                .sort((a, b) => b[1] - a[1] || (a[0] || '').localeCompare(b[0] || ''));
            const extLabel = (ext) => (ext && ext.startsWith('.')) ? ext.slice(1) : (ext || '?');
            let html = '';
            extEntries.forEach(([ext, count]) => {
                const color = extensionColorMap[ext] || EXTENSION_FALLBACK;
                const label = escapeAttr(extLabel(ext));
                html += `<div class="legend-type-row"><div class="legend-swatch" style="background:${color};"></div><span class="legend-ext">${label}</span><span class="legend-count">${count}</span></div>`;
            });
            html += `<div class="legend-type-row"><div class="legend-swatch" style="background:${FOLDER_COLOR};"></div><span class="legend-ext">Folder</span><span class="legend-count">${folderCount}</span></div>`;
            const container = document.getElementById('legend-file-types');
            const containerDetail = document.getElementById('legend-file-types-detail');
            if (container) container.innerHTML = html;
            if (containerDetail) containerDetail.innerHTML = html;
        }
        updateLegend();
        
        document.getElementById('legend-expand-btn').addEventListener('click', function () {
            var legend = document.getElementById('legend');
            legend.classList.toggle('detailed-open');
            this.setAttribute('title', legend.classList.contains('detailed-open') ? 'Collapse key' : 'Expand key');
        });

        // When opened from Cursor (or with shared link), URL has ?path=... — auto-load that repo
        (function () {
            const params = new URLSearchParams(window.location.search);
            const pathParam = params.get('path');
            if (pathParam) loadRepo(pathParam);
        })();

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
        window._graphG = g;
        window._graphSvg = svg;
        window._graphZoom = zoom;
        window._graphWidth = width;
        window._graphHeight = height;
        
        // Click on background to deselect
        svg.on('click', function(event) {
            // Only deselect if clicking on the SVG background itself, not on nodes or container circle
            const target = event.target;
            if (target === svg.node() || target.tagName === 'svg') {
                selectedNode = null;
                updateBreadcrumb();
                updateSelection();
                renderSidePanel();
            }
        });
        
        function getNodeColor(node) {
            if (node.type === 'folder') return FOLDER_COLOR;
            return extensionColorMap[node.extension] || EXTENSION_FALLBACK;
        }

        function getNodeSize(node) {
            const value = Math.max(node.pagerank || 0, 0.01);
            const maxValue = Math.max(maxMetrics.pagerank || 1, 0.01);
            const normalized = Math.sqrt(value) / Math.sqrt(maxValue);
            // Linear mapping so size differences are obvious: radius 6 (low) to 50 (high)
            const radius = 6 + normalized * 44;
            return Math.max(6, Math.min(50, radius));
        }
        
        function getPackRadius(node) {
            const fileR = Math.max(28, getNodeSize(node));
            return node.type === 'folder' ? 2 * fileR : fileR;
        }
        
        function getPackValue(node) {
            // Pack uses area (value); use fixed ratio so folders are always 2x file radius
            return node.type === 'folder' ? 4 : 1;
        }
        
        function normPath(p) {
            return (p || '').replace(/\\\\/g, '/').replace(/^\\//, '').trim();
        }
        function getAffectedPathsFromChange(c) {
            const out = [];
            if (c.path !== undefined) out.push(c.path);
            if (c.oldPath !== undefined) out.push(c.oldPath);
            if (c.newPath !== undefined) out.push(c.newPath);
            if (c.fromFile !== undefined) out.push(c.fromFile);
            if (c.toFile !== undefined) out.push(c.toFile);
            return out.map(normPath).filter(Boolean);
        }
        function getChangedPathSet(changes) {
            const set = new Set();
            (changes || []).forEach(c => getAffectedPathsFromChange(c).forEach(p => set.add(p)));
            return set;
        }
        function getMergedChangedPathSet() {
            const set = getChangedPathSet(lastChangesData.changes);
            const g = gitStatusData;
            (g.modified || []).forEach(p => set.add(normPath(p)));
            (g.added || []).forEach(p => set.add(normPath(p)));
            (g.deleted || []).forEach(p => set.add(normPath(p)));
            (g.renamed || []).forEach(r => { set.add(normPath(r.oldPath)); set.add(normPath(r.newPath)); });
            return set;
        }
        function getFolderHasChangedChildSet(nodes) {
            const changedPaths = getMergedChangedPathSet();
            const folderSet = new Set();
            (nodes || []).filter(n => n.type === 'folder').forEach(n => {
                const folderPath = normPath(n.path || n.id);
                if (!folderPath || folderPath === 'root') return;
                for (const p of changedPaths) {
                    if (p === folderPath || p.startsWith(folderPath + '/')) {
                        folderSet.add(n.id);
                        break;
                    }
                }
            });
            if (changedPaths.size > 0) folderSet.add('root');
            return folderSet;
        }

        function isChangeInFolder(c, folderPath) {
            const paths = getAffectedPathsFromChange(c);
            if (!folderPath) return paths.length > 0;
            return paths.some(p => p === folderPath || p.startsWith(folderPath + '/'));
        }
        
        function isPathInFolder(p, folderPath) {
            const norm = normPath(p);
            if (!folderPath) return true;
            return norm === folderPath || norm.startsWith(folderPath + '/');
        }
        let filteredChangesForPanel = [];
        let expandedChangeDescriptions = {};
        let expandedChangeKeys = new Set();
        let expandedGitSummaries = {};
        let expandedGitKeys = new Set();
        function changeKey(c) {
            return (c.type || '') + '|' + (c.path || c.fromFile || c.oldPath || '') + '|' + (c.toFile || c.newPath || '');
        }
        function updateChangesInFolderPanel() {
            const titleEl = document.getElementById('recent-changes-title');
            const listEl = document.getElementById('recent-changes-list');
            const gitTitleEl = document.getElementById('recent-changes-git-title');
            const gitListEl = document.getElementById('recent-changes-git-list');
            if (!titleEl || !listEl) return;
            const folderPath = currentPath || '';
            if (titleEl) titleEl.textContent = 'Changes from Recent Save';
            const changes = lastChangesData.changes || [];
            filteredChangesForPanel = changes.filter(c => isChangeInFolder(c, folderPath));
            if (filteredChangesForPanel.length === 0) {
                listEl.innerHTML = '';
            } else {
                listEl.innerHTML = filteredChangesForPanel.map(function(c, i) {
                    const mainLine = changeMainLine(c);
                    return '<div class="change-line-with-desc" data-index="' + i + '">' +
                        '<div class="change-line-header">' +
                        '<span class="change-line-text">' + mainLine + '</span>' +
                        '<button type="button" class="change-desc-toggle" onclick="describeChange(this)" aria-expanded="false" title="Toggle description">▼</button>' +
                        '</div>' +
                        '<div class="change-description" style="display:none;"></div></div>';
                }).join('');
                filteredChangesForPanel.forEach(function(c, i) {
                    const key = changeKey(c);
                    if (!expandedChangeKeys.has(key)) return;
                    const stored = expandedChangeDescriptions[key];
                    const row = listEl.children[i];
                    if (!row) return;
                    const descEl = row.querySelector('.change-description');
                    const btn = row.querySelector('.change-desc-toggle');
                    if (descEl && btn && stored) {
                        descEl.textContent = stored.text;
                        descEl.style.display = 'block';
                        btn.setAttribute('aria-expanded', 'true');
                        btn.textContent = '▲';
                    }
                });
            }
            if (gitTitleEl && gitListEl) {
                gitTitleEl.textContent = 'Changes from Previous Saves';
                const batches = lastChangesData.batches || [];
                const previousBatches = batches.length > 1 ? batches.slice(0, -1).reverse() : [];
                let previousFlat = [];
                previousBatches.forEach(function(b) {
                    const ts = b.timestamp;
                    (b.changes || []).forEach(function(c) {
                        if (isChangeInFolder(c, folderPath)) previousFlat.push({ change: c, batchTimestamp: ts });
                    });
                });
                if (previousFlat.length === 0) {
                    gitListEl.innerHTML = '<div class="recent-changes-muted">No previous changes yet. Save with Cmd+S to build history.</div>';
                } else {
                    function pathFromChange(c) {
                        return (c.path || c.newPath || c.toFile || c.fromFile || '').replace(/\\\\/g, '/').trim();
                    }
                    function statusFromChange(c) {
                        const t = (c.type || '').toLowerCase();
                        if (t === 'file_added' || t === 'folder_added') return 'A';
                        if (t === 'file_deleted' || t === 'folder_deleted') return 'D';
                        if (t === 'path_changed' || t === 'folder_path_changed') return 'R';
                        return 'M';
                    }
                    let html = '';
                    previousFlat.forEach(function(item) {
                        const c = item.change;
                        const path = pathFromChange(c);
                        const status = statusFromChange(c);
                        const mainLine = changeMainLine(c);
                        const batchTs = item.batchTimestamp;
                        const desc = (c.description || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        html += '<div class="change-line-with-desc git-prev-change" data-path="' + escapeAttr(path) + '" data-status="' + escapeAttr(status) + '" data-batch-ts="' + escapeAttr(String(batchTs)) + '">' +
                            '<div class="change-line-header">' +
                            '<span class="change-line-text">' + mainLine + '</span>' +
                            '<button type="button" class="change-desc-toggle" onclick="describeFileChange(this)" aria-expanded="false" data-path="' + escapeAttr(path) + '" data-status="' + escapeAttr(status) + '" data-batch-ts="' + escapeAttr(String(batchTs)) + '" title="Toggle description">▼</button>' +
                            '</div>' +
                            '<div class="change-description" style="display:none;">' + desc + '</div></div>';
                    });
                    gitListEl.innerHTML = html;
                    [].forEach.call(gitListEl.querySelectorAll('.change-line-with-desc.git-prev-change'), function(wrap) {
                        const btn = wrap.querySelector('.change-desc-toggle');
                        const summaryEl = wrap.querySelector('.change-description');
                        if (!btn || !summaryEl) return;
                        const p = btn.getAttribute('data-path');
                        const bts = btn.getAttribute('data-batch-ts');
                        const cacheKey = p + '::' + (bts || 'latest');
                        if (!expandedGitKeys.has(cacheKey)) return;
                        const text = expandedGitSummaries[cacheKey] || summaryEl.textContent;
                        if (text) {
                            summaryEl.textContent = text;
                            summaryEl.style.display = 'block';
                            btn.setAttribute('aria-expanded', 'true');
                            btn.textContent = '▲';
                        }
                    });
                }
            }
        }
        
        function updateDescribeBtnState(btn, expanded) {
            if (btn) {
                btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
                btn.textContent = expanded ? '▲' : '▼';
            }
        }
        async function describeChange(btn) {
            const row = btn.closest('.change-line-with-desc');
            if (!row) return;
            const idx = parseInt(row.getAttribute('data-index'), 10);
            if (isNaN(idx) || idx < 0 || idx >= filteredChangesForPanel.length) return;
            const change = filteredChangesForPanel[idx];
            const descEl = row.querySelector('.change-description');
            if (!descEl) return;
            const key = changeKey(change);
            const isExpanded = descEl.style.display === 'block';
            if (isExpanded && descEl.textContent !== 'Loading…') {
                descEl.style.display = 'none';
                descEl.textContent = '';
                expandedChangeKeys.delete(key);
                updateDescribeBtnState(btn, false);
                return;
            }
            expandedChangeKeys.add(key);
            const stored = expandedChangeDescriptions[key];
            if (stored) {
                descEl.textContent = stored.text;
                descEl.style.display = 'block';
                updateDescribeBtnState(btn, true);
                return;
            }
            btn.disabled = true;
            descEl.style.display = 'block';
            descEl.textContent = 'Loading…';
            updateDescribeBtnState(btn, true);
            try {
                const resp = await fetch(window.location.origin + '/api/describe_change', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ change: change })
                });
                const data = await resp.json();
                const text = data.description || (data.error ? 'Error: ' + data.error : 'No description.');
                descEl.textContent = text;
                expandedChangeDescriptions[key] = { text: text };
            } catch (e) {
                descEl.textContent = 'Error: ' + e.message;
                expandedChangeDescriptions[key] = { text: 'Error: ' + e.message };
            }
            btn.disabled = false;
            updateDescribeBtnState(btn, true);
        }
        
        async function describeFileChange(btn) {
            const path = btn.getAttribute('data-path');
            const status = btn.getAttribute('data-status') || 'M';
            const batchTs = btn.getAttribute('data-batch-ts');
            if (!path) return;
            const wrap = btn.closest('.change-line-with-desc');
            const summaryEl = wrap ? wrap.querySelector('.change-description') : null;
            if (!summaryEl) return;
            const cacheKey = path + '::' + (batchTs || 'latest');
            const isExpanded = btn.getAttribute('aria-expanded') === 'true';
            if (isExpanded) {
                summaryEl.style.display = 'none';
                summaryEl.textContent = '';
                expandedGitKeys.delete(cacheKey);
                updateDescribeBtnState(btn, false);
                return;
            }
            expandedGitKeys.add(cacheKey);
            if (expandedGitSummaries[cacheKey]) {
                summaryEl.textContent = expandedGitSummaries[cacheKey];
                summaryEl.style.display = 'block';
                updateDescribeBtnState(btn, true);
                return;
            }
            summaryEl.style.display = 'block';
            summaryEl.textContent = 'Loading…';
            updateDescribeBtnState(btn, true);
            btn.disabled = true;
            const body = { path: path, status: status };
            if (batchTs != null && batchTs !== '') body.batchTimestamp = Number(batchTs);
            try {
                const resp = await fetch(window.location.origin + '/api/describe_file_change', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await resp.json();
                const text = data.description || (data.error ? 'Error: ' + data.error : 'No summary.');
                summaryEl.textContent = text;
                expandedGitSummaries[cacheKey] = text;
            } catch (e) {
                const errText = 'Error: ' + e.message;
                summaryEl.textContent = errText;
                expandedGitSummaries[cacheKey] = errText;
            }
            btn.disabled = false;
            updateDescribeBtnState(btn, true);
        }
        
        function navigateTo(path, clearPanel) {
            if (clearPanel) selectedNode = null;
            pushHistory(path || '');
            currentPath = path;
            clearSearchUI();
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
            updateSidebarNav();
        }
        
        function pushHistory(path) {
            if (path === (selectionHistory[historyIndex] ?? null)) return;
            selectionHistory = selectionHistory.slice(0, historyIndex + 1);
            selectionHistory.push(path);
            historyIndex = selectionHistory.length - 1;
        }
        function applyHistoryEntry(path) {
            if (path === '') {
                currentPath = '';
                selectedNode = null;
                clearSearchUI();
                updateBreadcrumb();
                renderGraph();
                updateSelection();
                renderSidePanel();
                updateSidebarNav();
                return;
            }
            const node = nodesById.get(path);
            if (!node) return;
            if (node.type === 'folder') {
                selectedNode = null;
                currentPath = path;
            } else {
                selectedNode = node;
                const parts = path.split('/');
                parts.pop();
                currentPath = parts.join('/');
            }
            clearSearchUI();
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
            updateSidebarNav();
        }
        function goBack() {
            if (historyIndex <= 0) return;
            historyIndex--;
            applyHistoryEntry(selectionHistory[historyIndex]);
        }
        function goForward() {
            if (selectionHistory.length === 0 || historyIndex >= selectionHistory.length - 1) return;
            historyIndex++;
            applyHistoryEntry(selectionHistory[historyIndex]);
        }
        function updateSidebarNav() {
            const backBtn = document.getElementById('sidebar-back-btn');
            const forwardBtn = document.getElementById('sidebar-forward-btn');
            if (backBtn) backBtn.disabled = historyIndex <= 0 || selectionHistory.length === 0;
            if (forwardBtn) forwardBtn.disabled = historyIndex >= selectionHistory.length - 1 || selectionHistory.length === 0;
        }
        function focusFile(path) {
            pushHistory(path);
            const parts = path.split('/');
            parts.pop();
            const parentPath = parts.join('/');
            currentPath = parentPath;
            selectedNode = nodesById.get(path) || null;
            updateBreadcrumb();
            renderGraph();
            updateSelection();
            renderSidePanel();
            updateSidebarNav();
        }
        function clearSelection() {
            selectedNode = null;
            updateBreadcrumb();
            updateSelection();
            renderSidePanel();
            updateSidebarNav();
        }
        function clearSearchUI() {
            const input = document.getElementById('search-input');
            const container = document.getElementById('search-results');
            if (input) input.value = '';
            if (container) {
                container.style.display = 'none';
                container.innerHTML = '';
            }
            clearSelection();
        }
        function normalizeSearchText(s) {
            return String(s || '').toLowerCase();
        }
        function getSearchMatches(query, limit) {
            const q = normalizeSearchText(query);
            if (!q) return [];
            const nodes = graphData.nodes || [];
            const out = [];
            const max = limit || 30;
            for (const n of nodes) {
                if (n.type !== 'file' && n.type !== 'folder') continue;
                const name = normalizeSearchText(n.name);
                const path = normalizeSearchText(n.path || n.id || '');
                if (!name && !path) continue;
                if (name.includes(q) || path.includes(q)) {
                    out.push(n);
                    if (out.length >= max) break;
                }
            }
            return out;
        }
        function renderSearchResultsList(nodes, query) {
            const container = document.getElementById('search-results');
            if (!container) return;
            container.innerHTML = '';
            if (!query || nodes.length === 0) {
                container.style.display = 'none';
                return;
            }
            const esc = escapeAttr;
            container.style.display = 'block';
            container.innerHTML = nodes.map(n => {
                const path = n.path || n.id || '';
                const kind = n.type === 'folder' ? 'Folder' : 'File';
                const icon = n.type === 'folder' ? '📁' : '📄';
                return `<div class="search-result-item" data-node-id="${esc(n.id)}">
                    <span class="search-result-icon">${icon}</span>
                    <div class="search-result-text">
                        <div class="search-result-name">${esc(n.name)}</div>
                        <div class="search-result-path">${esc(path || '/')}</div>
                        <div class="search-result-meta">${kind}</div>
                    </div>
                </div>`;
            }).join('');
        }
        function handleSearchSelect(nodeId) {
            if (!nodeId) return;
            const node = nodesById.get(nodeId);
            if (!node) return;
            if (node.type === 'folder') {
                navigateTo(node.path || node.id, true);
                return;
            }
            const path = node.path || node.id;
            if (!path) return;
            focusFile(path);
        }
        function attachSearchHandlers() {
            const input = document.getElementById('search-input');
            const container = document.getElementById('search-results');
            const clearBtn = document.getElementById('search-clear-btn');
            if (!input || !container) return;
            input.addEventListener('input', () => {
                const query = input.value.trim();
                if (!query) {
                    clearSearchUI();
                    return;
                }
                const matches = getSearchMatches(query, 30);
                renderSearchResultsList(matches, query);
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    clearSearchUI();
                }
            });
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    clearSearchUI();
                    input.focus();
                });
            }
            container.addEventListener('click', (e) => {
                const item = e.target.closest('.search-result-item');
                if (!item) return;
                const nodeId = item.getAttribute('data-node-id');
                handleSearchSelect(nodeId);
                container.style.display = 'none';
                input.blur();
            });
            document.addEventListener('click', (e) => {
                if (e.target === input || container.contains(e.target)) return;
                container.style.display = 'none';
            });
        }
        
        function updateBreadcrumb() {
            const parts = currentPath ? currentPath.split('/') : [];
            let html = `<span class="breadcrumb-item breadcrumb-folder" onclick="navigateTo('', true)">${graphData.rootName}</span>`;
            
            let accumulated = '';
            for (const part of parts) {
                accumulated += (accumulated ? '/' : '') + part;
                const p = accumulated;
                html += `<span class="breadcrumb-sep">/</span>`;
                html += `<span class="breadcrumb-item breadcrumb-folder" onclick="navigateTo('${p}', true)">${escapeAttr(part)}</span>`;
            }
            if (selectedNode && selectedNode.type !== 'folder') {
                const fileColor = getNodeColor(selectedNode);
                html += `<span class="breadcrumb-sep">/</span><span class="breadcrumb-file" style="color:${fileColor}">${escapeAttr(selectedNode.name)}</span>`;
            }
            
            document.getElementById('breadcrumb').innerHTML = html;
        }
        
        function renderGraph() {
            const g = window._graphG;
            if (!g) return;
            
            g.selectAll('*').remove();
            hideNodeTooltip();
            const width = document.getElementById('graph-container').clientWidth;
            const height = document.getElementById('graph-container').clientHeight;
            
            const changedPathSet = getMergedChangedPathSet();
            const folderHasChangedChildSet = getFolderHasChangedChildSet(graphData.nodes);
            
            // Normal view: children of current folder
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
                    .attr('fill', '#e7e7ee')
                    .text('Empty folder');
                return;
            }
            
            // Sort visibleNodes by connected components so linked nodes are placed next to each other
            (function sortByConnectedComponents() {
                const idToNode = new Map(visibleNodes.map(n => [n.id, n]));
                const adj = new Map();
                visibleNodes.forEach(n => adj.set(n.id, new Set()));
                visibleLinks.forEach(l => {
                    const srcId = typeof l.source === 'object' && l.source !== null ? l.source.id : l.source;
                    const tgtId = typeof l.target === 'object' && l.target !== null ? l.target.id : l.target;
                    if (idToNode.has(srcId) && idToNode.has(tgtId) && srcId !== tgtId) {
                        adj.get(srcId).add(tgtId);
                        adj.get(tgtId).add(srcId);
                    }
                });
                const compId = new Map();
                let compIndex = 0;
                visibleNodes.forEach(n => {
                    if (compId.has(n.id)) return;
                    const stack = [n.id];
                    compId.set(n.id, compIndex);
                    while (stack.length) {
                        const id = stack.pop();
                        for (const nb of adj.get(id)) {
                            if (!compId.has(nb)) {
                                compId.set(nb, compIndex);
                                stack.push(nb);
                            }
                        }
                    }
                    compIndex++;
                });
                visibleNodes.forEach(n => { n._comp = compId.has(n.id) ? compId.get(n.id) : compIndex; });
                visibleNodes.sort((a, b) => (a._comp - b._comp) || ((a.id || '').localeCompare(b.id || '')));
            })();
            
            // Pack layout: assign value (area) so folders are always 2x file radius
            simulation = null;
            visibleNodes.forEach(n => { n.value = getPackValue(n); });
            const root = { children: visibleNodes };
            const hierarchy = d3.hierarchy(root, d => (d === root ? d.children : null)).sum(d => d.value ?? 0);
            const PACK_PADDING = 12;
            d3.pack().size([width, height]).padding(PACK_PADDING)(hierarchy);
            hierarchy.children.forEach(c => {
                c.data.x = c.x;
                c.data.y = c.y;
                c.data.r = c.r;
            });
            const containerCenterX = hierarchy.x;
            const containerCenterY = hierarchy.y;
            const containerR = hierarchy.r;
            
            // Store container dimensions for use in updateSelection
            window._containerCenterX = containerCenterX;
            window._containerCenterY = containerCenterY;
            window._containerR = containerR;
            
            // Resolve link source/target to node objects (with x, y, r)
            const nodeById = new Map(visibleNodes.map(n => [n.id, n]));
            visibleLinks.forEach(l => {
                const srcId = typeof l.source === 'object' && l.source !== null ? l.source.id : l.source;
                const tgtId = typeof l.target === 'object' && l.target !== null ? l.target.id : l.target;
                if (nodeById.has(srcId)) l.source = nodeById.get(srcId);
                if (nodeById.has(tgtId)) l.target = nodeById.get(tgtId);
            });
            const resolvedLinks = visibleLinks.filter(l => l.source && l.target && l.source.x != null && l.target.x != null);
            
            // Draw container circle (current folder: gray fill, black stroke)
            // Clicking on it navigates back to parent folder
            g.append('circle')
                .attr('class', 'container-circle')
                .attr('cx', containerCenterX)
                .attr('cy', containerCenterY)
                .attr('r', hierarchy.r)
                .attr('fill', '#6b7280')
                .attr('stroke', '#111')
                .attr('stroke-width', 2)
                .style('cursor', 'pointer')
                .style('pointer-events', 'all')
                .on('click', function(event) {
                    event.stopPropagation();
                    const currentFolderPath = currentPath || '';
                    if (currentFolderPath) {
                        // Navigate to parent folder
                        const parentPath = getParentFolderPath(currentFolderPath);
                        navigateTo(parentPath, true);
                    }
                    // If already at root, do nothing
                })
                .lower();
            
            // Draw nodes (circle + folder label outside / file label inside)
            const node = g.append('g')
                .attr('class', 'nodes')
                .selectAll('g')
                .data(visibleNodes)
                .join('g')
                .attr('class', d => {
                    let cls = 'node ' + (d.type === 'folder' ? 'folder' : 'file');
                    if (selectedNode && d.id === selectedNode.id) cls += ' selected';
                    if (d.type === 'file' && changedPathSet.has(normPath(d.id))) cls += ' changed';
                    if (d.type === 'folder' && folderHasChangedChildSet.has(d.id)) cls += ' has-changed-child';
                    return cls;
                })
                .attr('data-id', d => d.id)
                .attr('transform', d => `translate(${d.x},${d.y})`)
                .on('click', (event, d) => {
                    event.stopPropagation();
                    if (d.type === 'folder') {
                        navigateTo(d.path || d.id, true);
                    } else {
                        clearSearchUI();
                        selectedNode = d;
                        pushHistory(d.id || d.path);
                        const parts = (d.path || d.id).split('/');
                        parts.pop();
                        currentPath = parts.join('/');
                        updateBreadcrumb();
                        renderGraph();
                        updateSelection();
                        renderSidePanel();
                        updateSidebarNav();
                    }
                })
                .on('mouseover', (event, d) => {
                    handleNodeMouseOver(event, d);
                })
                .on('mouseout', (event, d) => {
                    handleNodeMouseOut(event, d);
                });
            
            node.filter(d => d.type === 'folder')
                .on('mouseenter', function(event, d) {
                    if (!d.children || d.children.length === 0) return;
                    const children = d.children.map(id => nodesById.get(id)).filter(Boolean);
                    if (children.length === 0) return;
                    const size = Math.max(2 * d.r - 24, 24);
                    const root = { children: children.map(n => ({ ...n, value: 1 })) };
                    const hierarchy = d3.hierarchy(root, x => (x === root ? x.children : null)).sum(x => x.value ?? 0);
                    d3.pack().size([size, size]).padding(2)(hierarchy);
                    const center = size / 2;
                    const clipId = 'folder-clip-' + String(d.id || 'root').replace(/[^a-z0-9-_]/gi, '_');
                    const defs = d3.select('#graph').select('defs');
                    defs.append('clipPath').attr('id', clipId).append('circle').attr('r', d.r).attr('cx', 0).attr('cy', 0);
                    const overlay = d3.select(this).append('g').attr('class', 'folder-preview-overlay').attr('clip-path', 'url(#' + clipId + ')');
                    hierarchy.children.forEach(c => {
                        const nd = c.data;
                        const fill = nd.type === 'folder' ? '#6b7280' : getNodeColor(nd);
                        overlay.append('circle')
                            .attr('class', 'folder-preview-dot')
                            .attr('cx', c.x - center)
                            .attr('cy', c.y - center)
                            .attr('r', Math.max(c.r, 3))
                            .style('fill', fill)
                            .attr('stroke', 'none');
                    });
                })
                .on('mouseleave', function(event, d) {
                    d3.select(this).selectAll('.folder-preview-overlay').remove();
                    const clipId = 'folder-clip-' + String(d.id || 'root').replace(/[^a-z0-9-_]/gi, '_');
                    d3.select('#graph').select('defs').select('#' + clipId).remove();
                });
            
            node.append('circle')
                .attr('r', d => d.r)
                .attr('fill', d => d.type === 'folder' ? '#6b7280' : getNodeColor(d))
                .attr('stroke', d => d.type === 'folder' ? '#111' : (d3.color(getNodeColor(d))?.darker(0.5) || '#333'));
            
            // Folder and file labels: inside circle, 12px, truncated to fit
            node.each(function(d) {
                const maxChars = Math.max(1, Math.floor((d.r * 1.6) / 7));
                const label = d.name.length > maxChars ? d.name.slice(0, maxChars - 3) + '...' : d.name;
                d3.select(this).append('text')
                    .attr('class', 'node-label-inside')
                    .attr('x', 0)
                    .attr('y', 0)
                    .text(label);
            });
            
            // Draw same-level links as straight lines
            g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(resolvedLinks)
                .join('line')
                .attr('class', d => `link ${d.type}`)
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)')
                .style('pointer-events', 'none') // Links don't block clicks to container circle
                .attr('x1', d => d.source && d.source.x != null ? d.source.x : 0)
                .attr('y1', d => d.source && d.source.y != null ? d.source.y : 0)
                .attr('x2', d => {
                    if (!d.target || d.target.x == null) return 0;
                    const dx = d.target.x - (d.source?.x ?? 0);
                    const dy = d.target.y - (d.source?.y ?? 0);
                    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                    // Adjusted offset for 0.7x arrowhead size: reduced from 5 to 3.5 (0.7x of 5)
                    const targetR = (d.target.r != null ? d.target.r : getPackRadius(d.target)) + 3.5;
                    return d.target.x - (dx/dist) * targetR;
                })
                .attr('y2', d => {
                    if (!d.target || d.target.y == null) return 0;
                    const dx = d.target.x - (d.source?.x ?? 0);
                    const dy = d.target.y - (d.source?.y ?? 0);
                    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                    // Adjusted offset for 0.7x arrowhead size: reduced from 5 to 3.5 (0.7x of 5)
                    const targetR = (d.target.r != null ? d.target.r : getPackRadius(d.target)) + 3.5;
                    return d.target.y - (dy/dist) * targetR;
                });
            
            updateSelection();
            applyTourDimmingAndHighlight();
            
        }
        
        function getParentFolderPath(nodeId) {
            if (!nodeId) return '';
            const parts = String(nodeId).replace(/\\\\/g, '/').split('/').filter(Boolean);
            parts.pop();
            return parts.join('/');
        }
        
        
        function applyTourDimmingAndHighlight() {
            const gRef = window._graphG;
            if (!gRef) return;
            if (!window._tourActive || !window._tourSteps || !window._tourSteps.length) {
                gRef.selectAll('.node').attr('opacity', 1).classed('tour-dimmed', false);
                return;
            }
            const step = window._tourSteps[window._tourStepIndex];
            if (step.zoomOut || step.sidebarStep || step.noDimming || step.sizingStep || step.changesStep || step.aiSummaryStep || !step.nodeId) {
                gRef.selectAll('.node').attr('opacity', 1).classed('tour-dimmed', false);
                return;
            }
            const targetId = step.nodeId;
            gRef.selectAll('.node').attr('opacity', d => d.id === targetId ? 1 : 0.2).classed('tour-dimmed', d => d.id !== targetId);
        }
        
        function zoomToTourNode() {
            const g = window._graphG;
            const svg = window._graphSvg;
            const zoom = window._graphZoom;
            if (!g || !svg || !zoom || !window._tourSteps || !window._tourSteps.length) return;
            const targetId = window._tourSteps[window._tourStepIndex].nodeId;
            const nodeEl = g.selectAll('.node').filter(d => d.id === targetId);
            const d = nodeEl.datum();
            if (!d) return;
            const width = window._graphWidth || document.getElementById('graph-container').clientWidth;
            const height = window._graphHeight || document.getElementById('graph-container').clientHeight;
            const k = 1.5;
            const t = d3.zoomIdentity.translate(width / 2 - d.x * k, height / 2 - d.y * k).scale(k);
            svg.transition().duration(600).ease(d3.easeCubicInOut).call(zoom.transform, t);
        }
        
        function updateTourUI() {
            const progressEl = document.getElementById('tour-step-progress');
            const barFillEl = document.getElementById('tour-progress-bar-fill');
            const titleEl = document.getElementById('tour-step-title');
            const bodyEl = document.getElementById('tour-step-body');
            const dotsEl = document.getElementById('tour-progress-dots');
            const proTipEl = document.getElementById('tour-pro-tip');
            const backBtn = document.getElementById('tour-btn-back');
            const nextBtn = document.getElementById('tour-btn-next');
            const exitBtn = document.getElementById('tour-btn-exit');
            if (!progressEl || !titleEl || !bodyEl || !dotsEl || !backBtn || !nextBtn) return;
            const steps = window._tourSteps;
            const idx = window._tourStepIndex;
            const n = steps.length;
            progressEl.textContent = 'STEP ' + (idx + 1) + ' OF ' + n;
            if (barFillEl) barFillEl.style.width = (n > 0 ? ((idx + 1) / n) * 100 : 0) + '%';
            titleEl.textContent = steps[idx].title;
            bodyEl.style.display = '';
            bodyEl.textContent = steps[idx].body || 'Placeholder explanation for this step.';
            var isSidebarStep = steps[idx].sidebarStep === true;
            var allowGraphInteraction = steps[idx].allowGraphInteraction === true;
            var overlayEl = document.getElementById('tour-overlay');
            if (overlayEl) overlayEl.classList.toggle('tour-overlay-allow-graph-click', allowGraphInteraction);
            var fileInfoPanelEl = document.getElementById('file-info-panel');
            if (fileInfoPanelEl) fileInfoPanelEl.classList.toggle('tour-sidebar-highlight', isSidebarStep);
            if (proTipEl) {
                proTipEl.style.display = steps[idx].aiSummaryStep === true ? 'block' : 'none';
            }
            backBtn.style.display = isSidebarStep ? 'none' : '';
            nextBtn.style.display = '';
            if (exitBtn) exitBtn.textContent = 'Exit';
            backBtn.disabled = idx === 0;
            nextBtn.disabled = false;
            nextBtn.textContent = idx === n - 1 ? "I'm ready \u2192" : 'Next';
            dotsEl.innerHTML = '';
            for (let i = 0; i < n; i++) {
                const dot = document.createElement('div');
                dot.className = 'tour-progress-dot' + (i === idx ? ' active' : '');
                dotsEl.appendChild(dot);
            }
        }
        
        function getFallbackTourSteps() {
            const fileNodes = graphData.nodes.filter(n => n.type === 'file');
            const stepTitles = ['Entry Point', 'Core Logic', 'UI Layer', 'Config', 'Where to Start'];
            return fileNodes.slice(0, 5).map((n, i) => ({
                title: stepTitles[i] || 'Step ' + (i + 1),
                body: 'Placeholder explanation for this step.',
                nodeId: n.id
            }));
        }
        
        function getTourNodeWithMostLinks(tourNodeIds) {
            const links = graphData.links || [];
            var bestId = tourNodeIds[0] || null;
            var bestCount = -1;
            tourNodeIds.forEach(function(nodeId) {
                var count = 0;
                links.forEach(function(l) {
                    var src = typeof l.source === 'object' && l.source ? l.source.id : l.source;
                    var tgt = typeof l.target === 'object' && l.target ? l.target.id : l.target;
                    if (src === nodeId || tgt === nodeId) count++;
                });
                if (count > bestCount) { bestCount = count; bestId = nodeId; }
            });
            return bestId;
        }
        
        function getTourNodeWithInboundAndOutbound(tourNodeIds) {
            const links = graphData.links || [];
            var withBoth = null;
            var bestTotal = -1;
            var fallbackId = tourNodeIds[0] || null;
            tourNodeIds.forEach(function(nodeId) {
                var inbound = 0;
                var outbound = 0;
                links.forEach(function(l) {
                    var src = typeof l.source === 'object' && l.source ? l.source.id : l.source;
                    var tgt = typeof l.target === 'object' && l.target ? l.target.id : l.target;
                    if (tgt === nodeId) inbound++;
                    if (src === nodeId) outbound++;
                });
                var total = inbound + outbound;
                if (total > bestTotal) { bestTotal = total; fallbackId = nodeId; }
                if (inbound > 0 && outbound > 0 && !withBoth) withBoth = nodeId;
            });
            return withBoth !== null ? withBoth : fallbackId;
        }
        
        function zoomOutForTour() {
            const svg = window._graphSvg;
            const zoom = window._graphZoom;
            if (svg && zoom) {
                svg.transition().duration(600).ease(d3.easeCubicInOut).call(zoom.transform, d3.zoomIdentity);
            }
        }
        
        function deselectAndZoomOutToRoot() {
            navigateTo('', true);
            setTimeout(zoomOutForTour, 50);
        }
        
        function selectNodeForTour(nodeId) {
            if (!nodeId) return;
            if (window._tourStepIndex >= 6) return;
            var node = nodesById.get(nodeId);
            if (!node) node = graphData.nodes.find(function(n) { return (n.id || n.path) === nodeId; });
            if (!node) return;
            selectedNode = node;
            pushHistory(node.id || node.path || nodeId);
            var parts = (node.path || node.id || nodeId).split('/');
            parts.pop();
            currentPath = parts.length ? parts.join('/') : '';
            updateBreadcrumb();
            renderSidePanel();
            updateSelection();
            updateSidebarNav();
        }

        function runChangesStepDemo() {
            openChangesPanel();
            // Use the first tour step's nodeId as the demo file
            var firstStep = window._tourSteps && window._tourSteps[0];
            var nodeId = firstStep && firstStep.nodeId;
            if (!nodeId) return;
            var node = nodesById.get(nodeId) || graphData.nodes.find(function(n) { return (n.id || n.path) === nodeId; });
            if (!node) return;
            selectedNode = node;
            pushHistory(node.id || node.path || nodeId);
            var parts = (node.path || node.id || nodeId).split('/');
            parts.pop();
            currentPath = parts.length ? parts.join('/') : '';
            updateBreadcrumb();
            renderSidePanel();
            updateSelection();
            updateSidebarNav();
            setTimeout(function() {
                var panel = document.getElementById('recent-changes-panel');
                if (!panel) return;
                panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                panel.classList.add('tour-changes-highlight');
            }, 500);
        }

        function runAiSummaryStepDemo() {
            closeChangesPanel();
            openFilePanel();
            // Clear changes highlight from the previous step
            var changesPanel = document.getElementById('recent-changes-panel');
            if (changesPanel) changesPanel.classList.remove('tour-changes-highlight');
            // Use the first tour step's nodeId as the demo file
            var firstStep = window._tourSteps && window._tourSteps[0];
            var nodeId = firstStep && firstStep.nodeId;
            if (!nodeId) return;
            var node = nodesById.get(nodeId) || graphData.nodes.find(function(n) { return (n.id || n.path) === nodeId; });
            if (!node) return;
            selectedNode = node;
            pushHistory(node.id || node.path || nodeId);
            var parts = (node.path || node.id || nodeId).split('/');
            parts.pop();
            currentPath = parts.length ? parts.join('/') : '';
            updateBreadcrumb();
            renderSidePanel();
            updateSelection();
            updateSidebarNav();
            setTimeout(function() {
                var section = document.querySelector('#details-panel .ai-summary-section');
                if (!section) return;
                section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                section.classList.add('tour-ai-summary-highlight');
                var overviewTab = section.querySelector('.ai-summary-tab[data-mode=\"overview\"]');
                if (overviewTab) overviewTab.click();
            }, 500);
        }
        
        function startTourWithSteps(apiSteps) {
            const introEl = document.getElementById('tour-intro');
            const stepViewEl = document.getElementById('tour-step-view');
            if (introEl) introEl.style.display = 'none';
            if (stepViewEl) stepViewEl.style.display = 'block';
            if (Array.isArray(apiSteps) && apiSteps.length > 0) {
                window._tourSteps = apiSteps.map(s => ({
                    nodeId: (s.nodeId || '').replace(/\\\\/g, '/'),
                    title: s.title || 'Step',
                    body: s.explanation || s.body || 'Key file in the codebase.'
                }));
            } else {
                window._tourSteps = getFallbackTourSteps();
            }
            var fileStepIds = window._tourSteps.slice(0, 5).map(function(s) { return s.nodeId; }).filter(Boolean);
            var arrowsNodeId = fileStepIds.length ? getTourNodeWithInboundAndOutbound(fileStepIds) : null;
            window._tourSteps.push(
                { title: 'Follow the Arrows', body: 'See the arrows on this file? Lines coming IN mean other files depend on it. Lines going OUT mean it imports others. Click around — explore the connections yourself.', nodeId: arrowsNodeId, noDimming: true, allowGraphInteraction: true },
                { title: 'Size = Importance', body: 'Notice how nodes are different sizes? The bigger the bubble, the more files depend on it. This is called PageRank. Zoom in and out — explore which files matter most in this codebase.', nodeId: null, noDimming: true, allowGraphInteraction: true, sizingStep: true },
                { title: 'Track Changes Live', body: 'Every time you save a file, Codescape detects what changed. This panel shows exactly which files have been modified on your branch, and you can still keep track of the previous changes, ordered from most recent at top, you have made in your working session.', nodeId: null, noDimming: true, allowGraphInteraction: true, changesStep: true },
                { title: 'Understand Any File Instantly', body: 'See those tabs? Click Overview to get a plain-English summary of any file. Impact shows what breaks if you change it. Edit safely warns you before you touch something critical. Read next tells you where to go next.', nodeId: null, noDimming: true, allowGraphInteraction: true, aiSummaryStep: true }
            );
            if (!window._tourSteps.length) return;
            window._tourActive = true;
            window._tourStepIndex = 0;
            const parentPath = getParentFolderPath(window._tourSteps[0].nodeId);
            navigateTo(parentPath || '', true);
            document.getElementById('tour-overlay').classList.add('active');
            updateTourUI();
            setTimeout(function() {
                zoomToTourNode();
                if (window._tourSteps[0].nodeId) setTimeout(function() { selectNodeForTour(window._tourSteps[0].nodeId); }, 700);
            }, 50);
        }
        
        function showTourIntro() {
            const fileCount = graphData.nodes.filter(function(n) { return n.type === 'file'; }).length;
            const folderCount = graphData.nodes.filter(function(n) { return n.type === 'folder'; }).length;
            const statEl = document.getElementById('tour-intro-stat');
            if (statEl) statEl.textContent = '📁 Analyzing ' + fileCount + ' files across ' + folderCount + ' folders';
            const introEl = document.getElementById('tour-intro');
            const stepViewEl = document.getElementById('tour-step-view');
            const loadingEl = document.getElementById('tour-intro-loading');
            const goBtn = document.getElementById('tour-intro-go');
            if (introEl) introEl.style.display = 'block';
            if (stepViewEl) stepViewEl.style.display = 'none';
            if (loadingEl) loadingEl.style.display = 'none';
            if (goBtn) { goBtn.style.display = ''; goBtn.disabled = false; }
            window._tourStepsPromise = fetch(window.location.origin + '/api/generate_tour', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes: graphData.nodes, links: graphData.links || [] })
            })
                .then(function(r) { return r.ok ? r.json() : Promise.reject(new Error('Failed to generate tour')); })
                .catch(function() { return null; });
            document.getElementById('tour-overlay').classList.add('active');
        }
        
        function introGo() {
            const goBtn = document.getElementById('tour-intro-go');
            const loadingEl = document.getElementById('tour-intro-loading');
            const promise = window._tourStepsPromise;
            if (!promise) {
                startTourWithSteps(null);
                return;
            }
            goBtn.style.display = 'none';
            if (loadingEl) loadingEl.style.display = 'flex';
            if (goBtn) goBtn.disabled = true;
            promise.then(function(steps) {
                if (loadingEl) loadingEl.style.display = 'none';
                if (goBtn) { goBtn.style.display = ''; goBtn.disabled = false; }
                startTourWithSteps(steps);
            });
        }
        
        function startTour() {
            showTourIntro();
        }
        
        function exitTour() {
            window._tourActive = false;
            window._tourStepsPromise = null;
            const overlayEl = document.getElementById('tour-overlay');
            if (overlayEl) overlayEl.classList.remove('tour-overlay-allow-graph-click');
            closeFilePanel();
            closeChangesPanel();
            const fileInfoPanelEl = document.getElementById('file-info-panel');
            if (fileInfoPanelEl) fileInfoPanelEl.classList.remove('tour-sidebar-highlight');
            var changesPanel = document.getElementById('recent-changes-panel');
            if (changesPanel) changesPanel.classList.remove('tour-changes-highlight');
            document.querySelectorAll('.ai-summary-section.tour-ai-summary-highlight').forEach(function(el) {
                el.classList.remove('tour-ai-summary-highlight');
            });
            const introEl = document.getElementById('tour-intro');
            const stepViewEl = document.getElementById('tour-step-view');
            if (introEl) introEl.style.display = 'none';
            if (stepViewEl) stepViewEl.style.display = 'block';
            document.getElementById('tour-overlay').classList.remove('active');
            navigateTo('', true);
            setTimeout(function() {
                const svg = window._graphSvg;
                const zoom = window._graphZoom;
                if (svg && zoom) {
                    svg.transition().duration(400).ease(d3.easeCubicInOut).call(zoom.transform, d3.zoomIdentity);
                }
            }, 0);
        }
        
        function tourNext() {
            const n = window._tourSteps.length;
            if (window._tourStepIndex >= n - 1) {
                exitTour();
                return;
            }
            var leavingStep = window._tourSteps[window._tourStepIndex];
            if (leavingStep.changesStep) closeChangesPanel();
            if (leavingStep.aiSummaryStep) closeFilePanel();
            const panelInner = document.getElementById('tour-panel-inner');
            if (panelInner) panelInner.classList.add('tour-content-fade-out');
            setTimeout(function() {
                window._tourStepIndex++;
                const step = window._tourSteps[window._tourStepIndex];
                updateTourUI();
                if (step.zoomOut) {
                    zoomOutForTour();
                } else if (step.sizingStep) {
                    deselectAndZoomOutToRoot();
                } else if (step.sidebarStep) {
                    // No navigation, no zoom; sidebar highlight is applied in updateTourUI
                } else if (step.changesStep) {
                    runChangesStepDemo();
                } else if (step.aiSummaryStep) {
                    runAiSummaryStepDemo();
                } else if (step.nodeId) {
                    const parentPath = getParentFolderPath(step.nodeId);
                    navigateTo(parentPath || '', true);
                    setTimeout(function() {
                        zoomToTourNode();
                        if (window._tourStepIndex <= 5 && step.nodeId) setTimeout(function() { selectNodeForTour(step.nodeId); }, 700);
                    }, 0);
                }
                if (panelInner) panelInner.classList.remove('tour-content-fade-out');
            }, 150);
        }
        
        function tourBack() {
            if (window._tourStepIndex <= 0) return;
            var leavingStep = window._tourSteps[window._tourStepIndex];
            if (leavingStep.changesStep) closeChangesPanel();
            if (leavingStep.aiSummaryStep) closeFilePanel();
            const panelInner = document.getElementById('tour-panel-inner');
            if (panelInner) panelInner.classList.add('tour-content-fade-out');
            setTimeout(function() {
                window._tourStepIndex--;
                const step = window._tourSteps[window._tourStepIndex];
                updateTourUI();
                if (step.zoomOut) {
                    zoomOutForTour();
                } else if (step.sizingStep) {
                    deselectAndZoomOutToRoot();
                } else if (step.sidebarStep) {
                    // No navigation; sidebar highlight is removed in updateTourUI when we leave this step
                } else if (step.changesStep) {
                    runChangesStepDemo();
                } else if (step.aiSummaryStep) {
                    runAiSummaryStepDemo();
                } else if (step.nodeId) {
                    const parentPath = getParentFolderPath(step.nodeId);
                    navigateTo(parentPath || '', true);
                    setTimeout(function() {
                        zoomToTourNode();
                        if (window._tourStepIndex <= 5 && step.nodeId) setTimeout(function() { selectNodeForTour(step.nodeId); }, 700);
                    }, 0);
                }
                if (panelInner) panelInner.classList.remove('tour-content-fade-out');
            }, 150);
        }
        
        function getRelativePathFromFile(selectedFilePath, targetFilePath) {
            // Calculate relative path from selected file to target file
            // Example: selectedFilePath = "client/src/redux/root-saga.ts"
            //          targetFilePath = "client/src/redux/settings/index.js"
            //          Result: "../settings/index.js"
            
            if (!selectedFilePath || !targetFilePath) return '../';
            
            // Normalize paths (remove leading/trailing slashes, handle root name)
            const normalizePath = (path) => {
                let normalized = path.replace(/^\/+|\/+$/g, ''); // Remove leading/trailing slashes
                // Remove root name prefix if present
                if (graphData.rootName && normalized.startsWith(graphData.rootName + '/')) {
                    normalized = normalized.substring(graphData.rootName.length + 1);
                }
                return normalized.split('/').filter(Boolean);
            };
            
            const selectedParts = normalizePath(selectedFilePath);
            const targetParts = normalizePath(targetFilePath);
            
            // Remove filename from selected file path to get its directory
            const selectedDirParts = selectedParts.slice(0, -1);
            
            // Find common prefix
            let commonLength = 0;
            while (commonLength < selectedDirParts.length && commonLength < targetParts.length && 
                   selectedDirParts[commonLength] === targetParts[commonLength]) {
                commonLength++;
            }
            
            // Calculate up-levels needed (go up from selected file's directory)
            const upLevels = selectedDirParts.length - commonLength;
            const downPath = targetParts.slice(commonLength);
            
            // Build relative path
            const upPath = upLevels > 0 ? '../'.repeat(upLevels) : '';
            const relativePath = upPath + (downPath.length > 0 ? downPath.join('/') : '');
            return relativePath || './' + targetParts[targetParts.length - 1];
        }
        
        function getOrCreateColoredArrowhead(color) {
            // Create a unique marker ID based on color
            const colorId = color.replace('#', '').replace(/[^a-z0-9]/gi, '');
            const markerId = `arrowhead-colored-${colorId}`;
            
            // Check if marker already exists
            const svg = window._graphSvg;
            if (!svg) return 'url(#arrowhead-cross-level)';
            
            const existingMarker = svg.select(`#${markerId}`);
            if (!existingMarker.empty()) {
                return `url(#${markerId})`;
            }
            
            // Create new colored marker
            const defs = svg.select('defs');
            defs.append('marker')
                .attr('id', markerId)
                .attr('markerWidth', 7)
                .attr('markerHeight', 4.9)
                .attr('refX', 7)
                .attr('refY', 2.45)
                .attr('orient', 'auto')
                .append('polygon')
                .attr('points', '0 0, 7 2.45, 0 4.9')
                .attr('fill', color);
            
            return `url(#${markerId})`;
        }
        
        // Helper function to show folder preview overlay persistently
        function showFolderPreviewOverlay(folderNode, g) {
            if (!folderNode || !folderNode.children || folderNode.children.length === 0) return;
            if (!g) return;
            
            try {
                const folderElement = g.select(`.node[data-id="${folderNode.id}"]`);
                if (folderElement.empty()) return;
                
                // Check if overlay already exists
                if (!folderElement.select('.folder-preview-overlay-persistent').empty()) return;
                
                const children = folderNode.children.map(id => nodesById.get(id)).filter(Boolean);
                if (children.length === 0) return;
                
                // Get folder radius - use from node data or calculate
                const folderR = folderNode.r || getPackRadius(folderNode);
                const size = Math.max(2 * folderR - 24, 24);
                const root = { children: children.map(n => ({ ...n, value: 1 })) };
                const hierarchy = d3.hierarchy(root, x => (x === root ? x.children : null)).sum(x => x.value ?? 0);
                d3.pack().size([size, size]).padding(2)(hierarchy);
                const center = size / 2;
                const clipId = 'folder-clip-persistent-' + String(folderNode.id || 'root').replace(/[^a-z0-9-_]/gi, '_');
                const defs = d3.select('#graph').select('defs');
                if (!defs.empty() && defs.select('#' + clipId).empty()) {
                    defs.append('clipPath').attr('id', clipId).append('circle').attr('r', folderR).attr('cx', 0).attr('cy', 0);
                }
                const overlay = folderElement.append('g')
                    .attr('class', 'folder-preview-overlay-persistent')
                    .attr('clip-path', 'url(#' + clipId + ')');
                if (hierarchy.children) {
                    hierarchy.children.forEach(c => {
                        const nd = c.data;
                        const fill = nd.type === 'folder' ? '#6b7280' : getNodeColor(nd);
                        overlay.append('circle')
                            .attr('class', 'folder-preview-dot')
                            .attr('cx', c.x - center)
                            .attr('cy', c.y - center)
                            .attr('r', Math.max(c.r, 3))
                            .style('fill', fill)
                            .attr('stroke', 'none');
                    });
                }
            } catch (e) {
                console.error('Error showing folder preview overlay:', e);
            }
        }
        
        function updateSelection() {
            const g = window._graphG;
            if (!g) return;
            
            const sid = selectedNode ? selectedNode.id : null;
            const isFileSelected = selectedNode && selectedNode.type !== 'folder';
            g.selectAll('.node')
                .classed('selected', d => d.id === sid);
            
            // Remove existing outside nodes and cross-level arrows
            g.selectAll('.outside-node').remove();
            g.selectAll('.link-cross-level').remove();
            
            // Remove all persistent folder preview overlays
            g.selectAll('.folder-preview-overlay-persistent').remove();
            // Remove persistent nested file circles
            g.selectAll('.nested-file-circle-persistent').remove();
            try {
                const defs = d3.select('#graph').select('defs');
                if (!defs.empty()) {
                    defs.selectAll('clipPath[id^="folder-clip-persistent-"]').remove();
                }
            } catch (e) {
                // Ignore errors in cleanup
            }
            
            // Track folders that should show preview overlays
            const foldersToShow = new Set();
            
            // When a file is selected, show persistent hover views for all parent folders up the hierarchy
            if (isFileSelected && selectedNode) {
                const selectedPath = selectedNode.path || selectedNode.id || '';
                let currentParentPath = getParentFolderPath(selectedPath);
                let level = 0;
                const maxLevels = 20; // Safety limit
                
                // Walk up the hierarchy and add all parent folders
                while (level < maxLevels) {
                    // Check if we've reached root (empty path means root)
                    if (!currentParentPath || currentParentPath === '') {
                        // Add root if it exists
                        const rootNode = nodesById.get('root');
                        if (rootNode && rootNode.type === 'folder' && rootNode.id) {
                            foldersToShow.add(rootNode.id);
                        }
                        break;
                    }
                    
                    // Try to find folder by path
                    let parentFolderNode = nodesById.get(currentParentPath);
                    if (!parentFolderNode) {
                        // Also try by ID if path doesn't match
                        for (const [id, node] of nodesById.entries()) {
                            if (node.path === currentParentPath || id === currentParentPath) {
                                parentFolderNode = node;
                                break;
                            }
                        }
                    }
                    
                    if (parentFolderNode && parentFolderNode.type === 'folder' && parentFolderNode.id) {
                        foldersToShow.add(parentFolderNode.id);
                    }
                    
                    // Get next parent
                    const nextParentPath = getParentFolderPath(currentParentPath);
                    if (nextParentPath === currentParentPath || !nextParentPath) {
                        // Reached root or no change
                        const rootNode = nodesById.get('root');
                        if (rootNode && rootNode.type === 'folder' && rootNode.id) {
                            foldersToShow.add(rootNode.id);
                        }
                        break;
                    }
                    
                    currentParentPath = nextParentPath;
                    level++;
                }
            }
            
            // Build list of cross-level dependency paths to exclude from same-level links
            let crossLevelDepPaths = new Set();
            let crossLevelDepNodeIds = new Set();
            if (isFileSelected && selectedNode) {
                const currentFolderPath = (selectedNode.path || '').split('/').slice(0, -1).join('/');
                const dependencies = selectedNode.dependencies || [];
                const dependents = selectedNode.dependents || [];
                
                // Mark cross-level dependencies (not in same folder)
                dependencies.forEach(depPath => {
                    const depParent = getParentFolderPath(depPath);
                    if (depParent !== currentFolderPath) {
                        crossLevelDepPaths.add(depPath);
                        // Also add the node ID if we can find it
                        const depNode = nodesById.get(depPath);
                        if (depNode && depNode.id) {
                            crossLevelDepNodeIds.add(depNode.id);
                        }
                    }
                });
                dependents.forEach(depPath => {
                    const depParent = getParentFolderPath(depPath);
                    if (depParent !== currentFolderPath) {
                        crossLevelDepPaths.add(depPath);
                        // Also add the node ID if we can find it
                        const depNode = nodesById.get(depPath);
                        if (depNode && depNode.id) {
                            crossLevelDepNodeIds.add(depNode.id);
                        }
                    }
                });
            }
            
            // Update same-level links (lines) - hide cross-level ones, they'll be drawn separately
            g.selectAll('.links .link')
                .classed('visible', d => {
                    if (!sid || !isFileSelected) return false;
                    const sourceId = typeof d.source === 'object' && d.source !== null ? d.source.id : d.source;
                    const targetId = typeof d.target === 'object' && d.target !== null ? d.target.id : d.target;
                    const sourceNode = typeof d.source === 'object' ? d.source : nodesById.get(sourceId);
                    const targetNode = typeof d.target === 'object' ? d.target : nodesById.get(targetId);
                    
                    // Hide if this is a cross-level dependency
                    // Check by path, ID, or normalized path
                    const targetPath = targetNode ? (targetNode.path || targetNode.id || '') : '';
                    const sourcePath = sourceNode ? (sourceNode.path || sourceNode.id || '') : '';
                    const targetPathNorm = targetPath.replace(/\\\\/g, '/');
                    const sourcePathNorm = sourcePath.replace(/\\\\/g, '/');
                    
                    if (sourceId === sid && targetNode && 
                        (crossLevelDepPaths.has(targetPath) || 
                         crossLevelDepPaths.has(targetPathNorm) ||
                         crossLevelDepNodeIds.has(targetId) ||
                         crossLevelDepPaths.has(targetNode.id))) {
                        return false;
                    }
                    if (targetId === sid && sourceNode && 
                        (crossLevelDepPaths.has(sourcePath) || 
                         crossLevelDepPaths.has(sourcePathNorm) ||
                         crossLevelDepNodeIds.has(sourceId) ||
                         crossLevelDepPaths.has(sourceNode.id))) {
                        return false;
                    }
                    
                    return sourceId === sid || targetId === sid;
                })
                .classed('inbound', d => {
                    if (!isFileSelected || !sid) return false;
                    const targetVal = typeof d.target === 'object' && d.target !== null ? (d.target.id || d.target.path) : d.target;
                    const sourceVal = typeof d.source === 'object' && d.source !== null ? (d.source.id || d.source.path) : d.source;
                    const targetMatches = (targetVal === sid || (d.target && (d.target.path || d.target.id) === sid));
                    const sourceMatches = (sourceVal === sid || (d.source && (d.source.path || d.source.id) === sid));
                    return targetMatches && !sourceMatches;
                })
                .classed('outbound', d => {
                    if (!isFileSelected || !sid) return false;
                    const sourceVal = typeof d.source === 'object' && d.source !== null ? (d.source.id || d.source.path) : d.source;
                    const targetVal = typeof d.target === 'object' && d.target !== null ? (d.target.id || d.target.path) : d.target;
                    const sourceMatches = (sourceVal === sid || (d.source && (d.source.path || d.source.id) === sid));
                    const targetMatches = (targetVal === sid || (d.target && (d.target.path || d.target.id) === sid));
                    return sourceMatches && !targetMatches;
                })
                .classed('dep-arrow', isFileSelected)
                .attr('marker-end', d => {
                    if (!isFileSelected) return 'url(#arrowhead)';
                    const sourceId = typeof d.source === 'object' && d.source !== null ? (d.source.id || d.source.path) : d.source;
                    const targetId = typeof d.target === 'object' && d.target !== null ? (d.target.id || d.target.path) : d.target;
                    if (targetId === sid || (d.target && d.target.path === sid)) return 'url(#arrowhead-inbound)';
                    if (sourceId === sid || (d.source && d.source.path === sid)) return 'url(#arrowhead-outbound)';
                    return 'url(#arrowhead-outbound)';
                });
            
            // Show cross-level dependencies - either as direct connections or external nodes
            if (isFileSelected && selectedNode) {
                const currentFolderPath = (selectedNode.path || '').split('/').slice(0, -1).join('/');
                const dependencies = selectedNode.dependencies || [];
                const dependents = selectedNode.dependents || [];
                
                // Get visible nodes in current layer (for checking if dependency exists in layer)
                const currentFolder = nodesById.get(currentPath || 'root');
                const visibleNodeIds = currentFolder && currentFolder.children ? new Set(currentFolder.children) : new Set();
                
                // Build a map of all nodes visible in current layer (including nested)
                const visibleNodesMap = new Map();
                const allVisibleNodes = [];
                
                // Function to recursively collect all nodes in visible folders
                function collectVisibleNodes(nodeId) {
                    const node = nodesById.get(nodeId);
                    if (!node) return;
                    
                    // Add this node to map with multiple key formats
                    if (node.id) {
                        visibleNodesMap.set(node.id, node);
                        const normalizedId = node.id.replace(/\\\\/g, '/');
                        visibleNodesMap.set(normalizedId, node);
                    }
                    if (node.path) {
                        visibleNodesMap.set(node.path, node);
                        const normalizedPath = node.path.replace(/\\\\/g, '/');
                        visibleNodesMap.set(normalizedPath, node);
                        
                        // Add path segments for flexible matching (e.g., "settings/index.js")
                        const pathParts = normalizedPath.split('/');
                        // Add last 2-3 segments for matching nested files
                        for (let i = Math.max(0, pathParts.length - 3); i < pathParts.length; i++) {
                            const segment = pathParts.slice(i).join('/');
                            if (segment && segment !== normalizedPath && segment.length > 0) {
                                visibleNodesMap.set(segment, node);
                            }
                        }
                    }
                    allVisibleNodes.push(node);
                    
                    // If it's a folder with children, recursively collect children
                    if (node.type === 'folder' && node.children) {
                        node.children.forEach(childId => {
                            collectVisibleNodes(childId);
                        });
                    }
                }
                
                // Collect all visible nodes starting from direct children
                visibleNodeIds.forEach(nodeId => {
                    collectVisibleNodes(nodeId);
                });
                
                // Get container dimensions
                const containerCx = window._containerCenterX;
                const containerCy = window._containerCenterY;
                const containerR = window._containerR;
                
                if (containerCx && containerCy && containerR) {
                    // Find cross-level dependencies (outbound) - dependencies not in current folder
                    const crossLevelDeps = dependencies.filter(depPath => {
                        const depParent = getParentFolderPath(depPath);
                        return depParent !== currentFolderPath;
                    });
                    
                    // Find cross-level dependents (inbound) - dependents not in current folder
                    const crossLevelDependents = dependents.filter(depPath => {
                        const depParent = getParentFolderPath(depPath);
                        return depParent !== currentFolderPath;
                    });
                    
                    // Collect folders for ALL dependencies that point to files inside visible folders
                    dependencies.forEach(depPath => {
                        try {
                            const depParentFolder = getParentFolderPath(depPath);
                            const depParentFolderNode = visibleNodesMap.get(depParentFolder) || nodesById.get(depParentFolder);
                            if (depParentFolderNode && depParentFolderNode.type === 'folder' && depParentFolderNode.id) {
                                foldersToShow.add(depParentFolderNode.id);
                            }
                        } catch (e) {
                            // Ignore errors
                        }
                    });
                    
                    // Collect folders for ALL dependents that point to files inside visible folders
                    dependents.forEach(depPath => {
                        try {
                            const depParentFolder = getParentFolderPath(depPath);
                            const depParentFolderNode = visibleNodesMap.get(depParentFolder) || nodesById.get(depParentFolder);
                            if (depParentFolderNode && depParentFolderNode.type === 'folder' && depParentFolderNode.id) {
                                foldersToShow.add(depParentFolderNode.id);
                            }
                        } catch (e) {
                            // Ignore errors
                        }
                    });
                    
                    // Get selected node position
                    const selectedNodeElement = g.select(`.node[data-id="${sid}"]`);
                    if (!selectedNodeElement.empty()) {
                        const selectedX = parseFloat(selectedNodeElement.select('circle').attr('cx')) || selectedNode.x || 0;
                        const selectedY = parseFloat(selectedNodeElement.select('circle').attr('cy')) || selectedNode.y || 0;
                        const selectedR = parseFloat(selectedNodeElement.select('circle').attr('r')) || getPackRadius(selectedNode);
                        
                        // Get selected node color for external nodes
                        const selectedNodeColor = getNodeColor(selectedNode);
                        
                        // Track external nodes count for positioning
                        let externalNodeIndex = 0;
                        
                        // Process outbound dependencies
                        crossLevelDeps.forEach((depPath) => {
                            // Look up the actual node data for the dependency
                            let depNode = nodesById.get(depPath);
                            if (!depNode) {
                                // Try with normalized path
                                const normalizedDepPath = depPath.replace(/\\\\/g, '/');
                                depNode = nodesById.get(normalizedDepPath);
                                if (!depNode) return; // Skip if node not found
                            }
                            
                            // Check if dependency exists in current layer (check multiple path formats)
                            // Try exact matches first
                            let targetNodeInLayer = visibleNodesMap.get(depPath) || 
                                                   visibleNodesMap.get(depNode.id) || 
                                                   visibleNodesMap.get(depNode.path);
                            
                            // Debug logging
                            if (!targetNodeInLayer && depPath.includes('settings')) {
                                console.log('Looking for dependency:', depPath);
                                console.log('Dep node ID:', depNode.id);
                                console.log('Dep node path:', depNode.path);
                                console.log('Visible nodes map size:', visibleNodesMap.size);
                                console.log('Sample visible node keys:', Array.from(visibleNodesMap.keys()).slice(0, 10));
                            }
                            
                            // If not found, try normalized paths
                            if (!targetNodeInLayer) {
                                const normalizedDepPath = depPath.replace(/\\\\/g, '/');
                                targetNodeInLayer = visibleNodesMap.get(normalizedDepPath);
                            }
                            if (!targetNodeInLayer && depNode.id) {
                                const normalizedId = depNode.id.replace(/\\\\/g, '/');
                                targetNodeInLayer = visibleNodesMap.get(normalizedId);
                            }
                            if (!targetNodeInLayer && depNode.path) {
                                const normalizedPath = depNode.path.replace(/\\\\/g, '/');
                                targetNodeInLayer = visibleNodesMap.get(normalizedPath);
                            }
                            
                            // Also check by comparing paths (in case formats differ)
                            // This handles cases where dependency path is full (e.g., "client/src/redux/settings/index.js")
                            // but visible node path is relative (e.g., "settings/index.js")
                            if (!targetNodeInLayer) {
                                const depPathNormalized = depPath.replace(/\\\\/g, '/').toLowerCase();
                                const depPathParts = depPathNormalized.split('/');
                                
                                // Try matching with last N segments of dependency path
                                for (let segCount = Math.min(4, depPathParts.length); segCount >= 1; segCount--) {
                                    const depSegment = depPathParts.slice(-segCount).join('/');
                                    targetNodeInLayer = visibleNodesMap.get(depSegment);
                                    if (targetNodeInLayer) break;
                                    
                                    // Also try case-insensitive match
                                    for (const [key, node] of visibleNodesMap.entries()) {
                                        const keyLower = key.toLowerCase();
                                        if (keyLower === depSegment || 
                                            keyLower.endsWith('/' + depSegment) ||
                                            depSegment.endsWith('/' + keyLower)) {
                                            targetNodeInLayer = node;
                                            break;
                                        }
                                    }
                                    if (targetNodeInLayer) break;
                                }
                                
                                // Final fallback: check if any visible node path ends with dependency path
                                if (!targetNodeInLayer) {
                                    for (const [key, node] of visibleNodesMap.entries()) {
                                        const nodePath = (node.path || node.id || '').replace(/\\\\/g, '/').toLowerCase();
                                        if (nodePath === depPathNormalized || 
                                            nodePath.endsWith('/' + depPathNormalized) ||
                                            depPathNormalized.endsWith('/' + nodePath)) {
                                            targetNodeInLayer = node;
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            if (targetNodeInLayer) {
                                // Check if target node is nested inside a folder (not directly visible)
                                const targetParentFolder = getParentFolderPath(targetNodeInLayer.path || targetNodeInLayer.id);
                                const parentFolderNode = visibleNodesMap.get(targetParentFolder) || nodesById.get(targetParentFolder);
                                
                                let targetX, targetY, targetR;
                                
                                // If target is nested inside a visible folder, calculate its position
                                if (parentFolderNode && parentFolderNode.type === 'folder' && 
                                    parentFolderNode.x !== undefined && parentFolderNode.y !== undefined) {
                                    // Get folder's children and calculate nested file position
                                    const folderChildren = (parentFolderNode.children || []).map(id => nodesById.get(id)).filter(Boolean);
                                    
                                    // Normalize paths for comparison
                                    const targetIdNorm = (targetNodeInLayer.id || '').replace(/\\\\/g, '/').toLowerCase();
                                    const targetPathNorm = (targetNodeInLayer.path || '').replace(/\\\\/g, '/').toLowerCase();
                                    const depPathNorm = depPath.replace(/\\\\/g, '/').toLowerCase();
                                    
                                    // Check if any child matches the target
                                    const matchingChild = folderChildren.find(c => {
                                        const cId = (c.id || '').replace(/\\\\/g, '/').toLowerCase();
                                        const cPath = (c.path || '').replace(/\\\\/g, '/').toLowerCase();
                                        return cId === targetIdNorm || cPath === targetPathNorm ||
                                               cId === depPathNorm || cPath === depPathNorm ||
                                               cId.endsWith('/' + targetIdNorm) || targetIdNorm.endsWith('/' + cId) ||
                                               cPath.endsWith('/' + targetPathNorm) || targetPathNorm.endsWith('/' + cPath) ||
                                               cId.endsWith('/' + depPathNorm) || depPathNorm.endsWith('/' + cId) ||
                                               cPath.endsWith('/' + depPathNorm) || depPathNorm.endsWith('/' + cPath);
                                    });
                                    
                                    if (matchingChild && folderChildren.length > 0) {
                                        // Calculate pack layout for folder's children - MUST match showFolderPreviewOverlay exactly
                                        const folderR = parentFolderNode.r || getPackRadius(parentFolderNode);
                                        const size = Math.max(2 * folderR - 24, 24);
                                        const root = { children: folderChildren.map(n => ({ ...n, value: 1 })) };
                                        const hierarchy = d3.hierarchy(root, x => (x === root ? x.children : null)).sum(x => x.value ?? 0);
                                        d3.pack().size([size, size]).padding(2)(hierarchy);
                                        const center = size / 2;
                                        
                                        // Find the nested file in the hierarchy - match by reference or ID/path
                                        if (hierarchy.children) {
                                            for (let i = 0; i < hierarchy.children.length; i++) {
                                                const c = hierarchy.children[i];
                                                const childNode = c.data;
                                                const childId = (childNode.id || '').replace(/\\\\/g, '/').toLowerCase();
                                                const childPath = (childNode.path || '').replace(/\\\\/g, '/').toLowerCase();
                                                
                                                // Match by reference (same object) or by ID/path
                                                if (childNode === matchingChild ||
                                                    childId === targetIdNorm || childPath === targetPathNorm ||
                                                    childId === depPathNorm || childPath === depPathNorm ||
                                                    childId.endsWith('/' + targetIdNorm) || targetIdNorm.endsWith('/' + childId) ||
                                                    childPath.endsWith('/' + targetPathNorm) || targetPathNorm.endsWith('/' + childPath)) {
                                                    // Position is relative to folder center, convert to absolute
                                                    // This matches exactly how showFolderPreviewOverlay positions circles
                                                    targetX = parentFolderNode.x + (c.x - center);
                                                    targetY = parentFolderNode.y + (c.y - center);
                                                    targetR = Math.max(c.r, 3);
                                                    
                                                    // Add persistent orange circle at nested file position
                                                    const folderElement = g.select(`.node[data-id="${parentFolderNode.id}"]`);
                                                    if (!folderElement.empty()) {
                                                        const nestedFileColor = getNodeColor(matchingChild);
                                                        const circleRadius = Math.max(c.r, 3);
                                                        const circleGroup = folderElement.append('g')
                                                            .attr('class', 'nested-file-circle-persistent')
                                                            .attr('transform', `translate(${c.x - center}, ${c.y - center})`)
                                                            .style('pointer-events', 'none');
                                                        
                                                        // Add circle
                                                        circleGroup.append('circle')
                                                            .attr('r', circleRadius)
                                                            .style('fill', nestedFileColor)
                                                            .attr('stroke', 'none');
                                                        
                                                        // Add text label
                                                        const fileName = matchingChild.name || matchingChild.id || '';
                                                        const maxChars = Math.max(1, Math.floor((circleRadius * 2) / 4));
                                                        const label = fileName.length > maxChars ? fileName.slice(0, maxChars - 3) + '...' : fileName;
                                                        circleGroup.append('text')
                                                            .attr('text-anchor', 'middle')
                                                            .attr('dominant-baseline', 'middle')
                                                            .attr('fill', '#ffffff')
                                                            .attr('font-size', Math.max(4, circleRadius * 0.35) + 'px')
                                                            .attr('font-weight', '500')
                                                            .style('pointer-events', 'none')
                                                            .text(label);
                                                    }
                                                    
                                                    break; // Found it, stop searching
                                                }
                                            }
                                        }
                                        
                                        // Mark folder for preview overlay
                                        if (parentFolderNode && parentFolderNode.id) {
                                            foldersToShow.add(parentFolderNode.id);
                                        }
                                    }
                                }
                                
                                // If not nested or calculation failed, try to find as direct node
                                if (targetX === undefined || targetY === undefined) {
                                    // Get the actual rendered position from DOM
                                    let targetNodeElement = g.select(`.node[data-id="${targetNodeInLayer.id}"]`);
                                    if (targetNodeElement.empty() && targetNodeInLayer.path) {
                                        targetNodeElement = g.select(`.node[data-id="${targetNodeInLayer.path}"]`);
                                    }
                                    if (targetNodeElement.empty() && targetNodeInLayer.id) {
                                        const normalizedId = targetNodeInLayer.id.replace(/\\\\/g, '/');
                                        targetNodeElement = g.select(`.node[data-id="${normalizedId}"]`);
                                    }
                                    if (targetNodeElement.empty()) {
                                        // Try finding by iterating through all nodes
                                        g.selectAll('.node').each(function() {
                                            const d = d3.select(this).datum();
                                            if (d) {
                                                const dId = d.id || '';
                                                const dPath = d.path || '';
                                                const targetId = targetNodeInLayer.id || '';
                                                const targetPath = targetNodeInLayer.path || '';
                                                
                                                if (dId === targetId || dPath === targetPath || 
                                                    dId === targetPath || dPath === targetId ||
                                                    dId.endsWith('/' + targetId) || targetId.endsWith('/' + dId) ||
                                                    dPath.endsWith('/' + targetPath) || targetPath.endsWith('/' + dPath)) {
                                                    targetNodeElement = d3.select(this);
                                                }
                                            }
                                        });
                                    }
                                    
                                    // Get coordinates - prefer DOM, fallback to data
                                    if (!targetNodeElement.empty()) {
                                        targetX = parseFloat(targetNodeElement.select('circle').attr('cx')) || targetNodeInLayer.x || 0;
                                        targetY = parseFloat(targetNodeElement.select('circle').attr('cy')) || targetNodeInLayer.y || 0;
                                        targetR = parseFloat(targetNodeElement.select('circle').attr('r')) || getPackRadius(targetNodeInLayer);
                                    } else if (targetNodeInLayer.x !== undefined && targetNodeInLayer.y !== undefined) {
                                        targetX = targetNodeInLayer.x || 0;
                                        targetY = targetNodeInLayer.y || 0;
                                        targetR = getPackRadius(targetNodeInLayer);
                                    } else {
                                        return; // Skip if no coordinates available
                                    }
                                }
                                
                                // Calculate arrow start/end points on node edges
                                const dx = targetX - selectedX;
                                const dy = targetY - selectedY;
                                const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                                const startX = selectedX + (dx/dist) * selectedR;
                                const startY = selectedY + (dy/dist) * selectedR;
                                const endX = targetX - (dx/dist) * targetR;
                                const endY = targetY - (dy/dist) * targetR;
                                
                                // Draw arrow from selected node to target node in layer
                                // Outbound cross-level: orange (same as same-level outbound)
                                const linkGroup = g.append('g').attr('class', 'link-cross-level');
                                linkGroup.append('line')
                                    .attr('x1', startX)
                                    .attr('y1', startY)
                                    .attr('x2', endX)
                                    .attr('y2', endY)
                                    .attr('stroke', '#f59e0b')
                                    .attr('stroke-width', 2)
                                    .attr('stroke-dasharray', '8 8')
                                    .attr('marker-end', 'url(#arrowhead-outbound)')
                                    .attr('class', 'link cross-level dep-arrow visible')
                                    .style('cursor', 'pointer')
                                    .style('opacity', 1)
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                // Mark folder for preview overlay if target is nested inside a folder
                                if (targetX !== undefined && targetY !== undefined && targetNodeInLayer) {
                                    try {
                                        const targetParentFolder = getParentFolderPath(targetNodeInLayer.path || targetNodeInLayer.id);
                                        const parentFolderNode = visibleNodesMap.get(targetParentFolder) || nodesById.get(targetParentFolder);
                                        if (parentFolderNode && parentFolderNode.type === 'folder' && parentFolderNode.id) {
                                            foldersToShow.add(parentFolderNode.id);
                                        }
                                    } catch (e) {
                                        console.error('Error tracking folder for preview:', e);
                                    }
                                }
                            } else {
                                // Behavior 2: Dependency doesn't exist in layer - show as external node
                                const relativePath = getRelativePathFromFile(selectedNode.path || selectedNode.id, depPath);
                                const totalExternalCount = crossLevelDeps.filter(d => !visibleNodesMap.get(d)).length + 
                                                          crossLevelDependents.filter(d => !visibleNodesMap.get(d)).length;
                                const angle = (Math.PI * 2 * externalNodeIndex) / Math.max(totalExternalCount, 1) - Math.PI / 2;
                                externalNodeIndex++;
                                
                                // Calculate actual node radius
                                const nodeRadius = getPackRadius(depNode);
                                const spacing = 50;
                                const outsideX = containerCx + Math.cos(angle) * (containerR + spacing + nodeRadius);
                                const outsideY = containerCy + Math.sin(angle) * (containerR + spacing + nodeRadius);
                                
                                // Calculate arrow start/end points on node edges
                                const dx = outsideX - selectedX;
                                const dy = outsideY - selectedY;
                                const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                                const startX = selectedX + (dx/dist) * selectedR;
                                const startY = selectedY + (dy/dist) * selectedR;
                                const endX = outsideX - (dx/dist) * nodeRadius;
                                const endY = outsideY - (dy/dist) * nodeRadius;
                                
                                // Draw arrow from selected node to outside node (outbound = orange)
                                const linkGroup = g.append('g').attr('class', 'link-cross-level');
                                linkGroup.append('line')
                                    .attr('x1', startX)
                                    .attr('y1', startY)
                                    .attr('x2', endX)
                                    .attr('y2', endY)
                                    .attr('stroke', '#f59e0b')
                                    .attr('stroke-width', 2)
                                    .attr('marker-end', 'url(#arrowhead-outbound)')
                                    .attr('class', 'link cross-level dep-arrow visible')
                                    .style('cursor', 'pointer')
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                // Create outside node with same color as selected node (outbound)
                                const outsideNodeGroup = g.append('g').attr('class', 'outside-node')
                                    .attr('data-id', depPath)
                                    .style('cursor', 'pointer')
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                // Use selected node's color for external node
                                const nodeColor = depNode.type === 'folder' ? '#6b7280' : selectedNodeColor;
                                const strokeColor = depNode.type === 'folder' ? '#111' : (d3.color(selectedNodeColor)?.darker(0.5) || '#333');
                                outsideNodeGroup.append('circle')
                                    .attr('cx', outsideX)
                                    .attr('cy', outsideY)
                                    .attr('r', nodeRadius)
                                    .attr('fill', nodeColor)
                                    .attr('stroke', strokeColor)
                                    .attr('stroke-width', depNode.type === 'folder' ? 2 : 1);
                                
                                // Label inside circle (like regular nodes)
                                const maxChars = Math.max(1, Math.floor((nodeRadius * 1.6) / 7));
                                const label = depNode.name.length > maxChars ? depNode.name.slice(0, maxChars - 3) + '...' : depNode.name;
                                outsideNodeGroup.append('text')
                                    .attr('class', 'node-label-inside')
                                    .attr('x', outsideX)
                                    .attr('y', outsideY)
                                    .attr('text-anchor', 'middle')
                                    .attr('dominant-baseline', 'middle')
                                    .attr('fill', '#ffffff')
                                    .attr('font-size', '12px')
                                    .attr('font-weight', '500')
                                    .text(label);
                                
                                // Relative path label below node
                                outsideNodeGroup.append('text')
                                    .attr('x', outsideX)
                                    .attr('y', outsideY + nodeRadius + 18)
                                    .attr('text-anchor', 'middle')
                                    .attr('fill', selectedNodeColor)
                                    .attr('font-size', '10px')
                                    .attr('font-family', 'JetBrains Mono, monospace')
                                    .text(relativePath || '../');
                                
                                // Mark folder for preview overlay if dependency is inside a visible folder
                                try {
                                    const depParentFolder = getParentFolderPath(depPath);
                                    const depParentFolderNode = visibleNodesMap.get(depParentFolder) || nodesById.get(depParentFolder);
                                    if (depParentFolderNode && depParentFolderNode.type === 'folder' && depParentFolderNode.id) {
                                        foldersToShow.add(depParentFolderNode.id);
                                    }
                                } catch (e) {
                                    console.error('Error tracking folder for preview:', e);
                                }
                            }
                        });
                        
                        // Process inbound dependencies
                        crossLevelDependents.forEach((depPath) => {
                            // Look up the actual node data for the dependency
                            let depNode = nodesById.get(depPath);
                            if (!depNode) {
                                const normalizedDepPath = depPath.replace(/\\\\/g, '/');
                                depNode = nodesById.get(normalizedDepPath);
                                if (!depNode) return;
                            }
                            
                            // Check if dependency exists in current layer
                            let sourceNodeInLayer = visibleNodesMap.get(depPath) || 
                                                   visibleNodesMap.get(depNode.id) || 
                                                   visibleNodesMap.get(depNode.path);
                            
                            if (!sourceNodeInLayer) {
                                const normalizedDepPath = depPath.replace(/\\\\/g, '/');
                                sourceNodeInLayer = visibleNodesMap.get(normalizedDepPath);
                            }
                            if (!sourceNodeInLayer && depNode.id) {
                                const normalizedId = depNode.id.replace(/\\\\/g, '/');
                                sourceNodeInLayer = visibleNodesMap.get(normalizedId);
                            }
                            if (!sourceNodeInLayer && depNode.path) {
                                const normalizedPath = depNode.path.replace(/\\\\/g, '/');
                                sourceNodeInLayer = visibleNodesMap.get(normalizedPath);
                            }
                            
                            // Also check by comparing paths
                            if (!sourceNodeInLayer) {
                                const depPathNormalized = depPath.replace(/\\\\/g, '/').toLowerCase();
                                const depPathParts = depPathNormalized.split('/');
                                
                                for (let segCount = Math.min(4, depPathParts.length); segCount >= 1; segCount--) {
                                    const depSegment = depPathParts.slice(-segCount).join('/');
                                    sourceNodeInLayer = visibleNodesMap.get(depSegment);
                                    if (sourceNodeInLayer) break;
                                    
                                    for (const [key, node] of visibleNodesMap.entries()) {
                                        const keyLower = key.toLowerCase();
                                        if (keyLower === depSegment || 
                                            keyLower.endsWith('/' + depSegment) ||
                                            depSegment.endsWith('/' + keyLower)) {
                                            sourceNodeInLayer = node;
                                            break;
                                        }
                                    }
                                    if (sourceNodeInLayer) break;
                                }
                                
                                if (!sourceNodeInLayer) {
                                    for (const [key, node] of visibleNodesMap.entries()) {
                                        const nodePath = (node.path || node.id || '').replace(/\\\\/g, '/').toLowerCase();
                                        if (nodePath === depPathNormalized || 
                                            nodePath.endsWith('/' + depPathNormalized) ||
                                            depPathNormalized.endsWith('/' + nodePath)) {
                                            sourceNodeInLayer = node;
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            if (sourceNodeInLayer) {
                                // Check if source node is nested inside a folder (not directly visible)
                                const sourceParentFolder = getParentFolderPath(sourceNodeInLayer.path || sourceNodeInLayer.id);
                                const parentFolderNode = visibleNodesMap.get(sourceParentFolder) || nodesById.get(sourceParentFolder);
                                
                                let sourceX, sourceY, sourceR;
                                
                                // If source is nested inside a visible folder, calculate its position
                                if (parentFolderNode && parentFolderNode.type === 'folder' && 
                                    parentFolderNode.x !== undefined && parentFolderNode.y !== undefined) {
                                    // Get folder's children and calculate nested file position
                                    const folderChildren = (parentFolderNode.children || []).map(id => nodesById.get(id)).filter(Boolean);
                                    
                                    // Normalize paths for comparison
                                    const sourceIdNorm = (sourceNodeInLayer.id || '').replace(/\\\\/g, '/').toLowerCase();
                                    const sourcePathNorm = (sourceNodeInLayer.path || '').replace(/\\\\/g, '/').toLowerCase();
                                    const depPathNorm = depPath.replace(/\\\\/g, '/').toLowerCase();
                                    
                                    // Check if any child matches the source
                                    const matchingChild = folderChildren.find(c => {
                                        const cId = (c.id || '').replace(/\\\\/g, '/').toLowerCase();
                                        const cPath = (c.path || '').replace(/\\\\/g, '/').toLowerCase();
                                        return cId === sourceIdNorm || cPath === sourcePathNorm ||
                                               cId === depPathNorm || cPath === depPathNorm ||
                                               cId.endsWith('/' + sourceIdNorm) || sourceIdNorm.endsWith('/' + cId) ||
                                               cPath.endsWith('/' + sourcePathNorm) || sourcePathNorm.endsWith('/' + cPath) ||
                                               cId.endsWith('/' + depPathNorm) || depPathNorm.endsWith('/' + cId) ||
                                               cPath.endsWith('/' + depPathNorm) || depPathNorm.endsWith('/' + cPath);
                                    });
                                    
                                    if (matchingChild && folderChildren.length > 0) {
                                        // Calculate pack layout for folder's children - MUST match showFolderPreviewOverlay exactly
                                        const folderR = parentFolderNode.r || getPackRadius(parentFolderNode);
                                        const size = Math.max(2 * folderR - 24, 24);
                                        const root = { children: folderChildren.map(n => ({ ...n, value: 1 })) };
                                        const hierarchy = d3.hierarchy(root, x => (x === root ? x.children : null)).sum(x => x.value ?? 0);
                                        d3.pack().size([size, size]).padding(2)(hierarchy);
                                        const center = size / 2;
                                        
                                        // Find the nested file in the hierarchy - match by reference or ID/path
                                        if (hierarchy.children) {
                                            for (let i = 0; i < hierarchy.children.length; i++) {
                                                const c = hierarchy.children[i];
                                                const childNode = c.data;
                                                const childId = (childNode.id || '').replace(/\\\\/g, '/').toLowerCase();
                                                const childPath = (childNode.path || '').replace(/\\\\/g, '/').toLowerCase();
                                                
                                                // Match by reference (same object) or by ID/path
                                                if (childNode === matchingChild ||
                                                    childId === sourceIdNorm || childPath === sourcePathNorm ||
                                                    childId === depPathNorm || childPath === depPathNorm ||
                                                    childId.endsWith('/' + sourceIdNorm) || sourceIdNorm.endsWith('/' + childId) ||
                                                    childPath.endsWith('/' + sourcePathNorm) || sourcePathNorm.endsWith('/' + childPath)) {
                                                    // Position is relative to folder center, convert to absolute
                                                    // This matches exactly how showFolderPreviewOverlay positions circles
                                                    sourceX = parentFolderNode.x + (c.x - center);
                                                    sourceY = parentFolderNode.y + (c.y - center);
                                                    sourceR = Math.max(c.r, 3);
                                                    
                                                    // Add persistent orange circle at nested file position
                                                    const folderElement = g.select(`.node[data-id="${parentFolderNode.id}"]`);
                                                    if (!folderElement.empty()) {
                                                        const nestedFileColor = getNodeColor(matchingChild);
                                                        const circleRadius = Math.max(c.r, 3);
                                                        const circleGroup = folderElement.append('g')
                                                            .attr('class', 'nested-file-circle-persistent')
                                                            .attr('transform', `translate(${c.x - center}, ${c.y - center})`)
                                                            .style('pointer-events', 'none');
                                                        
                                                        // Add circle
                                                        circleGroup.append('circle')
                                                            .attr('r', circleRadius)
                                                            .style('fill', nestedFileColor)
                                                            .attr('stroke', 'none');
                                                        
                                                        // Add text label
                                                        const fileName = matchingChild.name || matchingChild.id || '';
                                                        const maxChars = Math.max(1, Math.floor((circleRadius * 2) / 4));
                                                        const label = fileName.length > maxChars ? fileName.slice(0, maxChars - 3) + '...' : fileName;
                                                        circleGroup.append('text')
                                                            .attr('text-anchor', 'middle')
                                                            .attr('dominant-baseline', 'middle')
                                                            .attr('fill', '#ffffff')
                                                            .attr('font-size', Math.max(4, circleRadius * 0.35) + 'px')
                                                            .attr('font-weight', '500')
                                                            .style('pointer-events', 'none')
                                                            .text(label);
                                                    }
                                                    
                                                    break; // Found it, stop searching
                                                }
                                            }
                                        }
                                        
                                        // Mark folder for preview overlay
                                        if (parentFolderNode && parentFolderNode.id) {
                                            foldersToShow.add(parentFolderNode.id);
                                        }
                                    }
                                }
                                
                                // If not nested or calculation failed, try to find as direct node
                                if (sourceX === undefined || sourceY === undefined) {
                                    // Get the actual rendered position from DOM
                                    let sourceNodeElement = g.select(`.node[data-id="${sourceNodeInLayer.id}"]`);
                                    if (sourceNodeElement.empty() && sourceNodeInLayer.path) {
                                        sourceNodeElement = g.select(`.node[data-id="${sourceNodeInLayer.path}"]`);
                                    }
                                    if (sourceNodeElement.empty()) {
                                        g.selectAll('.node').each(function() {
                                            const d = d3.select(this).datum();
                                            if (d && (d.id === sourceNodeInLayer.id || d.path === sourceNodeInLayer.path || d.id === sourceNodeInLayer.path)) {
                                                sourceNodeElement = d3.select(this);
                                            }
                                        });
                                    }
                                    if (sourceNodeElement.empty()) return;
                                    
                                    sourceX = parseFloat(sourceNodeElement.select('circle').attr('cx')) || sourceNodeInLayer.x || 0;
                                    sourceY = parseFloat(sourceNodeElement.select('circle').attr('cy')) || sourceNodeInLayer.y || 0;
                                    sourceR = parseFloat(sourceNodeElement.select('circle').attr('r')) || getPackRadius(sourceNodeInLayer);
                                }
                                
                                const dx = selectedX - sourceX;
                                const dy = selectedY - sourceY;
                                const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                                const startX = sourceX + (dx/dist) * sourceR;
                                const startY = sourceY + (dy/dist) * sourceR;
                                const endX = selectedX - (dx/dist) * selectedR;
                                const endY = selectedY - (dy/dist) * selectedR;
                                
                                // Inbound cross-level: green (same as same-level inbound)
                                const linkGroup = g.append('g').attr('class', 'link-cross-level');
                                linkGroup.append('line')
                                    .attr('x1', startX)
                                    .attr('y1', startY)
                                    .attr('x2', endX)
                                    .attr('y2', endY)
                                    .attr('stroke', '#22c55e')
                                    .attr('stroke-width', 2)
                                    .attr('stroke-dasharray', '8 8')
                                    .attr('marker-end', 'url(#arrowhead-inbound)')
                                    .attr('class', 'link cross-level dep-arrow visible')
                                    .style('cursor', 'pointer')
                                    .style('opacity', 1)
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                // Mark folder for preview overlay if source is nested inside a folder
                                if (sourceX !== undefined && sourceY !== undefined && sourceNodeInLayer) {
                                    try {
                                        const sourceParentFolder = getParentFolderPath(sourceNodeInLayer.path || sourceNodeInLayer.id);
                                        const sourceParentFolderNode = visibleNodesMap.get(sourceParentFolder) || nodesById.get(sourceParentFolder);
                                        if (sourceParentFolderNode && sourceParentFolderNode.type === 'folder' && sourceParentFolderNode.id) {
                                            foldersToShow.add(sourceParentFolderNode.id);
                                        }
                                    } catch (e) {
                                        console.error('Error tracking folder for preview:', e);
                                    }
                                }
                            } else {
                                // External node for inbound
                                const depNodeColor = getNodeColor(depNode);
                                const relativePath = getRelativePathFromFile(selectedNode.path || selectedNode.id, depPath);
                                const totalExternalCount = crossLevelDeps.filter(d => !visibleNodesMap.get(d)).length + 
                                                          crossLevelDependents.filter(d => !visibleNodesMap.get(d)).length;
                                const angle = (Math.PI * 2 * externalNodeIndex) / Math.max(totalExternalCount, 1) - Math.PI / 2;
                                externalNodeIndex++;
                                
                                const nodeRadius = getPackRadius(depNode);
                                const spacing = 50;
                                const outsideX = containerCx + Math.cos(angle) * (containerR + spacing + nodeRadius);
                                const outsideY = containerCy + Math.sin(angle) * (containerR + spacing + nodeRadius);
                                
                                const dx = selectedX - outsideX;
                                const dy = selectedY - outsideY;
                                const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                                const startX = outsideX + (dx/dist) * nodeRadius;
                                const startY = outsideY + (dy/dist) * nodeRadius;
                                const endX = selectedX - (dx/dist) * selectedR;
                                const endY = selectedY - (dy/dist) * selectedR;
                                
                                // Arrow from outside node to selected (inbound = green)
                                const linkGroup = g.append('g').attr('class', 'link-cross-level');
                                linkGroup.append('line')
                                    .attr('x1', startX)
                                    .attr('y1', startY)
                                    .attr('x2', endX)
                                    .attr('y2', endY)
                                    .attr('stroke', '#22c55e')
                                    .attr('stroke-width', 2)
                                    .attr('marker-end', 'url(#arrowhead-inbound)')
                                    .attr('class', 'link cross-level dep-arrow visible')
                                    .style('cursor', 'pointer')
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                const outsideNodeGroup = g.append('g').attr('class', 'outside-node')
                                    .attr('data-id', depPath)
                                    .style('cursor', 'pointer')
                                    .on('click', function(event) {
                                        event.stopPropagation();
                                        focusFile(depPath);
                                    });
                                
                                const nodeColor = depNode.type === 'folder' ? '#6b7280' : depNodeColor;
                                const strokeColor = depNode.type === 'folder' ? '#111' : (d3.color(depNodeColor)?.darker(0.5) || '#333');
                                outsideNodeGroup.append('circle')
                                    .attr('cx', outsideX)
                                    .attr('cy', outsideY)
                                    .attr('r', nodeRadius)
                                    .attr('fill', nodeColor)
                                    .attr('stroke', strokeColor)
                                    .attr('stroke-width', depNode.type === 'folder' ? 2 : 1);
                                
                                const maxChars = Math.max(1, Math.floor((nodeRadius * 1.6) / 7));
                                const label = depNode.name.length > maxChars ? depNode.name.slice(0, maxChars - 3) + '...' : depNode.name;
                                outsideNodeGroup.append('text')
                                    .attr('class', 'node-label-inside')
                                    .attr('x', outsideX)
                                    .attr('y', outsideY)
                                    .attr('text-anchor', 'middle')
                                    .attr('dominant-baseline', 'middle')
                                    .attr('fill', '#ffffff')
                                    .attr('font-size', '12px')
                                    .attr('font-weight', '500')
                                    .text(label);
                                
                                outsideNodeGroup.append('text')
                                    .attr('x', outsideX)
                                    .attr('y', outsideY + nodeRadius + 18)
                                    .attr('text-anchor', 'middle')
                                    .attr('fill', depNodeColor)
                                    .attr('font-size', '10px')
                                    .attr('font-family', 'JetBrains Mono, monospace')
                                    .text(relativePath || '../');
                                
                                // Mark folder for preview overlay if dependency is inside a visible folder
                                try {
                                    const depParentFolder = getParentFolderPath(depPath);
                                    const depParentFolderNode = visibleNodesMap.get(depParentFolder) || nodesById.get(depParentFolder);
                                    if (depParentFolderNode && depParentFolderNode.type === 'folder' && depParentFolderNode.id) {
                                        foldersToShow.add(depParentFolderNode.id);
                                    }
                                } catch (e) {
                                    console.error('Error tracking folder for preview:', e);
                                }
                            }
                        });
                    }
                }
            }
            
            // Show folder preview overlays for all collected folders
            foldersToShow.forEach(folderId => {
                try {
                    const folderNode = visibleNodesMap.get(folderId) || nodesById.get(folderId);
                    if (folderNode && folderNode.type === 'folder' && 
                        folderNode.x !== undefined && folderNode.y !== undefined) {
                        showFolderPreviewOverlay(folderNode, g);
                    }
                } catch (e) {
                    console.error('Error showing folder preview overlay:', e);
                }
            });
        }

        function escapeAttr(s) {
            return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }
        function escJs(s) {
            return String(s).replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'");
        }

        function partitionDeps(currentFolderPath, paths) {
            const inScope = [];
            const outOfScope = [];
            for (const p of paths) {
                const parentDir = p.split('/').slice(0, -1).join('/');
                if (parentDir === currentFolderPath) inScope.push(p);
                else outOfScope.push(p);
            }
            return { inScope, outOfScope };
        }

        function compactLocationChip(path, currentFolderPath) {
            // currentFolderPath = folder currently shown in the canvas (view scope).
            const depDirSegs = path.split('/').filter(Boolean).slice(0, -1);
            if (depDirSegs.length === 0) return '(root)';
            const selectedDirSegs = (currentFolderPath || '').split('/').filter(Boolean);
            // Within-folder: dep's parent is inside or equal to current folder → show relative subpath only.
            const isPrefix = selectedDirSegs.length <= depDirSegs.length &&
                selectedDirSegs.every((seg, i) => depDirSegs[i] === seg);
            if (isPrefix) {
                const subpath = depDirSegs.slice(selectedDirSegs.length);
                return subpath.length ? subpath.join(' › ') : '(same folder)';
            }
            // Outside: anchor at LCP and show path down to dep's parent (full path from root).
            return depDirSegs.join(' › ');
        }

        function renderInternalDepSection(paths, currentFolderPath, direction) {
            if (!paths || paths.length === 0) return '';
            const { inScope, outOfScope } = partitionDeps(currentFolderPath, paths);
            const arrow = direction === 'inbound' ? '⬅' : '➡';
            const cls = direction === 'inbound' ? 'inbound' : 'outbound';
            const allItems = [...inScope.map(p => ({ path: p, inFolder: true })), ...outOfScope.map(p => ({ path: p, inFolder: false }))];
            const show = allItems.slice(0, 20);
            let html = show.map(({ path: p, inFolder }) => {
                const name = p.split('/').pop();
                if (inFolder) {
                    return `<div class="dep-item ${cls}" onclick="focusFile('${escJs(p)}')">
                        <span class="dep-item-icon" aria-hidden="true">${arrow}</span>
                        <span class="name" title="${escapeAttr(p)}">${escapeAttr(name)}</span>
                    </div>`;
                }
                const fullPathFromRoot = (graphData.rootName ? graphData.rootName + '/' : '') + (p.startsWith('/') ? p.slice(1) : p);
                const parts = fullPathFromRoot.split('/').filter(Boolean);
                const pathSegmentsHtml = parts.length === 0 ? '<span class="dep-item-path-file">(root)</span>' : parts.map((seg, i) => {
                    const isLast = i === parts.length - 1;
                    const spanClass = isLast ? 'dep-item-path-file' : 'dep-item-path-folder';
                    const sep = i === 0 ? '' : '<span class="dep-item-path-sep">/</span>';
                    return sep + `<span class="${spanClass}">${escapeAttr(seg)}</span>`;
                }).join('');
                return `<div class="dep-item ${cls} dep-item-outside" onclick="focusFile('${escJs(p)}')">
                    <span class="name dep-item-name-clickable" title="${escapeAttr(p)}">${escapeAttr(name)}</span>
                    <div class="dep-item-location-wrap" onclick="event.stopPropagation()">
                        <button type="button" class="dep-item-path-toggle" title="Expand to show full path" aria-label="Show full path" onclick="this.closest('.dep-item').classList.toggle('show-full-path')">
                            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
                            <span class="dep-item-path-toggle-chevron">&#9660;</span>
                        </button>
                    </div>
                    <div class="dep-item-full-path">${pathSegmentsHtml}</div>
                </div>`;
            }).join('');
            if (allItems.length > 20) html += `<div class="empty-state">+${allItems.length - 20} more</div>`;
            return html;
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
                            <div class="file-name file-name-folder"><svg class="sidebar-icon" viewBox="0 0 24 24"><use href="#folder-icon"/></svg><span>${esc(node.name)}</span></div>
                            <div class="folder-count-toggle">
                                <button type="button" class="${folderCountMode === 'direct' ? 'active' : ''}" onclick="setFolderCountMode('direct')">Direct</button>
                                <button type="button" class="${folderCountMode === 'recursive' ? 'active' : ''}" onclick="setFolderCountMode('recursive')">Recursive</button>
                            </div>
                            <div class="file-meta">
                                <div class="meta-item">
                                    <div class="meta-label">Subfolders</div>
                                    <div class="meta-value">${folderCountMode === 'direct' ? (node.subfolderCount ?? 0) : (node.recursiveSubfolderCount ?? 0)}</div>
                                </div>
                                ${(node.fileCount ?? 0) > 0 ? `
                                <div class="meta-item">
                                    <div class="meta-label">Files</div>
                                    <div class="meta-value">${folderCountMode === 'direct' ? (node.directFileCount ?? 0) : (node.fileCount ?? 0)}</div>
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
            const currentFolderPath = (node.path || '').split('/').slice(0, -1).join('/');
            const fileColor = getNodeColor(node);
            return `
                <div class="sidebar-section" data-node-id="${esc(node.id)}">
                    <div class="sidebar-title">
                        <span>File</span>
                        <button type="button" class="card-remove" onclick="clearSelection()" aria-label="Clear">×</button>
                    </div>
                    <div class="file-info">
                        <div class="file-name"><svg class="sidebar-icon" viewBox="0 0 24 24"><use href="#file-icon"/></svg><span>${esc(node.name)}</span></div>
                        <div class="file-meta">
                            <div class="meta-item">
                                <div class="meta-label">Language</div>
                                <div class="meta-value file" style="color:${fileColor}">${esc(node.language || '')}</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Lines</div>
                                <div class="meta-value file" style="color:${fileColor}">${node.loc != null ? node.loc.toLocaleString() : 0}</div>
                            </div>
                        </div>
                        ${dependents.length > 0 ? `
                            <div class="deps-section">
                                <div class="deps-title">
                                    Inbound (<span class="count">${dependents.length}</span>)
                                    <button type="button" class="deps-title-info" aria-label="What does Inbound mean?" onclick="this.nextElementSibling.classList.toggle('show')"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg></button>
                                    <div class="deps-tooltip">The listed files import <span class="filename">${esc(node.name)}</span>. When you make a change to <span class="filename">${esc(node.name)}</span>, the listed files may be affected.</div>
                                </div>
                                ${renderInternalDepSection(dependents, currentFolderPath, 'inbound')}
                            </div>
                        ` : ''}
                        ${dependencies.length > 0 ? `
                            <div class="deps-section outbound">
                                <div class="deps-title">
                                    Outbound (<span class="count">${dependencies.length}</span>)
                                    <button type="button" class="deps-title-info" aria-label="What does Outbound mean?" onclick="this.nextElementSibling.classList.toggle('show')"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg></button>
                                    <div class="deps-tooltip"><span class="filename">${esc(node.name)}</span> imports the listed files. When you make a change to any of the listed files, <span class="filename">${esc(node.name)}</span> may be affected.</div>
                                </div>
                                ${renderInternalDepSection(dependencies, currentFolderPath, 'outbound')}
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
                    <div class="ai-summary-section" data-file-path="${esc(node.path || '')}" data-inbound="${esc((dependents || []).join('|'))}" data-outbound="${esc((dependencies || []).join('|'))}">
                        <div class="sidebar-title">AI Summary</div>
                        <div class="ai-summary-tabs">
                            <button type="button" class="ai-summary-tab" data-mode="overview">Overview</button>
                            <button type="button" class="ai-summary-tab" data-mode="how_it_works">How it works</button>
                            <button type="button" class="ai-summary-tab" data-mode="impact">Impact</button>
                            <button type="button" class="ai-summary-tab" data-mode="edit_safely">Edit safely</button>
                            <button type="button" class="ai-summary-tab" data-mode="read_next">Read next</button>
                        </div>
                        <div class="ai-summary-content">Click a tab to generate</div>
                    </div>
                </div>
            `;
        }

        function renderSidePanel() {
            const panel = document.getElementById('details-panel');
            if (selectedNode) {
                panel.innerHTML = getCardHTML(selectedNode);
                updateChangesInFolderPanel();
                return;
            }
            if (currentPath) {
                const folderNode = nodesById.get(currentPath);
                if (folderNode) {
                    panel.innerHTML = getCardHTML(folderNode);
                    updateChangesInFolderPanel();
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
            updateChangesInFolderPanel();
        }
        
        const sidebarBackBtn = document.getElementById('sidebar-back-btn');
        const sidebarForwardBtn = document.getElementById('sidebar-forward-btn');
        if (sidebarBackBtn) sidebarBackBtn.addEventListener('click', goBack);
        if (sidebarForwardBtn) sidebarForwardBtn.addEventListener('click', goForward);

        var filePanelOpen = false;
        var changesPanelOpen = false;
        var searchPanelOpen = false;
        function setFilePanelOpen(open) {
            filePanelOpen = !!open;
            var el = document.getElementById('file-info-panel');
            var btn = document.getElementById('panel-toggle-file-btn');
            if (el) el.classList.toggle('open', filePanelOpen);
            if (btn) btn.classList.toggle('active', filePanelOpen);
        }
        function setChangesPanelOpen(open) {
            changesPanelOpen = !!open;
            var el = document.getElementById('changes-panel');
            var btn = document.getElementById('panel-toggle-changes-btn');
            if (el) el.classList.toggle('open', changesPanelOpen);
            if (btn) btn.classList.toggle('active', changesPanelOpen);
        }
        function setSearchPanelOpen(open) {
            searchPanelOpen = !!open;
            var el = document.getElementById('search-panel');
            var btn = document.getElementById('panel-toggle-search-btn');
            if (el) el.classList.toggle('open', searchPanelOpen);
            if (btn) btn.classList.toggle('active', searchPanelOpen);
            if (open) {
                setTimeout(function() {
                    var input = document.getElementById('search-input');
                    if (input) input.focus();
                }, 100);
            }
        }
        function openFilePanel() {
            setChangesPanelOpen(false);
            setSearchPanelOpen(false);
            setFilePanelOpen(true);
        }
        function closeFilePanel() {
            setFilePanelOpen(false);
        }
        function openChangesPanel() {
            setFilePanelOpen(false);
            setSearchPanelOpen(false);
            setChangesPanelOpen(true);
        }
        function closeChangesPanel() {
            setChangesPanelOpen(false);
        }
        function openSearchPanel() {
            setFilePanelOpen(false);
            setChangesPanelOpen(false);
            setSearchPanelOpen(true);
        }
        function closeSearchPanel() {
            setSearchPanelOpen(false);
        }
        var filePanelBtn = document.getElementById('panel-toggle-file-btn');
        var changesPanelBtn = document.getElementById('panel-toggle-changes-btn');
        var searchPanelBtn = document.getElementById('panel-toggle-search-btn');
        if (filePanelBtn) filePanelBtn.addEventListener('click', function() {
            if (filePanelOpen) closeFilePanel(); else openFilePanel();
        });
        if (changesPanelBtn) changesPanelBtn.addEventListener('click', function() {
            if (changesPanelOpen) closeChangesPanel(); else openChangesPanel();
        });
        if (searchPanelBtn) searchPanelBtn.addEventListener('click', function() {
            if (searchPanelOpen) closeSearchPanel(); else openSearchPanel();
        });

        const detailsPanel = document.getElementById('details-panel');
        if (detailsPanel) {
            detailsPanel.addEventListener('click', async function(e) {
                if (!e.target || !e.target.classList.contains('ai-summary-tab')) return;
                const tab = e.target;
                const section = tab.closest('.ai-summary-section');
                if (!section) return;
                const path = section.getAttribute('data-file-path') || '';
                const inbound = section.getAttribute('data-inbound') || '';
                const outbound = section.getAttribute('data-outbound') || '';
                const mode = tab.getAttribute('data-mode') || '';
                const cacheKey = path + '::' + mode;
                const contentEl = section.querySelector('.ai-summary-content');
                if (!contentEl) return;
                section.querySelectorAll('.ai-summary-tab').forEach(function(t) { t.classList.remove('active'); });
                tab.classList.add('active');
                function escapeHtml(s) {
                    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                }
                if (aiSummaryCache[cacheKey]) {
                    if (aiSummaryCache[cacheKey].loading) {
                        contentEl.innerHTML = '<div class="ai-summary-loading">Generating…</div>';
                        return;
                    }
                    contentEl.innerHTML = '<div class="ai-summary-text">' + escapeHtml(aiSummaryCache[cacheKey].result) + '</div>';
                    return;
                }
                aiSummaryCache[cacheKey] = { loading: true };
                contentEl.innerHTML = '<div class="ai-summary-loading">Generating…</div>';
                const params = new URLSearchParams();
                params.set('path', path);
                params.set('mode', mode);
                params.set('inbound', inbound);
                params.set('outbound', outbound);
                try {
                    const resp = await fetch(window.location.origin + '/api/ai_file_mode?' + params.toString());
                    const data = await resp.json();
                    const result = (data && data.result) ? data.result : 'No summary available.';
                    aiSummaryCache[cacheKey] = { result: result };
                    contentEl.innerHTML = '<div class="ai-summary-text">' + escapeHtml(result) + '</div>';
                } catch (err) {
                    aiSummaryCache[cacheKey] = { result: 'Failed to load.' };
                    contentEl.innerHTML = '<div class="ai-summary-text">Failed to load.</div>';
                }
            });
        }
        const tourStartBtn = document.getElementById('tour-start-btn');
        if (tourStartBtn) tourStartBtn.addEventListener('click', startTour);
        const tourIntroClose = document.getElementById('tour-intro-close');
        if (tourIntroClose) tourIntroClose.addEventListener('click', exitTour);
        const tourIntroGo = document.getElementById('tour-intro-go');
        if (tourIntroGo) tourIntroGo.addEventListener('click', introGo);
        const tourBackBtn = document.getElementById('tour-btn-back');
        if (tourBackBtn) tourBackBtn.addEventListener('click', tourBack);
        const tourNextBtn = document.getElementById('tour-btn-next');
        if (tourNextBtn) tourNextBtn.addEventListener('click', tourNext);
        const tourExitBtn = document.getElementById('tour-btn-exit');
        if (tourExitBtn) tourExitBtn.addEventListener('click', exitTour);
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && (window._tourActive || document.getElementById('tour-overlay').classList.contains('active'))) {
                exitTour();
            }
        });
        attachSearchHandlers();

        // Initial render
        renderGraph();
        updateSidebarNav();
        updateChangesInFolderPanel();

        // Recent changes — poll and update graph/panel
        function humanChangeType(t, kind) {
            const s = (t || '').toLowerCase();
            if (s === 'file_body_edited') return 'File edited';
            if (s === 'file_added') return 'File added';
            if (s === 'file_deleted') return 'File deleted';
            if (s === 'folder_added') return 'Folder added';
            if (s === 'folder_deleted') return 'Folder deleted';
            if (s === 'path_changed') return (kind === 'renamed') ? 'File renamed' : 'File moved';
            if (s === 'folder_path_changed') return (kind === 'renamed') ? 'Folder renamed' : 'Folder moved';
            if (s === 'import_added') return 'Import added';
            if (s === 'import_removed') return 'Import removed';
            return (t || 'Change').replace(/_/g, ' ').replace(/\\b\\w/g, function(ch) { return ch.toUpperCase(); });
        }
        function changeMainLine(c) {
            const typeLabel = humanChangeType(c ? c.type : '', c ? c.kind : undefined);
            const esc = function(x) { return (x || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
            if (c.path) return typeLabel + ' · ' + esc(c.path);
            if (c.oldPath != null && c.newPath != null) return typeLabel + ' · ' + esc(c.oldPath) + ' → ' + esc(c.newPath);
            if (c.fromFile != null && c.toFile != null) return typeLabel + ' · ' + esc(c.fromFile) + ' → ' + esc(c.toFile);
            return typeLabel;
        }
        function formatChangeLine(c) {
            const k = c.kind ? ' (' + c.kind + ')' : '';
            if (c.path !== undefined) return c.type + ': ' + c.path + k;
            if (c.fromFile !== undefined) return c.type + ': ' + c.fromFile + ' → ' + c.toFile;
            if (c.oldPath !== undefined) return c.type + ': ' + c.oldPath + ' → ' + c.newPath + k;
            return c.type;
        }
        var lastSeenSendTimestamp = null;
        function loadRecentChanges() {
            const lastEl = document.getElementById('recent-changes-last-send');
            const listEl = document.getElementById('recent-changes-list');
            if (!lastEl || !listEl) return;
            const origin = window.location.origin;
            Promise.all([
                fetch(origin + '/api/last_changes').then(function(r) { return r.ok ? r.json() : null; }),
                fetch(origin + '/api/git_status').then(function(r) { return r.ok ? r.json() : null; })
            ]).then(function(results) {
                const data = results[0];
                const gitData = results[1];
                if (gitData) {
                    gitStatusData.modified = gitData.modified || [];
                    gitStatusData.added = gitData.added || [];
                    gitStatusData.deleted = gitData.deleted || [];
                    gitStatusData.renamed = gitData.renamed || [];
                }
                if (!data) { updateChangesInFolderPanel(); return; }
                const ts = data.lastSendTimestamp;
                const changes = data.changes || [];
                const batches = data.batches || [];
                lastChangesData.changes = changes;
                lastChangesData.lastSendTimestamp = ts;
                lastChangesData.batches = batches;
                if (ts == null) {
                    lastEl.textContent = '—';
                    lastEl.className = 'last-save-box';
                } else {
                    const minAgo = (Date.now() - ts) / 60000;
                    if (minAgo < 1) {
                        lastEl.textContent = 'Last save <1 min ago';
                        lastEl.className = 'last-save-box recent';
                    } else {
                        lastEl.textContent = 'Last save ' + Math.floor(minAgo) + ' min ago';
                        lastEl.className = 'last-save-box';
                    }
                }
                updateChangesInFolderPanel();
                if (ts !== lastSeenSendTimestamp) {
                    lastSeenSendTimestamp = ts;
                    fetch(origin + '/api/rescan')
                            .then(function(r) {
                                if (r.ok) return r.json();
                                if (r.status === 400) return null;
                                return Promise.reject();
                            })
                            .then(function(data) {
                                if (data && data.nodes && data.links) {
                                    updateGraphData(data);
                                    return;
                                }
                                fetch(window.location.origin + '/api/initial_path')
                                    .then(function(r2) { return r2.ok ? r2.json() : null; })
                                    .then(function(ip) {
                                        if (ip && ip.path) loadRepo(ip.path);
                                    })
                                    .catch(function() {});
                            })
                            .catch(function() {});
                }
            }).catch(function() {
                updateChangesInFolderPanel();
            });
        }
        loadRecentChanges();
        setInterval(loadRecentChanges, 2000);
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') loadRecentChanges();
        });
    </script>
</body>
</html>'''
    
    return html