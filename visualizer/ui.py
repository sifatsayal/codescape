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
            color: #7c3aed;
            cursor: pointer;
            transition: color 0.2s;
        }
        
        .breadcrumb-item:hover {
            color: #a78bfa;
        }
        
        .breadcrumb-sep {
            color: #6b7280;
        }
        .breadcrumb-file {
            color: #06b6d4;
        }

        .header-load-repo {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: 16px;
        }
        .header-load-repo input {
            width: 200px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid rgba(100, 100, 150, 0.3);
            background: rgba(30, 30, 50, 0.8);
            color: #e0e0e0;
        }
        .header-load-repo input::placeholder {
            color: #666;
        }
        .header-load-repo input:focus {
            outline: none;
            border-color: #7c3aed;
        }
        .header-load-repo button {
            font-size: 12px;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(124, 58, 237, 0.5);
            background: rgba(124, 58, 237, 0.25);
            color: #c4b5fd;
            cursor: pointer;
            white-space: nowrap;
        }
        .header-load-repo button:hover:not(:disabled) {
            background: rgba(124, 58, 237, 0.4);
        }
        .header-load-repo button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .header-load-repo button.browse-btn {
            border-color: rgba(6, 182, 212, 0.5);
            background: rgba(6, 182, 212, 0.2);
            color: #67e8f9;
        }
        .header-load-repo button.browse-btn:hover:not(:disabled) {
            background: rgba(6, 182, 212, 0.35);
        }
        .header-search {
            position: relative;
            margin-left: 16px;
            flex: 0 0 280px;
        }
        .header-search input {
            width: 100%;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 6px 28px 6px 10px;
            border-radius: 6px;
            border: 1px solid rgba(100, 100, 150, 0.3);
            background: rgba(20, 20, 35, 0.9);
            color: #e0e0e0;
        }
        .header-search input::placeholder {
            color: #666;
        }
        .header-search input:focus {
            outline: none;
            border-color: #06b6d4;
            box-shadow: 0 0 0 1px rgba(6, 182, 212, 0.6);
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
            max-width: 320px;
            background: rgba(15, 15, 25, 0.97);
            color: #e5e7eb;
            border-radius: 10px;
            border: 1px solid rgba(100, 100, 150, 0.5);
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.75);
            padding: 10px 12px;
            font-size: 12px;
            z-index: 160;
            pointer-events: auto;
        }
        .node-tooltip-header {
            font-weight: 600;
            margin-bottom: 4px;
            color: #e5e7eb;
        }
        .node-tooltip-subtitle {
            font-size: 11px;
            color: #9ca3af;
            margin-bottom: 6px;
        }
        .node-tooltip-meta-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #9ca3af;
        }
        .node-tooltip-meta-row + .node-tooltip-meta-row {
            margin-top: 2px;
        }
        .node-tooltip-divider {
            margin: 8px 0;
            height: 1px;
            background: rgba(55, 65, 81, 0.9);
        }
        .node-tooltip-summary {
            font-size: 12px;
            color: #d1d5db;
            line-height: 1.4;
        }
        .node-tooltip-summary-loading {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
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
            right: 380px;
            bottom: 0;
            background: #0a0a12;
        }

        #sidebar {
            position: fixed;
            top: 60px;
            right: 0;
            width: 380px;
            bottom: 0;
            background: rgba(15, 15, 25, 0.98);
            border-left: 1px solid rgba(100, 100, 150, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 16px;
        }
        .sidebar-body {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
            margin: 0 -16px;
        }
        .sidebar-section-wrap {
            overflow: auto;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        .sidebar-details-wrap {
            flex: 0 0 45%;
            min-height: 120px;
            padding: 0 16px;
            border-bottom: 1px solid rgba(100, 100, 150, 0.15);
        }
        .sidebar-changes-wrap {
            flex: 1 1 0;
            min-height: 160px;
            padding: 0 16px;
        }
        .sidebar-section-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6b7280;
            margin-bottom: 8px;
            padding-top: 12px;
            flex-shrink: 0;
            border-bottom: 1px solid rgba(100, 100, 150, 0.12);
            padding-bottom: 8px;
        }
        .sidebar-details-wrap .sidebar-section-label { padding-top: 0; }
        .sidebar-resizer {
            flex-shrink: 0;
            height: 10px;
            cursor: row-resize;
            background: rgba(100, 100, 150, 0.15);
            position: relative;
        }
        .sidebar-resizer:hover {
            background: rgba(124, 58, 237, 0.35);
        }
        .sidebar-resizer::after {
            content: '';
            position: absolute;
            left: 20%;
            right: 20%;
            top: 4px;
            height: 2px;
            background: rgba(150, 150, 180, 0.4);
            border-radius: 1px;
        }
        .sidebar-resizer:hover::after {
            background: rgba(167, 139, 250, 0.7);
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
            margin-top: 8px;
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
        .recent-changes-muted { margin-bottom: 10px; }
        .recent-changes-list { max-height: 200px; overflow-y: auto; }
        .recent-changes-list .change-line { margin-bottom: 4px; word-break: break-all; }
        .recent-changes-tip {
            margin-top: 12px;
            font-size: 10px;
            color: #6b7280;
            line-height: 1.35;
        }
        .recent-changes-tip strong { color: #9ca3af; }
        .all-changes-last-updated {
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 10px;
            padding: 8px 10px;
            border-radius: 6px;
            background: rgba(30, 30, 45, 0.5);
            transition: background 0.2s;
        }
        .all-changes-last-updated.recent {
            background: rgba(234, 179, 8, 0.2);
            color: #facc15;
        }
        .all-changes-list {
            max-height: 280px;
            overflow-y: auto;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.45;
        }
        .all-changes-event {
            margin-bottom: 6px;
            border-radius: 6px;
            background: rgba(30, 30, 45, 0.4);
            overflow: hidden;
        }
        .all-changes-event-head {
            display: flex;
            align-items: flex-start;
            gap: 6px;
            padding: 8px 10px;
            cursor: pointer;
            color: #e5e7eb;
            word-break: break-all;
        }
        .all-changes-event-head:hover { background: rgba(60, 60, 80, 0.4); }
        .all-changes-event-sparkle {
            flex-shrink: 0;
            margin-top: 1px;
            color: #a78bfa;
        }
        .all-changes-event-summary { flex: 1; min-width: 0; }
        .all-changes-event-toggle {
            flex-shrink: 0;
            color: #9ca3af;
            transition: transform 0.2s;
        }
        .all-changes-event.expanded .all-changes-event-toggle { transform: rotate(90deg); }
        .all-changes-event-detail {
            display: none;
            padding: 10px 12px;
            font-size: 11px;
            color: #9ca3af;
            background: rgba(20, 20, 35, 0.6);
            border-top: 1px solid rgba(100, 100, 150, 0.15);
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 180px;
            overflow-y: auto;
        }
        .all-changes-event.expanded .all-changes-event-detail { display: block; }
        .all-changes-diff-pre {
            margin: 0 0 10px 0;
            font-size: 10px;
            line-height: 1.4;
            overflow-x: auto;
            white-space: pre;
        }
        .all-changes-detail-ai-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #9ca3af;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(100, 100, 150, 0.2);
        }
        .all-changes-detail-summary {
            margin-top: 4px;
            padding-top: 0;
            border-top: none;
        }
        .all-changes-detail-ai-label + .all-changes-detail-summary {
            margin-top: 4px;
        }
        .all-changes-semantic-list {
            margin: 4px 0 0 0;
            padding-left: 18px;
            font-size: 12px;
            line-height: 1.4;
        }
        .all-changes-semantic-list li {
            margin-bottom: 2px;
        }
        .all-changes-event.source-human {
            border-left: 3px solid rgba(34, 197, 94, 0.8);
        }
        .all-changes-event.source-cursor {
            border-left: 3px solid rgba(59, 130, 246, 0.8);
        }
        .all-changes-empty {
            color: #6b7280;
            font-size: 12px;
            padding: 8px 0;
        }
        .change-line-with-desc {
            margin-bottom: 10px;
        }
        .change-line-with-desc .change-line-text {
            margin-bottom: 4px;
        }
        .change-describe-btn {
            font-size: 11px;
            padding: 4px 8px;
            border: 1px solid rgba(245, 158, 11, 0.5);
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 6px;
        }
        .change-describe-btn:hover {
            background: rgba(245, 158, 11, 0.35);
        }
        .change-description {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 6px;
            padding: 8px;
            background: rgba(20, 20, 35, 0.6);
            border-radius: 6px;
            border-left: 2px solid #f59e0b;
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
            fill: #374151;
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
        
        .container-circle {
            pointer-events: none;
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
        <div class="header-load-repo">
            <input type="text" id="load-repo-path" placeholder="Path to repo" title="Enter a folder path or click Browse" />
            <button type="button" id="load-repo-browse-btn" class="browse-btn" title="Choose folder on your computer">Browse</button>
            <button type="button" id="load-repo-btn">Load repo</button>
        </div>
        <div class="header-search">
            <input type="text" id="search-input" placeholder="Search files and folders…" autocomplete="off" />
            <button type="button" id="search-clear-btn" class="search-clear-btn" title="Clear search">×</button>
            <div id="search-results" class="search-results"></div>
        </div>
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
        <div id="sidebar-nav" class="sidebar-nav">
            <button type="button" id="sidebar-back-btn" class="sidebar-nav-btn" title="Back" aria-label="Back" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg></button>
            <button type="button" id="sidebar-forward-btn" class="sidebar-nav-btn" title="Forward" aria-label="Forward" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></button>
        </div>
        <div id="sidebar-body" class="sidebar-body">
            <div id="sidebar-details-wrap" class="sidebar-section-wrap sidebar-details-wrap">
                <div class="sidebar-section-label">Selection</div>
                <div id="details-panel">
                    <div class="details-placeholder">Click a node to view its details</div>
                </div>
            </div>
            <div id="sidebar-resizer" class="sidebar-resizer" title="Drag to resize"></div>
            <div id="sidebar-changes-wrap" class="sidebar-section-wrap sidebar-changes-wrap">
                <div class="sidebar-section-label">All changes</div>
                <div id="recent-changes-panel" class="recent-changes-panel all-changes-panel">
                    <div id="all-changes-last-updated" class="all-changes-last-updated">Last updated: —</div>
                    <div id="all-changes-list" class="all-changes-list"></div>
                    <div class="recent-changes-tip">Open: <strong>Codebase Visualizer: Visualize Codebase</strong>. Green = your changes (Cmd+S). Blue = Cursor (run <strong>Cursor applied changes</strong> after AI edits).</div>
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
        let lastChangesData = { lastSendTimestamp: null, changes: [] };
        let changeContextData = { lastSendTimestamp: null, events: [], touchedPaths: [], fileContexts: [] };

        const FOLDER_COLOR = '#7c3aed';
        const EXTENSION_PALETTE = [
            '#ec4899', '#06b6d4', '#22c55e', '#f59e0b', '#ef4444', '#14b8a6',
            '#8b5cf6', '#84cc16', '#f43f5e', '#0ea5e9', '#eab308', '#a855f7',
            '#10b981', '#6366f1', '#78716c'
        ];
        const EXTENSION_FALLBACK = '#64748b';
        let extensionColorMap = {};  // extension -> hex, computed from graphData.nodes
        const fileSummaryCache = new Map();  // path -> { summary: string, loading: boolean }
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
        function buildTooltipHTMLForNode(node, summaryState) {
            const isFile = node.type === 'file';
            const name = escapeAttr(node.name || '');
            const path = escapeAttr(node.path || node.id || '');
            let header = name;
            let subtitle = '';
            if (isFile) {
                const lang = node.language || '';
                subtitle = lang ? `${lang} • ${path}` : path;
            } else {
                subtitle = path || '(folder)';
            }
            let html = `<div class="node-tooltip-header">${header}</div>`;
            if (subtitle) {
                html += `<div class="node-tooltip-subtitle">${subtitle}</div>`;
            }
            if (isFile) {
                const loc = node.loc != null ? node.loc.toLocaleString() : '0';
                const inbound = Array.isArray(node.dependents) ? node.dependents.length : 0;
                const outbound = Array.isArray(node.dependencies) ? node.dependencies.length : 0;
                html += `<div class="node-tooltip-meta-row"><span>Lines of code</span><span>${loc}</span></div>`;
                html += `<div class="node-tooltip-meta-row"><span>Inbound (imports this)</span><span>${inbound}</span></div>`;
                html += `<div class="node-tooltip-meta-row"><span>Outbound (imports)</span><span>${outbound}</span></div>`;
                html += `<div class="node-tooltip-divider"></div>`;
                const hasSummary = summaryState && typeof summaryState.summary === 'string' && summaryState.summary.trim() !== '';
                if (hasSummary) {
                    html += `<div id="node-tooltip-summary" class="node-tooltip-summary">${escapeAttr(summaryState.summary)}</div>`;
                } else {
                    html += `<div id="node-tooltip-summary" class="node-tooltip-summary node-tooltip-summary-loading">
                        <span class="node-tooltip-spinner"></span>
                        <span>Generating AI summary…</span>
                    </div>`;
                }
            } else {
                const directFiles = node.directFileCount != null ? node.directFileCount : 0;
                const subfolders = node.subfolderCount != null ? node.subfolderCount : 0;
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
            const summaryState = isFile && path ? fileSummaryCache.get(path) : null;
            el.innerHTML = buildTooltipHTMLForNode(node, summaryState);
            const offset = 14;
            const x = (event.clientX || 0) + offset;
            const y = (event.clientY || 0) + offset;
            el.style.left = x + 'px';
            el.style.top = y + 'px';
            el.style.display = 'block';
            if (isFile && path) {
                if (!summaryState || (!summaryState.summary && !summaryState.loading)) {
                    fileSummaryCache.set(path, { summary: '', loading: true });
                    (async () => {
                        const summary = await fetchFileSummary(path);
                        fileSummaryCache.set(path, { summary, loading: false });
                        if (nodeTooltipNodeId === node.id && nodeTooltipEl) {
                            const summaryEl = nodeTooltipEl.querySelector('#node-tooltip-summary');
                            if (summaryEl) {
                                summaryEl.classList.remove('node-tooltip-summary-loading');
                                summaryEl.innerText = summary;
                            }
                        }
                    })();
                }
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

        async function loadRepo() {
            const pathInput = document.getElementById('load-repo-path');
            const path = (pathInput && pathInput.value) ? pathInput.value.trim() : '';
            if (!path) return;
            const btn = document.getElementById('load-repo-btn');
            if (btn) { btn.disabled = true; btn.textContent = 'Loading…'; }
            try {
                const resp = await fetch('/api/load?path=' + encodeURIComponent(path));
                const data = await resp.json();
                if (data.error) { alert(data.error); return; }
                updateGraphData(data);
            } catch (e) {
                alert('Failed to load repo: ' + e.message);
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = 'Load repo'; }
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

        const loadRepoBtn = document.getElementById('load-repo-btn');
        const loadRepoPath = document.getElementById('load-repo-path');
        if (loadRepoBtn) loadRepoBtn.addEventListener('click', loadRepo);
        if (loadRepoPath) loadRepoPath.addEventListener('keydown', function (e) { if (e.key === 'Enter') loadRepo(); });
        const browseBtn = document.getElementById('load-repo-browse-btn');
        if (browseBtn) browseBtn.addEventListener('click', async function () {
            browseBtn.disabled = true;
            browseBtn.textContent = 'Opening…';
            try {
                const resp = await fetch('/api/browse');
                const data = await resp.json();
                if (data.path && loadRepoPath) {
                    loadRepoPath.value = data.path;
                    loadRepo();
                }
            } catch (e) {
                alert('Browse failed: ' + e.message);
            } finally {
                browseBtn.disabled = false;
                browseBtn.textContent = 'Browse';
            }
        });

        // If URL has ?path=..., auto-load that folder (e.g. from Cursor or shared link)
        (function () {
            const params = new URLSearchParams(window.location.search);
            const pathParam = params.get('path');
            if (pathParam && loadRepoPath) {
                loadRepoPath.value = pathParam;
                loadRepo();
            }
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
        
        // Click on background to deselect
        svg.on('click', () => {
            selectedNode = null;
            updateBreadcrumb();
            updateSelection();
            renderSidePanel();
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
            return getChangedPathSet(lastChangesData.changes);
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
        function getPrimaryPathForEvent(ev) {
            if (ev.path) return normPath(ev.path);
            if (ev.newPath) return normPath(ev.newPath);
            if (ev.fromFile) return normPath(ev.fromFile);
            return null;
        }
        function eventKey(ev) {
            return (ev.type || '') + '|' + (ev.path || '') + '|' + (ev.oldPath || '') + '|' + (ev.newPath || '') + '|' + (ev.fromFile || '') + '|' + (ev.timestamp || 0);
        }
        var expandedChangeKeys = new Set();
        var GENERIC_SUMMARIES = ['file modified.', 'new file added.', 'file deleted.', 'file renamed or moved.', 'file modified (no diff available).'];
        function isSubstantiveSummary(s) {
            if (!s || typeof s !== 'string') return false;
            const t = s.trim().toLowerCase();
            if (t.length < 20) return false;
            return GENERIC_SUMMARIES.every(function(g) { return t !== g && !t.startsWith(g); });
        }
        function escapeHtml(s) {
            return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        function pathBasename(p) {
            var s = (p || '').replace(/\\\\/g, '/');
            var i = s.lastIndexOf('/');
            return i >= 0 ? s.slice(i + 1) : s;
        }
        function getSemanticLine(ev) {
            if (ev.type === 'file_added') return 'Added: ' + (ev.path || '');
            if (ev.type === 'file_deleted') return 'Deleted: ' + (ev.path || '');
            if (ev.type === 'file_body_edited') return 'Edited: ' + (ev.path || '');
            if (ev.type === 'path_changed') return (ev.kind === 'renamed' ? 'Renamed: ' : 'Moved: ') + (ev.newPath || '');
            if (ev.type === 'folder_added') return 'Folder added: ' + (ev.path || '');
            if (ev.type === 'folder_deleted') return 'Folder deleted: ' + (ev.path || '');
            if (ev.type === 'folder_path_changed') return (ev.kind === 'renamed' ? 'Renamed: ' : 'Moved: ') + (ev.newPath || '');
            if (ev.type === 'import_added') return 'Import added in ' + (ev.fromFile || '');
            if (ev.type === 'import_removed') return 'Import removed in ' + (ev.fromFile || '');
            return (ev.type || 'Change') + ': ' + (ev.path || ev.oldPath || ev.newPath || '');
        }
        var SPARKLE_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/><path d="M19 12l.75 2.25L22 15l-2.25.75L19 18l-.75-2.25L16 15l2.25-.75L19 12z"/><path d="M5 19l.75 2.25L8 22l-2.25-.75L5 19l-.75-2.25L2 16l2.25-.75L5 19z"/></svg>';
        function updateAllChangesPanel() {
            const lastEl = document.getElementById('all-changes-last-updated');
            const listEl = document.getElementById('all-changes-list');
            if (!lastEl || !listEl) return;
            const ts = changeContextData.lastSendTimestamp;
            const events = changeContextData.events || [];
            const pathToContext = {};
            function pathKey(p) {
                var n = normPath(p || '');
                return n.replace(/\/+$/, '');
            }
            (changeContextData.fileContexts || []).forEach(function(fc) {
                if (fc && fc.path) {
                    var k = pathKey(fc.path);
                    pathToContext[k] = fc;
                }
            });
            if (ts == null) {
                lastEl.textContent = 'Last updated: —';
                lastEl.classList.remove('recent');
            } else {
                const now = Date.now();
                const mins = Math.floor((now - ts) / 60000);
                if (mins < 1) {
                    lastEl.textContent = 'Last updated: <1 min ago';
                    lastEl.classList.add('recent');
                } else {
                    lastEl.textContent = 'Last updated: ' + mins + ' min ago';
                    lastEl.classList.remove('recent');
                }
            }
            if (events.length === 0) {
                listEl.innerHTML = '<div class="all-changes-empty">No changes from last save.</div>';
                return;
            }
            var ORIGINAL_TYPES = ['file_added', 'file_deleted', 'path_changed', 'folder_added', 'folder_deleted', 'folder_path_changed'];
            var displayRows = [];
            var editedPathToSource = {};
            events.forEach(function(ev) {
                if (ORIGINAL_TYPES.indexOf(ev.type) >= 0) {
                    displayRows.push({ kind: 'original', ev: ev });
                } else if (ev.type === 'file_body_edited' && ev.path) {
                    var p = pathKey(ev.path);
                    if (!editedPathToSource[p]) editedPathToSource[p] = ev.source || 'human';
                }
            });
            Object.keys(editedPathToSource).forEach(function(p) {
                displayRows.push({ kind: 'file_changed', path: p, source: editedPathToSource[p] });
            });
            listEl.innerHTML = displayRows.map(function(row, i) {
                var key, lineText, sourceClass, detailContent;
                if (row.kind === 'original') {
                    var ev = row.ev;
                    key = eventKey(ev);
                    lineText = getSemanticLine(ev);
                    sourceClass = (ev.source === 'cursor') ? 'source-cursor' : 'source-human';
                    var primaryPath = getPrimaryPathForEvent(ev);
                    var ctx = primaryPath ? (pathToContext[primaryPath] || pathToContext[pathKey(primaryPath)]) : null;
                    var diff = ctx && ctx.diff ? ctx.diff : null;
                    var summary = ctx && ctx.summary ? ctx.summary : null;
                    var detailParts = [];
                    if (ev.type === 'path_changed' || ev.type === 'folder_path_changed') {
                        var oldP = ev.oldPath || '';
                        var newP = ev.newPath || '';
                        if (ev.kind === 'renamed') {
                            detailParts.push('<div class="all-changes-detail-summary">Changed from ' + escapeHtml(pathBasename(oldP)) + ' to ' + escapeHtml(pathBasename(newP)) + '</div>');
                        } else {
                            detailParts.push('<div class="all-changes-detail-summary">Moved from ' + escapeHtml(oldP) + ' to ' + escapeHtml(newP) + '</div>');
                        }
                    }
                    if (summary && summary.trim()) detailParts.push('<div class="all-changes-detail-summary">' + escapeHtml(summary) + '</div>');
                    detailContent = detailParts.length ? detailParts.join('') : '';
                } else {
                    key = 'file_changed|' + row.path;
                    lineText = 'File changed: ' + row.path;
                    sourceClass = (row.source === 'cursor') ? 'source-cursor' : 'source-human';
                    var fc = pathToContext[row.path];
                    var detailParts = [];
                    if (fc && fc.semanticChanges && fc.semanticChanges.length > 0) {
                        detailParts.push('<ul class="all-changes-semantic-list">');
                        fc.semanticChanges.forEach(function(s) {
                            detailParts.push('<li>' + escapeHtml(s) + '</li>');
                        });
                        detailParts.push('</ul>');
                    }
                    detailContent = detailParts.length ? detailParts.join('') : '';
                }
                var isExpanded = expandedChangeKeys.has(key);
                return '<div class="all-changes-event ' + sourceClass + (isExpanded ? ' expanded' : '') + '" data-index="' + i + '" data-event-key="' + escapeAttr(key) + '">' +
                    '<div class="all-changes-event-head">' +
                    '<span class="all-changes-event-summary">' + escapeAttr(lineText) + '</span>' +
                    '<span class="all-changes-event-toggle">▶</span>' +
                    '</div>' +
                    '<div class="all-changes-event-detail">' + detailContent + '</div>' +
                    '</div>';
            }).join('');
            listEl.querySelectorAll('.all-changes-event-head').forEach(function(head) {
                head.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const row = head.closest('.all-changes-event');
                    if (!row) return;
                    const key = row.getAttribute('data-event-key');
                    if (key) {
                        if (expandedChangeKeys.has(key)) expandedChangeKeys.delete(key);
                        else expandedChangeKeys.add(key);
                    }
                    row.classList.toggle('expanded');
                });
            });
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
            hideNodeTooltip();
            const width = document.getElementById('graph-container').clientWidth;
            const height = document.getElementById('graph-container').clientHeight;
            
            const changedPathSet = getMergedChangedPathSet();
            const folderHasChangedChildSet = getFolderHasChangedChildSet(graphData.nodes);
            
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
            g.append('circle')
                .attr('class', 'container-circle')
                .attr('cx', containerCenterX)
                .attr('cy', containerCenterY)
                .attr('r', hierarchy.r)
                .attr('fill', '#374151')
                .attr('stroke', '#111')
                .attr('stroke-width', 2)
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
                        const fill = nd.type === 'folder' ? '#374151' : getNodeColor(nd);
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
                .attr('fill', d => d.type === 'folder' ? '#374151' : getNodeColor(d))
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
            
            // Draw links on top so inbound/outbound arrows are visible over nodes
            g.append('g')
                .attr('class', 'links')
                .selectAll('line')
                .data(resolvedLinks)
                .join('line')
                .attr('class', d => `link ${d.type}`)
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)')
                .attr('x1', d => d.source && d.source.x != null ? d.source.x : 0)
                .attr('y1', d => d.source && d.source.y != null ? d.source.y : 0)
                .attr('x2', d => {
                    if (!d.target || d.target.x == null) return 0;
                    const dx = d.target.x - (d.source?.x ?? 0);
                    const dy = d.target.y - (d.source?.y ?? 0);
                    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                    const targetR = (d.target.r != null ? d.target.r : getPackRadius(d.target)) + 5;
                    return d.target.x - (dx/dist) * targetR;
                })
                .attr('y2', d => {
                    if (!d.target || d.target.y == null) return 0;
                    const dx = d.target.x - (d.source?.x ?? 0);
                    const dy = d.target.y - (d.source?.y ?? 0);
                    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
                    const targetR = (d.target.r != null ? d.target.r : getPackRadius(d.target)) + 5;
                    return d.target.y - (dy/dist) * targetR;
                });
            
            updateSelection();
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
                    <span class="dep-item-icon" aria-hidden="true">${arrow}</span>
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
            const currentFolderPath = (node.path || '').split('/').slice(0, -1).join('/');
            return `
                <div class="sidebar-section" data-node-id="${esc(node.id)}">
                    <div class="sidebar-title">
                        <span>File</span>
                        <button type="button" class="card-remove" onclick="clearSelection()" aria-label="Clear">×</button>
                    </div>
                    <div class="file-info">
                        <div class="file-name"><svg class="sidebar-icon" viewBox="0 0 24 24"><use href="#file-icon"/></svg><span>${esc(node.name)}</span></div>
                        <div class="file-path">${esc(node.path)}</div>
                        <div class="file-meta">
                            <div class="meta-item">
                                <div class="meta-label">Language</div>
                                <div class="meta-value file">${esc(node.language || '')}</div>
                            </div>
                            <div class="meta-item">
                                <div class="meta-label">Lines</div>
                                <div class="meta-value file">${node.loc != null ? node.loc.toLocaleString() : 0}</div>
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
                </div>
            `;
        }

        function renderSidePanel() {
            const panel = document.getElementById('details-panel');
            if (selectedNode) {
                panel.innerHTML = getCardHTML(selectedNode);
                updateAllChangesPanel();
                return;
            }
            if (currentPath) {
                const folderNode = nodesById.get(currentPath);
                if (folderNode) {
                    panel.innerHTML = getCardHTML(folderNode);
                    updateAllChangesPanel();
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
            updateAllChangesPanel();
        }
        
        const sidebarBackBtn = document.getElementById('sidebar-back-btn');
        const sidebarForwardBtn = document.getElementById('sidebar-forward-btn');
        if (sidebarBackBtn) sidebarBackBtn.addEventListener('click', goBack);
        if (sidebarForwardBtn) sidebarForwardBtn.addEventListener('click', goForward);

        (function initSidebarResizer() {
            var SIDEBAR_RATIO_KEY = 'codebaseVisualizer.sidebarDetailsRatio';
            var MIN_RATIO = 0.15;
            var MAX_RATIO = 0.85;
            var bodyEl = document.getElementById('sidebar-body');
            var detailsWrap = document.getElementById('sidebar-details-wrap');
            var resizer = document.getElementById('sidebar-resizer');
            if (!bodyEl || !detailsWrap || !resizer) return;
            var currentRatio = 0.45;
            try {
                var saved = localStorage.getItem(SIDEBAR_RATIO_KEY);
                if (saved != null) {
                    var r = parseFloat(saved);
                    if (!isNaN(r) && r >= MIN_RATIO && r <= MAX_RATIO) currentRatio = r;
                }
            } catch (e) {}
            function setRatio(r) {
                currentRatio = Math.max(MIN_RATIO, Math.min(MAX_RATIO, r));
                detailsWrap.style.flex = '0 0 ' + (currentRatio * 100) + '%';
            }
            setRatio(currentRatio);
            resizer.addEventListener('mousedown', function(e) {
                e.preventDefault();
                var startY = e.clientY;
                var bodyRect = bodyEl.getBoundingClientRect();
                var startTopPx = currentRatio * bodyRect.height;
                function onMove(moveE) {
                    var dy = moveE.clientY - startY;
                    var bodyH = bodyEl.getBoundingClientRect().height;
                    setRatio((startTopPx + dy) / bodyH);
                }
                function onUp() {
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    document.removeEventListener('mousemove', onMove);
                    document.removeEventListener('mouseup', onUp);
                    try { localStorage.setItem(SIDEBAR_RATIO_KEY, String(currentRatio)); } catch (e2) {}
                }
                document.body.style.cursor = 'row-resize';
                document.body.style.userSelect = 'none';
                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onUp);
            });
        })();

        attachSearchHandlers();

        // Initial render
        renderGraph();
        updateSidebarNav();
        updateAllChangesPanel();

        // Recent changes — poll and update graph/panel
        function formatChangeLine(c) {
            const k = c.kind ? ' (' + c.kind + ')' : '';
            if (c.path !== undefined) return c.type + ': ' + c.path + k;
            if (c.fromFile !== undefined) return c.type + ': ' + c.fromFile + ' → ' + c.toFile;
            if (c.oldPath !== undefined) return c.type + ': ' + c.oldPath + ' → ' + c.newPath + k;
            return c.type;
        }
        var lastSeenSendTimestamp = null;
        function loadRecentChanges() {
            const listEl = document.getElementById('all-changes-list');
            if (!listEl) return;
            const origin = window.location.origin;
            fetch(origin + '/api/change_context').then(function(r) { return r.ok ? r.json() : null; }).then(function(data) {
                if (!data) {
                    changeContextData.lastSendTimestamp = null;
                    changeContextData.events = [];
                    changeContextData.touchedPaths = [];
                    changeContextData.fileContexts = [];
                    lastChangesData.changes = [];
                    lastChangesData.lastSendTimestamp = null;
                    updateAllChangesPanel();
                    return;
                }
                const ts = data.lastSendTimestamp;
                const events = data.events || [];
                changeContextData.lastSendTimestamp = ts;
                changeContextData.events = events;
                changeContextData.touchedPaths = data.touchedPaths || [];
                changeContextData.fileContexts = data.fileContexts || [];
                lastChangesData.changes = events;
                lastChangesData.lastSendTimestamp = ts;
                updateAllChangesPanel();
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
                                var pathInput = document.getElementById('load-repo-path');
                                if (!pathInput) return;
                                var pathToLoad = pathInput.value.trim();
                                if (pathToLoad) {
                                    loadRepo();
                                } else {
                                    fetch(window.location.origin + '/api/initial_path')
                                        .then(function(r2) { return r2.ok ? r2.json() : null; })
                                        .then(function(ip) {
                                            if (ip && ip.path && pathInput) {
                                                pathInput.value = ip.path;
                                                loadRepo();
                                            }
                                        })
                                        .catch(function() {});
                                }
                            })
                            .catch(function() {});
                }
            }).catch(function() {
                updateAllChangesPanel();
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