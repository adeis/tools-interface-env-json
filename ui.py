import json
import os
import sys
import webbrowser
import threading
import socket
import datetime
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

ENV_FILE = '.env'

def backup_env_file():
    if not os.path.exists(ENV_FILE):
        return
    
    backup_dir = 'artefak'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = f".env-{timestamp}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"Backup created successfully at: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

def read_company_config():
    if not os.path.exists(ENV_FILE):
        return {}
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('COMPANY_CONFIG='):
                val = line.split('=', 1)[1]
                # Check for enclosing double quotes if any
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                try:
                    return json.loads(val)
                except Exception as e:
                    print(f"Error parsing COMPANY_CONFIG JSON: {e}")
                    return {}
    return {}

def write_company_config(config_dict):
    # Perform backup before writing changes
    backup_env_file()

    lines = []
    found = False
    config_str = json.dumps(config_dict, separators=(',', ':')) # compact format
    
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('COMPANY_CONFIG='):
                    lines.append(f"COMPANY_CONFIG={config_str}\n")
                    found = True
                else:
                    lines.append(line)
                    
    if not found:
        # If the file didn't end with a newline, append one
        if lines and not lines[-1].endswith('\n'):
            lines.append('\n')
        lines.append(f"COMPANY_CONFIG={config_str}\n")
        
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def find_free_port(host, start_port=5000):
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except socket.error:
                port += 1
    return start_port

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nusawork - Company Configurer</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --panel-bg: rgba(17, 24, 39, 0.7);
            --card-bg: rgba(31, 41, 55, 0.4);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(99, 102, 241, 0.4);
            --border-active: rgba(99, 102, 241, 0.7);
            
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-glow: rgba(99, 102, 241, 0.3);
            
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.2);
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --danger-glow: rgba(239, 68, 68, 0.2);
            
            --font-outfit: 'Outfit', sans-serif;
            --font-inter: 'Inter', sans-serif;
            
            --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: var(--font-inter);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225,39%,30%,0.15) 0, transparent 50%),
                radial-gradient(at 100% 0%, hsla(339,49%,30%,0.08) 0, transparent 50%);
        }

        /* Scrollbar styles */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.25);
        }

        /* Glassmorphism Header */
        header {
            background: var(--panel-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .header-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .header-logo h1 {
            font-family: var(--font-outfit);
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #818cf8, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            font-weight: 500;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 12px var(--success); }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition-smooth);
            border: 1px solid transparent;
            color: var(--text-primary);
        }

        .btn:active {
            transform: scale(0.97);
        }

        .btn-primary {
            background-color: var(--primary);
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .btn-primary:hover {
            background-color: var(--primary-hover);
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.5);
        }
        
        .btn-primary:disabled {
            background-color: rgba(99, 102, 241, 0.4);
            cursor: not-allowed;
            box-shadow: none;
            opacity: 0.6;
        }

        .btn-success {
            background-color: var(--success);
            box-shadow: 0 4px 12px var(--success-glow);
        }

        .btn-success:hover {
            background-color: #059669;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
        }
        
        .btn-success.pulse-btn {
            animation: glow-pulse 1.5s infinite alternate;
        }
        
        @keyframes glow-pulse {
            from { box-shadow: 0 0 4px rgba(16, 185, 129, 0.4); }
            to { box-shadow: 0 0 16px rgba(16, 185, 129, 0.8); }
        }

        .btn-danger {
            background-color: var(--danger);
            box-shadow: 0 4px 12px var(--danger-glow);
        }

        .btn-danger:hover {
            background-color: var(--danger-hover);
            box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
        }

        .btn-secondary {
            background-color: transparent;
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background-color: rgba(255, 255, 255, 0.05);
            border-color: var(--text-secondary);
        }

        .btn-icon-only {
            padding: 0.5rem;
            border-radius: 6px;
        }

        /* App Container */
        .app-container {
            display: grid;
            grid-template-columns: 320px 1fr;
            flex-grow: 1;
            max-width: 1600px;
            width: 100%;
            margin: 0 auto;
            border-left: 1px solid var(--border-color);
            border-right: 1px solid var(--border-color);
            background: rgba(10, 15, 26, 0.3);
        }

        /* Sidebar */
        .sidebar {
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            background: rgba(17, 24, 39, 0.4);
            height: calc(100vh - 66px);
            position: sticky;
            top: 66px;
        }

        .sidebar-header {
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        .search-container {
            position: relative;
            display: flex;
            align-items: center;
        }

        .search-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.6rem 0.75rem 0.6rem 2.25rem;
            color: var(--text-primary);
            font-size: 0.875rem;
            transition: var(--transition-smooth);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }

        .search-icon {
            position: absolute;
            left: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            pointer-events: none;
        }

        .clear-search-btn {
            position: absolute;
            right: 0.75rem;
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            display: none;
            align-items: center;
        }

        .clear-search-btn:hover {
            color: var(--text-primary);
        }

        /* Company List */
        .company-list {
            flex-grow: 1;
            overflow-y: auto;
            padding: 1rem 0.75rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .company-item {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            cursor: pointer;
            transition: var(--transition-smooth);
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            position: relative;
            overflow: hidden;
        }

        .company-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background-color: transparent;
            transition: var(--transition-smooth);
        }

        .company-item:hover {
            background: rgba(31, 41, 55, 0.6);
            border-color: var(--border-hover);
            transform: translateX(2px);
        }

        .company-item.active {
            background: rgba(99, 102, 241, 0.08);
            border-color: var(--border-active);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.04);
        }

        .company-item.active::before {
            background-color: var(--primary);
        }

        .company-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .company-title {
            font-family: var(--font-outfit);
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-primary);
            word-break: break-all;
            padding-right: 1.5rem;
        }

        .badge {
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }

        .company-key {
            font-family: monospace;
            font-size: 0.7rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .copy-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            transition: var(--transition-smooth);
        }
        
        .copy-btn:hover {
            color: var(--text-primary);
        }

        .company-delete-btn {
            position: absolute;
            right: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0;
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: var(--transition-smooth);
        }

        .company-item:hover .company-delete-btn {
            opacity: 1;
        }

        .company-delete-btn:hover {
            color: var(--danger);
            background: rgba(239, 68, 68, 0.1);
        }

        .empty-list-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
        }

        /* Workspace */
        .workspace {
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            overflow-y: auto;
            height: calc(100vh - 66px);
        }

        .workspace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }

        .workspace-title-area {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .workspace-title {
            font-family: var(--font-outfit);
            font-size: 1.5rem;
            font-weight: 600;
        }

        .workspace-subtitle {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 0.25rem;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            padding: 0.4rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: var(--transition-smooth);
        }

        .tab-btn:hover {
            color: var(--text-primary);
        }

        .tab-btn.active {
            background: var(--card-bg);
            color: var(--text-primary);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
        }

        /* Editor Panes */
        .pane {
            display: none;
        }

        .pane.active {
            display: block;
        }

        /* Form styling */
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
        }

        .form-full-width {
            grid-column: span 2;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .form-label {
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
        }

        .form-control-container {
            position: relative;
            display: flex;
            align-items: center;
        }

        .form-control {
            width: 100%;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.65rem 0.75rem;
            color: var(--text-primary);
            font-size: 0.875rem;
            transition: var(--transition-smooth);
        }

        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }

        .form-control.input-action-right {
            padding-right: 6.5rem;
        }

        .form-control.input-icon-right {
            padding-right: 2.5rem;
        }

        .form-control-action-btn {
            position: absolute;
            right: 0.35rem;
            padding: 0.3rem 0.6rem;
            background: var(--primary);
            border: none;
            border-radius: 6px;
            color: white;
            font-size: 0.75rem;
            cursor: pointer;
            transition: var(--transition-smooth);
            font-weight: 500;
        }

        .form-control-action-btn:hover {
            background-color: var(--primary-hover);
        }

        .form-control-icon-btn {
            position: absolute;
            right: 0.75rem;
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            transition: var(--transition-smooth);
        }

        .form-control-icon-btn:hover {
            color: var(--text-primary);
        }

        .form-helper-text {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.15rem;
        }

        /* JSON Area */
        .json-textarea-container {
            position: relative;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.25);
            overflow: hidden;
        }

        .json-textarea {
            width: 100%;
            height: 480px;
            background: transparent;
            border: none;
            padding: 1rem;
            color: #a7f3d0; /* emerald 200 coding font color */
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            resize: vertical;
            outline: none;
        }

        .json-status-bar {
            background: rgba(0, 0, 0, 0.4);
            border-top: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
        }

        .json-status {
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .json-status.valid {
            color: var(--success);
        }

        .json-status.invalid {
            color: var(--danger);
        }

        /* Unsaved Changes Panel */
        .unsaved-badge {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            display: none;
            animation: pulse-red 2s infinite;
        }

        @keyframes pulse-red {
            0% { opacity: 0.8; }
            50% { opacity: 1; box-shadow: 0 0 8px rgba(239, 68, 68, 0.2); }
            100% { opacity: 0.8; }
        }

        /* Helper Box */
        .helper-box {
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid rgba(99, 102, 241, 0.15);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            font-size: 0.8rem;
            color: #c7d2fe;
            margin-top: 1rem;
        }

        .helper-box-icon {
            color: var(--primary);
            flex-shrink: 0;
            margin-top: 0.1rem;
        }

        .workspace-footer {
            display: flex;
            justify-content: flex-end;
            gap: 1rem;
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
            margin-top: auto;
        }

        .no-selected-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-grow: 1;
            color: var(--text-secondary);
            gap: 1rem;
            text-align: center;
            min-height: 400px;
        }
        
        .no-selected-state h3 {
            font-family: var(--font-outfit);
            font-size: 1.25rem;
            color: var(--text-primary);
        }

        /* Icons */
        .icon {
            vertical-align: middle;
            stroke-width: 2;
        }
        
        /* Modal Dialog */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            z-index: 100;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s ease-in-out;
        }

        .modal.active {
            display: flex;
            opacity: 1;
        }

        .modal-content {
            background: #111827;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            transform: scale(0.95);
            transition: transform 0.2s ease-in-out;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .modal.active .modal-content {
            transform: scale(1);
        }

        .modal-header {
            font-family: var(--font-outfit);
            font-size: 1.15rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .modal-body {
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
        }

        /* Toasts Container */
        .toast-container {
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            z-index: 200;
            max-width: 350px;
            width: 100%;
        }

        .toast {
            background: rgba(17, 24, 39, 0.9);
            border-left: 4px solid var(--primary);
            border-radius: 6px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
            padding: 0.75rem 1rem;
            color: var(--text-primary);
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            transform: translateX(120%);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
            opacity: 0;
            backdrop-filter: blur(8px);
            border-top: 1px solid var(--border-color);
            border-right: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
        }

        .toast.show {
            transform: translateX(0);
            opacity: 1;
        }

        .toast-success {
            border-left-color: var(--success);
        }

        .toast-danger {
            border-left-color: var(--danger);
        }

        .toast-close {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1rem;
            display: flex;
            align-items: center;
        }

        .toast-close:hover {
            color: var(--text-primary);
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .app-container {
                grid-template-columns: 1fr;
            }
            .sidebar {
                height: auto;
                position: relative;
                top: 0;
            }
            .workspace {
                height: auto;
                overflow-y: visible;
                padding: 1.25rem;
            }
            .form-grid {
                grid-template-columns: 1fr;
            }
            .form-full-width {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <!-- Top Header -->
    <header>
        <div class="header-logo">
            <h1>Nusawork Configurer</h1>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>Connected</span>
            </div>
            <div class="unsaved-badge" id="unsaved-badge">Unsaved Changes</div>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" id="shutdown-btn" title="Stop UI Server and Exit">
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
                <span>Shutdown</span>
            </button>
            <button class="btn btn-success" id="save-env-btn" disabled>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                <span>Save to .env</span>
            </button>
        </div>
    </header>

    <div class="app-container">
        <!-- Sidebar Directory -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <button class="btn btn-primary" id="add-company-btn" style="width: 100%;">
                    <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>Add New Company</span>
                </button>
                <div class="search-container">
                    <span class="search-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </span>
                    <input type="text" class="search-input" id="search-input" placeholder="Search by name or key...">
                    <button class="clear-search-btn" id="clear-search-btn">&times;</button>
                </div>
            </div>
            
            <div class="company-list" id="company-list">
                <!-- Loaded dynamically -->
            </div>
        </aside>

        <!-- Main Workspace -->
        <main class="workspace">
            <!-- Selected State -->
            <div id="workspace-selected" style="display: none; height: 100%; flex-direction: column;">
                <div class="workspace-header">
                    <div class="workspace-title-area">
                        <h2 class="workspace-title" id="display-title">Select a Company</h2>
                        <span class="workspace-subtitle" id="display-key-label">Key: None</span>
                    </div>
                    
                    <div class="tabs">
                        <button class="tab-btn active" data-tab="form">Form Editor</button>
                        <button class="tab-btn" data-tab="json">Raw JSON</button>
                    </div>
                </div>

                <!-- Form Tab Pane -->
                <div class="pane active" id="pane-form" style="margin-top: 1.5rem;">
                    <div class="form-grid">
                        <div class="form-group form-full-width">
                            <label class="form-label" for="company_key">
                                <span>Company Key (32-character Hex)</span>
                            </label>
                            <div class="form-control-container">
                                <input type="text" class="form-control input-action-right" id="company_key" maxlength="32" placeholder="e.g. b26d7056c7af4fb285b9f5850d057c83">
                                <button class="form-control-action-btn" id="generate-key-btn">Generate Key</button>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="grant_type">Grant Type</label>
                            <select class="form-control" id="grant_type">
                                <option value="client_credentials">client_credentials</option>
                                <option value="authorization_code">authorization_code</option>
                                <option value="password">password</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="client_id">Client ID</label>
                            <input type="number" class="form-control" id="client_id" placeholder="e.g. 3">
                        </div>

                        <div class="form-group form-full-width">
                            <label class="form-label" for="client_secret">Client Secret</label>
                            <div class="form-control-container">
                                <input type="password" class="form-control input-icon-right" id="client_secret" placeholder="Enter client secret">
                                <button class="form-control-icon-btn" id="toggle-secret-btn" type="button">
                                    <svg id="secret-eye-icon" class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                </button>
                            </div>
                        </div>

                        <div class="form-group form-full-width">
                            <label class="form-label" for="token_api_url">Token API URL</label>
                            <input type="url" class="form-control" id="token_api_url" placeholder="https://domain.app.nusawork.com/auth/api/oauth/token">
                        </div>

                        <div class="form-group form-full-width">
                            <label class="form-label" for="attendance_api_url">Attendance API URL</label>
                            <input type="url" class="form-control" id="attendance_api_url" placeholder="https://domain.app.nusawork.com/api/attendance-raw/client/storage-data">
                            <span class="form-helper-text">Generally generated automatically from the Token URL.</span>
                        </div>
                    </div>

                    <!-- Autocomplete suggestion box -->
                    <div class="helper-box" id="autocomplete-box" style="display: none;">
                        <span class="helper-box-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        </span>
                        <div>
                            <strong>Auto-filled URLs</strong>
                            <p>We've automatically suggested an Attendance API URL based on your Token API URL subdomain.</p>
                        </div>
                    </div>
                </div>

                <!-- JSON Tab Pane -->
                <div class="pane" id="pane-json" style="margin-top: 1.5rem;">
                    <div class="json-textarea-container">
                        <textarea class="json-textarea" id="json-textarea" spellcheck="false"></textarea>
                        <div class="json-status-bar">
                            <div class="json-status valid" id="json-status">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                <span>Valid JSON</span>
                            </div>
                            <div class="text-muted">Direct edits here affect all configuration.</div>
                        </div>
                    </div>
                </div>

                <!-- Form/Workspace actions -->
                <div class="workspace-footer">
                    <button class="btn btn-danger" id="delete-company-btn">
                        <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                        <span>Delete Company</span>
                    </button>
                    <button class="btn btn-secondary" id="cancel-changes-btn">Reset Form</button>
                    <button class="btn btn-primary" id="apply-changes-btn">Apply Changes</button>
                </div>
            </div>

            <!-- Empty Selected State -->
            <div class="no-selected-state" id="workspace-empty">
                <svg style="color: var(--text-muted);" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                <h3>No Company Selected</h3>
                <p>Select an existing company from the sidebar directory<br>or add a new configuration to start editing.</p>
                <button class="btn btn-primary" id="empty-add-btn" style="margin-top: 0.5rem;">
                    <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    <span>Add New Company</span>
                </button>
            </div>
        </main>
    </div>

    <!-- Confirm Modal Dialog -->
    <div class="modal" id="confirm-modal">
        <div class="modal-content">
            <div class="modal-header">
                <svg style="color: var(--danger)" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                <span>Confirm Deletion</span>
            </div>
            <div class="modal-body" id="confirm-modal-body">
                Are you sure you want to delete this company configuration? This action cannot be undone.
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="confirm-cancel">Cancel</button>
                <button class="btn btn-danger" id="confirm-yes">Delete</button>
            </div>
        </div>
    </div>

    <!-- Toast Notifications Container -->
    <div class="toast-container" id="toast-container"></div>

    <script>
        // State
        let originalConfig = {};
        let currentConfig = {};
        let selectedId = '';
        let activeTab = 'form';
        let searchQuery = '';
        let confirmAction = null;

        // DOM elements
        const companyList = document.getElementById('company-list');
        const workspaceSelected = document.getElementById('workspace-selected');
        const workspaceEmpty = document.getElementById('workspace-empty');
        const displayTitle = document.getElementById('display-title');
        const displayKeyLabel = document.getElementById('display-key-label');
        
        // Form controls
        const inputKey = document.getElementById('company_key');
        const selectGrantType = document.getElementById('grant_type');
        const inputClientId = document.getElementById('client_id');
        const inputClientSecret = document.getElementById('client_secret');
        const inputTokenUrl = document.getElementById('token_api_url');
        const inputAttendanceUrl = document.getElementById('attendance_api_url');
        
        // General UI elements
        const searchInput = document.getElementById('search-input');
        const clearSearchBtn = document.getElementById('clear-search-btn');
        const saveEnvBtn = document.getElementById('save-env-btn');
        const unsavedBadge = document.getElementById('unsaved-badge');
        const autocompleteBox = document.getElementById('autocomplete-box');
        const jsonTextarea = document.getElementById('json-textarea');
        const jsonStatus = document.getElementById('json-status');
        const modal = document.getElementById('confirm-modal');
        const shutdownBtn = document.getElementById('shutdown-btn');

        // Initial Load
        async function fetchConfig() {
            try {
                const res = await fetch('/api/config');
                originalConfig = await res.json();
                currentConfig = JSON.parse(JSON.stringify(originalConfig)); // deep clone
                
                checkUnsavedChanges();
                renderCompanyList();
                
                // Select first company if available
                const keys = Object.keys(currentConfig);
                if (keys.length > 0) {
                    selectCompany(keys[0]);
                } else {
                    showEmptyWorkspace();
                }
            } catch (err) {
                showToast('Failed to load configurations from .env', 'danger');
                console.error(err);
            }
        }

        // Helper to format clean company names from API URLs
        function getCompanyFriendlyName(id, data) {
            let url = data.attendance_api_url || data.token_api_url || '';
            if (!url) return `Company [${id.substring(0, 8)}]`;
            
            try {
                const parsed = new URL(url);
                const host = parsed.hostname;
                // Remove common domains
                let name = host.replace('.app.nusawork.com', '')
                               .replace('.app2.nusawork.com', '')
                               .replace('www.', '');
                return name.toUpperCase();
            } catch (e) {
                // regex fallback
                const match = url.match(/^(https?:\/\/)?([^\/:]+)/i);
                if (match && match[2]) {
                    return match[2].replace('.app.nusawork.com', '').replace('.app2.nusawork.com', '').toUpperCase();
                }
                return `Company [${id.substring(0, 8)}]`;
            }
        }

        // Render Sidebar
        function renderCompanyList() {
            companyList.innerHTML = '';
            const keys = Object.keys(currentConfig);
            
            // Filter keys
            const filteredKeys = keys.filter(key => {
                const data = currentConfig[key];
                const friendlyName = getCompanyFriendlyName(key, data).toLowerCase();
                const tokenUrl = (data.token_api_url || '').toLowerCase();
                const keyLower = key.toLowerCase();
                const searchLower = searchQuery.toLowerCase();
                
                return friendlyName.includes(searchLower) || 
                       tokenUrl.includes(searchLower) || 
                       keyLower.includes(searchLower);
            });

            if (filteredKeys.length === 0) {
                companyList.innerHTML = `
                    <div class="empty-list-state">
                        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        <span>No companies match search</span>
                    </div>
                `;
                return;
            }

            filteredKeys.forEach(key => {
                const data = currentConfig[key];
                const friendlyName = getCompanyFriendlyName(key, data);
                const isActive = key === selectedId;
                
                const item = document.createElement('div');
                item.className = `company-item ${isActive ? 'active' : ''}`;
                item.onclick = () => selectCompany(key);
                
                item.innerHTML = `
                    <div class="company-item-header">
                        <span class="company-title" title="${friendlyName}">${friendlyName}</span>
                        <span class="badge">ID: ${data.client_id || 0}</span>
                    </div>
                    <div class="company-key">
                        <span>${key.substring(0, 8)}...${key.substring(24)}</span>
                        <button class="copy-btn" onclick="copyToClipboard(event, '${key}')" title="Copy Full Key">
                            <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        </button>
                    </div>
                    <button class="company-delete-btn" onclick="triggerDelete(event, '${key}')" title="Delete Company">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                `;
                companyList.appendChild(item);
            });
        }

        // Select Company and fill views
        function selectCompany(id) {
            selectedId = id;
            const data = currentConfig[id];
            
            if (!data) {
                showEmptyWorkspace();
                return;
            }
            
            workspaceEmpty.style.display = 'none';
            workspaceSelected.style.display = 'flex';
            
            // Highlight selected in list
            document.querySelectorAll('.company-item').forEach(el => el.classList.remove('active'));
            renderCompanyList();
            
            // Set Workspace Info
            const friendlyName = getCompanyFriendlyName(id, data);
            displayTitle.textContent = friendlyName;
            displayKeyLabel.innerHTML = `Key: <code style="font-family:monospace; background:rgba(0,0,0,0.3); padding:0.1rem 0.3rem; border-radius:4px; font-size:0.8rem;">${id}</code>`;
            
            // Fill Form controls
            inputKey.value = id;
            inputKey.dataset.oldKey = id; // track original key in case of rename
            selectGrantType.value = data.grant_type || 'client_credentials';
            inputClientId.value = data.client_id || 3;
            inputClientSecret.value = data.client_secret || '';
            inputTokenUrl.value = data.token_api_url || '';
            inputAttendanceUrl.value = data.attendance_api_url || '';
            
            // Autocomplete helper state reset
            inputAttendanceUrl.dataset.autogenerated = 'false';
            autocompleteBox.style.display = 'none';
            
            // Reset client secret visibility
            inputClientSecret.type = 'password';
            document.getElementById('secret-eye-icon').innerHTML = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>`;
            
            // Load JSON in text tab
            jsonTextarea.value = JSON.stringify(currentConfig, null, 2);
            validateJsonSyntax();
        }

        function showEmptyWorkspace() {
            selectedId = '';
            workspaceSelected.style.display = 'none';
            workspaceEmpty.style.display = 'flex';
            document.querySelectorAll('.company-item').forEach(el => el.classList.remove('active'));
        }

        // Save Form values to currentConfig
        function applyFormChanges() {
            if (!selectedId) return false;
            
            const newKey = inputKey.value.trim();
            
            // Validation
            if (newKey.length !== 32 || !/^[0-9a-fA-F]+$/.test(newKey)) {
                showToast('Company key must be exactly 32 hex characters.', 'danger');
                inputKey.focus();
                return false;
            }
            
            const oldKey = inputKey.dataset.oldKey;
            
            // Check duplicate key
            if (newKey !== oldKey && currentConfig[newKey]) {
                showToast('A company with this key already exists.', 'danger');
                inputKey.focus();
                return false;
            }
            
            const updatedCompany = {
                grant_type: selectGrantType.value,
                client_id: parseInt(inputClientId.value) || 0,
                client_secret: inputClientSecret.value,
                token_api_url: inputTokenUrl.value.trim(),
                attendance_api_url: inputAttendanceUrl.value.trim()
            };
            
            // Update model
            if (newKey !== oldKey) {
                // Key changed (Rename)
                delete currentConfig[oldKey];
                selectedId = newKey;
            }
            
            currentConfig[selectedId] = updatedCompany;
            
            // Update lists and JSON
            renderCompanyList();
            selectCompany(selectedId);
            checkUnsavedChanges();
            
            showToast('Changes applied locally. Remember to Save to .env!', 'success');
            return true;
        }

        // Reset/Cancel Form changes for selected company
        function resetSelectedForm() {
            if (selectedId && currentConfig[selectedId]) {
                selectCompany(selectedId);
                showToast('Form reset to last applied state.', 'success');
            }
        }

        // Add New Company
        function generateRandomHex(length) {
            const chars = '0123456789abcdef';
            let result = '';
            for (let i = 0; i < length; i++) {
                result += chars[Math.floor(Math.random() * 16)];
            }
            return result;
        }

        function addNewCompany() {
            const newId = generateRandomHex(32);
            currentConfig[newId] = {
                grant_type: 'client_credentials',
                client_id: 3,
                client_secret: '',
                token_api_url: '',
                attendance_api_url: ''
            };
            
            searchQuery = '';
            searchInput.value = '';
            clearSearchBtn.style.display = 'none';
            
            renderCompanyList();
            selectCompany(newId);
            
            // Highlight Key to invite user to name it
            inputKey.focus();
            inputKey.select();
            
            checkUnsavedChanges();
            showToast('New company added! Edit details and Apply.', 'success');
        }

        // Delete Company Flow
        function triggerDelete(event, key) {
            if (event) event.stopPropagation();
            
            const friendlyName = getCompanyFriendlyName(key, currentConfig[key]);
            document.getElementById('confirm-modal-body').innerHTML = `Are you sure you want to delete <strong>${friendlyName}</strong>?<br><br>Key: <code style="font-family:monospace; background:rgba(0,0,0,0.3); padding:0.1rem 0.3rem; border-radius:4px; font-size:0.8rem;">${key}</code>`;
            
            confirmAction = () => {
                delete currentConfig[key];
                
                checkUnsavedChanges();
                renderCompanyList();
                
                if (selectedId === key) {
                    const remainingKeys = Object.keys(currentConfig);
                    if (remainingKeys.length > 0) {
                        selectCompany(remainingKeys[0]);
                    } else {
                        showEmptyWorkspace();
                    }
                }
                
                showToast(`Deleted ${friendlyName} locally.`, 'success');
            };
            
            openModal();
        }

        // Save State Checker (compare original vs current)
        function checkUnsavedChanges() {
            const originalStr = JSON.stringify(originalConfig);
            const currentStr = JSON.stringify(currentConfig);
            
            const changed = originalStr !== currentStr;
            
            if (changed) {
                saveEnvBtn.disabled = false;
                saveEnvBtn.classList.add('pulse-btn');
                unsavedBadge.style.display = 'inline-block';
            } else {
                saveEnvBtn.disabled = true;
                saveEnvBtn.classList.remove('pulse-btn');
                unsavedBadge.style.display = 'none';
            }
        }

        // Commit Config to server (.env)
        async function saveConfigToEnv() {
            // Apply current form changes if in form mode
            if (activeTab === 'form' && selectedId) {
                // Note: we don't block saving if form is unchanged, but if form has unsaved user edits, apply them
                // We'll run a quick compare of form inputs to the model
                const formId = inputKey.value.trim();
                const modelData = currentConfig[selectedId];
                if (modelData) {
                    const formChanged = formId !== selectedId || 
                                       selectGrantType.value !== modelData.grant_type ||
                                       parseInt(inputClientId.value) !== modelData.client_id ||
                                       inputClientSecret.value !== modelData.client_secret ||
                                       inputTokenUrl.value.trim() !== modelData.token_api_url ||
                                       inputAttendanceUrl.value.trim() !== modelData.attendance_api_url;
                    if (formChanged) {
                        const applied = applyFormChanges();
                        if (!applied) return; // validation failed
                    }
                }
            } else if (activeTab === 'json') {
                if (!validateJsonSyntax()) {
                    showToast('Cannot save. JSON syntax is invalid.', 'danger');
                    return;
                }
            }

            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(currentConfig)
                });
                
                const result = await res.json();
                if (result.success) {
                    originalConfig = JSON.parse(JSON.stringify(currentConfig)); // sync
                    checkUnsavedChanges();
                    showToast('Configuration successfully saved to .env file!', 'success');
                } else {
                    showToast(`Failed to save: ${result.error}`, 'danger');
                }
            } catch (err) {
                showToast('Network error while saving config', 'danger');
                console.error(err);
            }
        }

        // JSON validation helper
        function validateJsonSyntax() {
            const rawText = jsonTextarea.value;
            try {
                const parsed = JSON.parse(rawText);
                
                // Extra validation: must be an object
                if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
                    throw new Error("Root element must be a JSON Object");
                }
                
                // Extra validation: keys must be 32 hex chars, values must be objects
                for (let key in parsed) {
                    if (key.length !== 32 || !/^[0-9a-fA-F]+$/.test(key)) {
                        throw new Error(`Key "${key}" is not a 32-character hexadecimal key`);
                    }
                    if (typeof parsed[key] !== 'object' || parsed[key] === null || Array.isArray(parsed[key])) {
                        throw new Error(`Value for key "${key}" must be a config object`);
                    }
                }

                currentConfig = parsed;
                checkUnsavedChanges();
                
                jsonStatus.className = 'json-status valid';
                jsonStatus.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg><span>Valid JSON configuration</span>`;
                
                // Update selectedId if it got deleted or renamed in raw json
                if (selectedId && !currentConfig[selectedId]) {
                    const keys = Object.keys(currentConfig);
                    selectedId = keys.length > 0 ? keys[0] : '';
                }
                
                return true;
            } catch (e) {
                jsonStatus.className = 'json-status invalid';
                jsonStatus.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg><span>Invalid JSON: ${e.message}</span>`;
                return false;
            }
        }

        // Autocomplete Attendance URL
        function handleTokenUrlChange() {
            const tokenUrl = inputTokenUrl.value.trim();
            const attendanceUrl = inputAttendanceUrl.value.trim();
            
            // Automatically fill the attendance url if it's empty or was previously autogenerated
            if (tokenUrl && (!attendanceUrl || inputAttendanceUrl.dataset.autogenerated === 'true')) {
                try {
                    const urlObj = new URL(tokenUrl);
                    const origin = urlObj.origin;
                    inputAttendanceUrl.value = `${origin}/api/attendance-raw/client/storage-data`;
                    inputAttendanceUrl.dataset.autogenerated = 'true';
                    
                    // Show helpful autocomplete info box
                    autocompleteBox.style.display = 'flex';
                    setTimeout(() => {
                        autocompleteBox.style.opacity = '1';
                    }, 50);
                } catch(e) {
                    // Try simple string replacement if URL parsing fails
                    const match = tokenUrl.match(/^(https?:\/\/[^\/]+)/);
                    if (match && match[1]) {
                        inputAttendanceUrl.value = `${match[1]}/api/attendance-raw/client/storage-data`;
                        inputAttendanceUrl.dataset.autogenerated = 'true';
                        autocompleteBox.style.display = 'flex';
                    }
                }
            }
        }

        // Clipboard Copy
        function copyToClipboard(e, text) {
            e.stopPropagation();
            navigator.clipboard.writeText(text).then(() => {
                showToast('Key copied to clipboard!', 'success');
            }).catch(err => {
                showToast('Failed to copy key', 'danger');
            });
        }

        // Toast Messages
        function showToast(message, type = 'primary') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            let icon = '';
            if (type === 'success') {
                icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--success)"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            } else if (type === 'danger') {
                icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--danger)"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
            }
            
            toast.innerHTML = `
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    ${icon}
                    <span>${message}</span>
                </div>
                <button class="toast-close">&times;</button>
            `;
            
            container.appendChild(toast);
            
            // Animate in
            setTimeout(() => toast.classList.add('show'), 10);
            
            // Auto remove
            const removeTimeout = setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
            
            // Close button click
            toast.querySelector('.toast-close').onclick = () => {
                clearTimeout(removeTimeout);
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            };
        }

        // Confirm Dialog Helpers
        function openModal() {
            modal.classList.add('active');
        }

        function closeModal() {
            modal.classList.remove('active');
            confirmAction = null;
        }

        // Shutdown CLI Server
        async function shutdownServer() {
            const confirmStop = confirm("Shutdown Configurer web server and stop CLI process?");
            if (!confirmStop) return;
            
            try {
                showToast('Shutting down server...', 'primary');
                await fetch('/api/shutdown', { method: 'POST' });
                document.body.innerHTML = `
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; text-align:center; font-family:sans-serif; color:var(--text-secondary); background-color:var(--bg-color);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--danger); margin-bottom:1rem;"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
                        <h2>Server Shutdown</h2>
                        <p style="margin-top:0.5rem;">The configurer server has been shut down successfully.<br>You can close this tab now.</p>
                    </div>
                `;
            } catch (err) {
                console.error(err);
                showToast('Error sending shutdown command.', 'danger');
            }
        }

        // Event Listeners
        document.addEventListener('DOMContentLoaded', () => {
            fetchConfig();

            // Search input
            searchInput.oninput = (e) => {
                searchQuery = e.target.value;
                clearSearchBtn.style.display = searchQuery ? 'flex' : 'none';
                renderCompanyList();
            };

            clearSearchBtn.onclick = () => {
                searchQuery = '';
                searchInput.value = '';
                clearSearchBtn.style.display = 'none';
                renderCompanyList();
            };

            // Add Company Button
            document.getElementById('add-company-btn').onclick = addNewCompany;
            document.getElementById('empty-add-btn').onclick = addNewCompany;

            // Generate Key
            document.getElementById('generate-key-btn').onclick = () => {
                const newHex = generateRandomHex(32);
                inputKey.value = newHex;
                showToast('Generated new random hex key!', 'success');
            };

            // Secret Show/Hide toggle
            document.getElementById('toggle-secret-btn').onclick = () => {
                if (inputClientSecret.type === 'password') {
                    inputClientSecret.type = 'text';
                    document.getElementById('secret-eye-icon').innerHTML = `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>`;
                } else {
                    inputClientSecret.type = 'password';
                    document.getElementById('secret-eye-icon').innerHTML = `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>`;
                }
            };

            // URL inputs listener (auto-complete suggegstion)
            inputTokenUrl.oninput = handleTokenUrlChange;
            inputAttendanceUrl.oninput = () => {
                // If user edits, mark autocomplete helper as user-customized
                inputAttendanceUrl.dataset.autogenerated = 'false';
                autocompleteBox.style.opacity = '0';
                setTimeout(() => { autocompleteBox.style.display = 'none'; }, 200);
            };

            // Tab Switching
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.onclick = (e) => {
                    const tab = e.target.dataset.tab;
                    if (tab === activeTab) return;
                    
                    // If shifting away from form, apply local form changes first
                    if (activeTab === 'form' && tab === 'json') {
                        const success = applyFormChanges();
                        if (!success) return; // Validation failed, abort tab shift
                    }
                    
                    activeTab = tab;
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
                    document.getElementById(`pane-${tab}`).classList.add('active');
                    
                    if (tab === 'json') {
                        jsonTextarea.value = JSON.stringify(currentConfig, null, 2);
                        validateJsonSyntax();
                    } else {
                        // Switching back to form, reload form content
                        selectCompany(selectedId);
                    }
                };
            });

            // JSON Editor textarea listener
            jsonTextarea.oninput = validateJsonSyntax;

            // Form Workspace action buttons
            document.getElementById('apply-changes-btn').onclick = applyFormChanges;
            document.getElementById('cancel-changes-btn').onclick = resetSelectedForm;
            document.getElementById('delete-company-btn').onclick = (e) => triggerDelete(e, selectedId);

            // Modal action buttons
            document.getElementById('confirm-cancel').onclick = closeModal;
            document.getElementById('confirm-yes').onclick = () => {
                if (confirmAction) confirmAction();
                closeModal();
            };

            // Top Save button
            saveEnvBtn.onclick = saveConfigToEnv;
            shutdownBtn.onclick = shutdownServer;
        });
    </script>
</body>
</html>
"""

class ConfigRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress request logging to keep console clean
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif self.path == '/api/config':
            config = read_company_config()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(config).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                config_dict = json.loads(post_data.decode('utf-8'))
                write_company_config(config_dict)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
        elif self.path == '/api/shutdown':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            
            def shutdown():
                print("\\nStopping server and exiting process...")
                self.server.shutdown()
                sys.exit(0)
            
            threading.Thread(target=shutdown).start()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def start_server(host, port):
    server = HTTPServer((host, port), ConfigRequestHandler)
    print(f"\\n=========================================")
    print(f" Nusawork Company Configurer UI Server")
    print(f"=========================================")
    print(f" Running at: http://{host}:{port}")
    print(f" Press Ctrl+C in terminal or click 'Shutdown' in UI to exit.")
    
    # Auto-open in default browser
    browser_host = '127.0.0.1' if host == '0.0.0.0' else host
    url = f"http://{browser_host}:{port}"
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down server...")
        server.server_close()
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nusawork Company Configurer UI Server")
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='IP address to bind the server (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=None, help='Port to run the server on (default: auto-detect free port starting at 5000)')
    
    args = parser.parse_args()
    
    host = args.ip
    if args.port is not None:
        port = args.port
    else:
        port = find_free_port(host, 5000)
        
    start_server(host, port)
