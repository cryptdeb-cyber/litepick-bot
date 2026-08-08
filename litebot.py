#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANTOINE BOT v3.0 - Web Interface (Fichier Tokana)
"""

import asyncio
import aiohttp
import json
import time
import logging
import re
import threading
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "https://litepick.io"
BASE_BET = 0.000001

# Ampidino io mba hiseho ny logs rehetra
sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
CORS(app)

# ============================================================
# JAVASCRIPT ENGINE (ANTOINE BOT v2.63)
# ============================================================

JS_ENGINE = """
// ============================================================
// ANTOINE BOT v2.63 - With CSRF Token
// ============================================================

if (window.__BOT_RUNNING) throw new Error("Bot efa mandeha! F5 aloha");
window.__BOT_RUNNING = true;
const BASE_BET = 0.000001;

let CACHED_INPUT = null;
let CACHED_2X = null;
let CACHED_MIN = null;
let lastCacheTime = 0;
const CACHE_TIMEOUT = 500;

// ============================================================
// CORE FUNCTIONS
// ============================================================

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function waitForCondition(conditionFn, maxWaitMs = 86400000) {
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitMs) {
        if (!window.__BOT_RUNNING) return false;
        try {
            if (await conditionFn()) return true;
        } catch (e) {
            console.log("[waitForCondition] Error:", e);
        }
        await wait(30);
    }
    return false;
}

function isReadyToClick(el) {
    if (!el) return false;
    try {
        const style = window.getComputedStyle(el);
        const isVisible = el.offsetWidth > 0 && el.offsetHeight > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        if (!isVisible) return false;
        const isDisabled = el.disabled || el.getAttribute('disabled') === 'true' || el.classList.contains('disabled') || style.pointerEvents === 'none';
        if (isDisabled) return false;
        const opacity = parseFloat(style.opacity);
        if (!isNaN(opacity) && opacity < 0.7) return false;
        let isOutsideGame = el.closest('header, footer, nav, #mobile_nav, .mobile_bottom_nav, [class*="menu"], [class*="nav"], [class*="footer"], [class*="header"], [class*="sidebar"], [class*="social"]');
        if (isOutsideGame) return false;
        return true;
    } catch (e) {
        return false;
    }
}

function getMiseInput() {
    CACHED_INPUT = null;
    let btn2x = Array.from(document.querySelectorAll('button, div, span')).find(el => el.textContent.trim() === "2X" && el.offsetWidth > 0);
    if (btn2x) {
        let p = btn2x.parentElement;
        for (let i = 0; i < 5 && p; i++) {
            let inp = p.querySelector('input[type="text"], input[type="number"], input:not([type])');
            if (inp && !inp.disabled && inp.offsetWidth > 0) {
                CACHED_INPUT = inp;
                lastCacheTime = Date.now();
                return inp;
            }
            p = p.parentElement;
        }
    }
    let inp = Array.from(document.querySelectorAll('input')).find(el => {
        return el.value && el.value.includes("0.0000") && !el.disabled && el.offsetWidth > 0;
    });
    if (inp) {
        CACHED_INPUT = inp;
        lastCacheTime = Date.now();
        return inp;
    }
    inp = Array.from(document.querySelectorAll('input')).find(el => !el.disabled && el.offsetWidth > 0);
    if (inp) {
        CACHED_INPUT = inp;
        lastCacheTime = Date.now();
        return inp;
    }
    return null;
}

async function getMiseValue() {
    try {
        let input = getMiseInput();
        if (!input) return BASE_BET;
        let val = parseFloat(input.value.replace(',', '.'));
        return isNaN(val) ? BASE_BET : val;
    } catch (e) {
        return BASE_BET;
    }
}

function get2XBtn() {
    CACHED_2X = null;
    let btn = Array.from(document.querySelectorAll('button, div, span')).find(el => {
        return el.textContent.trim() === "2X" && el.offsetWidth > 0 && el.offsetHeight > 0;
    }) || null;
    if (btn) CACHED_2X = btn;
    return btn;
}

function getMinBtn() {
    CACHED_MIN = null;
    let btn = Array.from(document.querySelectorAll('button, div, span')).find(el => {
        let txt = el.textContent.trim().toLowerCase();
        return (txt === "min" || txt === "minimum") && el.offsetWidth > 0 && el.offsetHeight > 0;
    }) || null;
    if (btn) CACHED_MIN = btn;
    return btn;
}

function setMiseDirect(targetValue) {
    try {
        let input = getMiseInput();
        if (!input) return false;
        let strVal = targetValue.toFixed(8);
        let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        if (nativeSetter) nativeSetter.call(input, strVal);
        else input.value = strVal;

        input.dispatchEvent(new Event('focus', { bubbles: true }));
        input.dispatchEvent(new InputEvent('input', { bubbles: true, data: strVal, inputType: 'insertText' }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.dispatchEvent(new Event('blur', { bubbles: true }));
        return true;
    } catch (e) {
        return false;
    }
}

async function syncMiseWithStreak() {
    if (currentLossStreak >= 15) {
        currentLossStreak = 0;
    }
    let inputEnabled = await waitForCondition(() => {
        let inp = getMiseInput();
        return inp && !inp.disabled && inp.offsetWidth > 0;
    }, 86400000);

    if (!inputEnabled) return false;

    let currentMise = await getMiseValue();
    let targetMise = currentLossStreak === 0 ? BASE_BET : BASE_BET * Math.pow(2, currentLossStreak);

    if (currentLossStreak === 0) {
        if (Math.abs(currentMise - BASE_BET) < 0.00000001) return true;
        let btnMin = getMinBtn();
        if (btnMin && isReadyToClick(btnMin)) {
            await moveAndClick(btnMin, false);
            await wait(500);
        }
        for (let i = 0; i < 100; i++) {
            setMiseDirect(BASE_BET);
            await wait(500);
            let miseAfter = await getMiseValue();
            if (Math.abs(miseAfter - BASE_BET) < 0.00000001) return true;
        }
        return false;
    }

    let btn2X = get2XBtn();
    if (btn2X) {
        let miseBefore = await getMiseValue();
        let retryCount = 0;
        let maxRetry = 1;

        while (retryCount < maxRetry) {
            await waitForCondition(() => isReadyToClick(btn2X), 86400000);
            await moveAndClick(btn2X, false);

            await waitForCondition(async () => {
                let newMise = await getMiseValue();
                return newMise > miseBefore + 0.00000001;
            }, 86400000);

            let miseAfter = await getMiseValue();
            if (Math.abs(miseAfter - targetMise) < 0.00000001) return true;
            retryCount++;
            await wait(500);
        }
    }
    return false;
}

function ensureCursor() {
    let cursor = document.getElementById('bot-virtual-cursor');
    if (!cursor) {
        cursor = document.createElement('div');
        cursor.id = 'bot-virtual-cursor';
        Object.assign(cursor.style, {
            position: 'absolute', width: '20px', height: '20px', borderRadius: '50%',
            backgroundColor: 'rgba(255, 0, 0, 0.8)', border: '2px solid white',
            boxShadow: '0 0 10px rgba(255, 0, 0, 0.8)', pointerEvents: 'none', zIndex: '999999',
            transition: 'all 0.05s ease-in-out',
            top: '0px', left: '0px', transform: 'translate(-50%, -50%)'
        });
        document.body.appendChild(cursor);
    }
    return cursor;
}

function triggerClickAnimation() {
    let virtualCursor = ensureCursor();
    virtualCursor.style.transform = 'translate(-50%, -50%) scale(0.5)';
    virtualCursor.style.backgroundColor = 'rgba(0, 255, 0, 0.9)';
    setTimeout(() => {
        virtualCursor.style.transform = 'translate(-50%, -50%) scale(1)';
        virtualCursor.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
    }, 30);
}

async function moveAndClick(el, isCommencer = false) {
    if (!el) return false;
    try {
        let ready = await waitForCondition(() => isReadyToClick(el), 86400000);
        if (!ready) return false;
        const rect = el.getBoundingClientRect();
        let virtualCursor = ensureCursor();
        virtualCursor.style.left = `${rect.left + rect.width / 2 + window.scrollX}px`;
        virtualCursor.style.top = `${rect.top + rect.height / 2 + window.scrollY}px`;
        if (isCommencer) await wait(50); else await wait(80);
        triggerClickAnimation();
        await wait(30);
        if (typeof el.click === 'function') el.click();
        else el.dispatchEvent(new MouseEvent('click', { bubbles: true, view: window }));
        return true;
    } catch (e) {
        return false;
    }
}

function getActionBtn() {
    try {
        return Array.from(document.querySelectorAll('button, div, span')).find(el => {
            let txt = el.textContent.trim().toUpperCase();
            let isOutside = el.closest('header, footer, nav, #mobile_nav, .mobile_bottom_nav, [class*="menu"], [class*="nav"], [class*="footer"], [class*="header"]');
            return (txt === "COMMENCER" || txt === "START" || txt === "RETRAIT D'ARGENT" || txt === "RETRAIT" || txt === "CASHOUT" || txt === "ENCAISSER") && el.offsetWidth > 0 && !isOutside;
        }) || null;
    } catch (e) {
        return null;
    }
}

function getBalance() {
    try {
        let balanceElement = document.querySelector('.balance, [class*="balance"], #balance');
        if (!balanceElement) {
            balanceElement = Array.from(document.querySelectorAll('div, span, p')).find(el => {
                let isOutside = el.closest('header, footer, nav, #mobile_nav, .mobile_bottom_nav');
                return /^[0-9]+([.,][0-9]+)?\\s*$/.test(el.textContent.trim()) && el.offsetWidth > 0 && !isOutside;
            });
        }
        if (balanceElement) {
            let val = parseFloat(balanceElement.textContent.replace(/[^0-9.]/g, '').replace(',', '.'));
            return isNaN(val) ? 0 : val;
        }
    } catch (e) {}
    return 0;
}

function getTilesByRow() {
    try {
        let allElements = Array.from(document.querySelectorAll('div, span, p, button'));
        let allTiles = allElements.filter(el => {
            if (el.offsetWidth === 0 || el.offsetHeight === 0) return false;
            let isTileSize = el.offsetWidth > 30 && el.offsetWidth < 150 && el.offsetHeight > 30 && el.offsetHeight < 100;
            let txt = el.textContent.trim().toLowerCase();
            let isControlBtn = txt.includes("start") || txt.includes("commencer") || txt.includes("cashout") || txt.includes("retrait") || txt === "2x" || txt === "1/2" || txt === "min" || txt === "max" || txt === "facile" || txt === "moyen" || txt === "dur" || txt === "easy" || txt === "medium" || txt === "hard";
            let isOutside = el.closest('header, footer, nav, #mobile_nav, .mobile_bottom_nav, [class*="menu"], [class*="nav"], [class*="footer"], [class*="header"], [class*="sidebar"]');
            return isTileSize && !isControlBtn && !isOutside;
        });
        let sortedTiles = allTiles.sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top);
        let rows = [];
        let tempTiles = [...sortedTiles];
        while (tempTiles.length > 0) {
            let row = tempTiles.splice(0, 3);
            row.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
            rows.push(row);
        }
        return rows;
    } catch (e) {
        return [];
    }
}

function getActiveTilesLigne1() {
    try { return (getTilesByRow()[0] || []).filter(el => isReadyToClick(el)); } catch (e) { return []; }
}

function getActiveTilesLigne2() {
    try { return (getTilesByRow()[1] || []).filter(el => isReadyToClick(el)); } catch (e) { return []; }
}

function getActiveTilesLigne3() {
    try { return (getTilesByRow()[2] || []).filter(el => isReadyToClick(el)); } catch (e) { return []; }
}

function getRandomTile(tilesArray) {
    if (window.__USE_GUARANTEED && window.__GUARANTEED_TILE !== null) {
        let idx = window.__GUARANTEED_TILE;
        if (idx < tilesArray.length) {
            console.log("[API] Using guaranteed tile: " + (idx + 1));
            return tilesArray[idx];
        }
    }
    return tilesArray.length ? tilesArray[Math.floor(Math.random() * tilesArray.length)] : null;
}

let currentLossStreak = 0;
let lastBalance = 0;

// ============================================================
// PYTHON API COMMUNICATION BRIDGE
// ============================================================

window.setGuaranteedTile = function(tileIndex) {
    if (tileIndex !== null && tileIndex !== undefined && tileIndex >= 0) {
        window.__GUARANTEED_TILE = tileIndex;
        window.__USE_GUARANTEED = true;
        console.log("[API] Guaranteed tile from Python: " + (tileIndex + 1));
        return true;
    } else {
        window.__GUARANTEED_TILE = null;
        window.__USE_GUARANTEED = false;
        return false;
    }
};

window.getBotStatus = function() {
    return {
        running: window.__BOT_RUNNING || false,
        streak: currentLossStreak || 0,
        balance: getBalance(),
        loggedIn: window.location.href.includes('gems.php'),
        tilesCount: getTilesByRow().flat().length,
        useGuaranteed: window.__USE_GUARANTEED || false,
        guaranteedTile: window.__GUARANTEED_TILE
    };
};

window.resetStreak = function() {
    currentLossStreak = 0;
    console.log("[Python] Streak reset");
};

window.stopBot = function() {
    window.__BOT_RUNNING = false;
    console.log("[Python] Bot stopped");
};

// ============================================================
// MAIN BOT LOOP
// ============================================================

async function startBot() {
    if (!window.__BOT_RUNNING) return;
    if (!window.location.href.includes('gems.php')) {
        setTimeout(startBot, 1000);
        return;
    }
    if (lastBalance === 0) lastBalance = getBalance();

    try {
        CACHED_INPUT = null;
        CACHED_2X = null;
        CACHED_MIN = null;

        await syncMiseWithStreak();

        console.log(`%c--- Session (Streak: ${currentLossStreak} | Mise: ${await getMiseValue()}) ---`, "color: cyan; font-weight: bold;");

        await waitForCondition(() => {
            let btn = getActionBtn();
            return btn && isReadyToClick(btn) && (btn.textContent.includes("COMMENCER") || btn.textContent.includes("START"));
        }, 86400000);

        let actionBtn = getActionBtn();
        if (actionBtn) await moveAndClick(actionBtn, true);
        await wait(300);

        let readyL1 = await waitForCondition(() => getActiveTilesLigne1().length > 0, 86400000);
        if (!readyL1) { setTimeout(startBot, 300); return; }
        
        await moveAndClick(getRandomTile(getActiveTilesLigne1()), false);
        
        console.log("-> Miandry verification Ligne 1...");
        await wait(300);

        await waitForCondition(() => {
            let btn = getActionBtn();
            return (btn && isReadyToClick(btn) && (btn.textContent.includes("COMMENCER") || btn.textContent.includes("START"))) || (getActiveTilesLigne2().length > 0);
        }, 86400000);

        let hasL2Active = getActiveTilesLigne2().length > 0;

        if (hasL2Active) {
            if (currentLossStreak === 0) {
                let cashoutBtn = getActionBtn();
                if (cashoutBtn && (cashoutBtn.textContent.includes("RETRAIT") || cashoutBtn.textContent.includes("CASHOUT"))) {
                    await moveAndClick(cashoutBtn, false);
                    await wait(300);
                }
                window.__USE_GUARANTEED = false;
                window.__GUARANTEED_TILE = null;
            } else {
                let readyL2 = await waitForCondition(() => getActiveTilesLigne2().length > 0, 86400000);
                if (readyL2) {
                    await moveAndClick(getRandomTile(getActiveTilesLigne2()), false);
                    
                    console.log("-> Miandry verification Ligne 2...");
                    await wait(300);

                    console.log("-> Miandry ny fihetsiky ny Ligne 3...");

                    let l3Ready = await waitForCondition(() => {
                        let l3Active = getActiveTilesLigne3().length > 0;
                        let btn = getActionBtn();
                        let isStart = btn && (btn.textContent.toUpperCase().includes("COMMENCER") || btn.textContent.toUpperCase().includes("START"));
                        return l3Active || isStart;
                    }, 86400000);

                    await wait(500);

                    let hasL3ActiveNow = getActiveTilesLigne3().length > 0;

                    if (hasL3ActiveNow) {
                        console.log("%c[L2 WIN] Ligne 3 active !", "color: lime; font-weight: bold;");
                        
                        let cashoutBtn = getActionBtn();
                        if (cashoutBtn && (cashoutBtn.textContent.toUpperCase().includes("CASHOUT") || 
                                          cashoutBtn.textContent.toUpperCase().includes("RETRAIT") || 
                                          cashoutBtn.textContent.toUpperCase().includes("ENCAISSER"))) {
                            await moveAndClick(cashoutBtn, false);
                            await wait(300);
                        }
                        
                        currentLossStreak = 0;
                        await syncMiseWithStreak();
                        window.__USE_GUARANTEED = false;
                        window.__GUARANTEED_TILE = null;
                    } else {
                        console.log("%c[LOSS L2] Pas de Ligne 3 -> Streak++", "color: red;");
                        currentLossStreak++;
                        await wait(500);
                    }
                }
            }
        } else {
            console.log("%c[LOSS L1] -> Streak++", "color: red;");
            currentLossStreak++;
            await wait(300);
        }

        lastBalance = getBalance();
        let randomDelay = 200 + Math.random() * 300;
        setTimeout(startBot, randomDelay);

    } catch (e) {
        console.log("%c[BOT ERROR] Misy erreur - Continue...", "color: red; font-weight: bold;");
        console.log(e);
        setTimeout(startBot, 300);
    }
}

console.log("%c[ANTOINE BOT v2.63] With CSRF Token", "color: #00ff00; font-size: 16px; font-weight: bold;");
startBot();
"""

# ============================================================
# BOT CONTROLLER
# ============================================================

class BotController:
    def __init__(self):
        self.driver = None
        self.running = False
        self.bot_thread = None
        self.status = {
            'running': False,
            'streak': 0,
            'balance': 0,
            'tilesCount': 0,
            'loggedIn': False
        }
    
    def start(self):
        if self.running:
            return {"success": False, "message": "Bot efa mandeha"}
        
        try:
            def run_bot():
                asyncio.run(self._run_bot())
            
            self.bot_thread = threading.Thread(target=run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            self.running = True
            self.status['running'] = True
            
            return {"success": True, "message": "Bot started successfully"}
            
        except Exception as e:
            self.running = False
            return {"success": False, "message": str(e)}
    
    async def _run_bot(self):
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,720')
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            
            self.driver.get(f"{BASE_URL}/gems.php")
            await asyncio.sleep(5)
            
            self.driver.execute_script(JS_ENGINE)
            self.driver.execute_script("window.startBot();")
            
            self.status['loggedIn'] = True
            
            while self.running and self.driver:
                try:
                    status = self.driver.execute_script("return window.getBotStatus();")
                    if status:
                        self.status['streak'] = status.get('streak', 0)
                        self.status['balance'] = status.get('balance', 0)
                        self.status['tilesCount'] = status.get('tilesCount', 0)
                        self.status['loggedIn'] = status.get('loggedIn', False)
                except:
                    pass
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            self.running = False
            self.status['running'] = False
    
    def stop(self):
        if not self.running:
            return {"success": False, "message": "Bot tsy mandeha"}
        
        try:
            if self.driver:
                self.driver.execute_script("window.stopBot();")
            self.running = False
            self.status['running'] = False
            return {"success": True, "message": "Bot stopped"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def reset_streak(self):
        if not self.driver:
            return {"success": False, "message": "Bot tsy mandeha"}
        
        try:
            self.driver.execute_script("window.resetStreak();")
            self.status['streak'] = 0
            return {"success": True, "message": "Streak reset"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_status(self):
        return self.status

bot = BotController()

# ============================================================
# HTML PAGE (Ao anaty Python mivantana)
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="mg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANTOINE BOT</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 25px;
            padding: 40px;
            max-width: 450px;
            width: 100%;
            box-shadow: 0 25px 80px rgba(0,0,0,0.5);
            animation: slideUp 0.5s ease;
        }
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header .logo { font-size: 4em; margin-bottom: 10px; }
        .header h1 {
            font-size: 2em;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        .header .version { color: #666; font-size: 0.9em; }
        
        .status-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s;
        }
        .status-card.running {
            border-color: #22c55e;
            box-shadow: 0 0 40px rgba(34,197,94,0.1);
        }
        .status-card .icon { font-size: 3.5em; display: block; }
        .status-card .status-text { 
            font-size: 1.5em; 
            font-weight: bold; 
            color: white;
            margin: 10px 0;
        }
        .status-card .status-sub { color: #888; font-size: 0.9em; }
        .status-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 1.5s infinite;
        }
        .status-dot.running { background: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.5); }
        .status-dot.stopped { background: #ef4444; animation: none; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.3); } }
        
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 20px 0;
        }
        .stat {
            background: rgba(255,255,255,0.03);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .stat .label { color: #888; font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat .value {
            font-size: 1.3em;
            font-weight: bold;
            color: white;
            margin-top: 5px;
        }
        .stat .value.gold { color: #f59e0b; }
        .stat .value.green { color: #22c55e; }
        .stat .value.blue { color: #3b82f6; }
        .stat .value.red { color: #ef4444; }
        
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 20px 0;
        }
        .btn {
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            color: white;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .btn:active { transform: scale(0.95); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
        .btn-start {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            grid-column: span 2;
        }
        .btn-start:hover { box-shadow: 0 10px 25px rgba(34,197,94,0.3); }
        .btn-stop {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        .btn-stop:hover { box-shadow: 0 10px 25px rgba(239,68,68,0.3); }
        .btn-reset {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }
        .btn-reset:hover { box-shadow: 0 10px 25px rgba(245,158,11,0.3); }
        
        .log-box {
            background: rgba(0,0,0,0.4);
            border-radius: 12px;
            padding: 15px;
            max-height: 150px;
            overflow-y: auto;
            margin: 15px 0;
            font-family: 'Consolas', monospace;
            font-size: 0.8em;
            line-height: 1.8;
        }
        .log-box::-webkit-scrollbar { width: 4px; }
        .log-box::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 4px; }
        .log-box::-webkit-scrollbar-thumb { background: #667eea; border-radius: 4px; }
        .log-entry { padding: 2px 0; color: #888; }
        .log-entry .time { color: #555; margin-right: 10px; }
        .log-entry.success { color: #4ade80; }
        .log-entry.error { color: #f87171; }
        .log-entry.warning { color: #fbbf24; }
        .log-entry.info { color: #60a5fa; }
        
        .footer {
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
            font-size: 0.8em;
            color: #555;
        }
        .footer a { color: #667eea; text-decoration: none; }
        
        .loading-spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 2px solid white;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        @media (max-width: 480px) {
            .container { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🤖</div>
            <h1>ANTOINE BOT</h1>
            <div class="version">v3.0 • Web Control</div>
        </div>
        
        <div class="status-card" id="statusCard">
            <span class="icon" id="statusIcon">⏸️</span>
            <div class="status-text">
                <span class="status-dot stopped" id="statusDot"></span>
                <span id="statusText">Stopped</span>
            </div>
            <div class="status-sub" id="statusSub">Click Start to begin</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="label">💰 Balance</div>
                <div class="value gold" id="balance">0.00000000</div>
            </div>
            <div class="stat">
                <div class="label">📈 Streak</div>
                <div class="value" id="streak">0</div>
            </div>
            <div class="stat">
                <div class="label">🎯 Tiles</div>
                <div class="value blue" id="tiles">0</div>
            </div>
            <div class="stat">
                <div class="label">🔒 Status</div>
                <div class="value green" id="loginStatus">✅ Ready</div>
            </div>
        </div>
        
        <div class="btn-group">
            <button class="btn btn-start" id="startBtn">
                <i class="fas fa-play"></i> Start Bot
            </button>
            <button class="btn btn-stop" id="stopBtn" disabled>
                <i class="fas fa-stop"></i> Stop
            </button>
            <button class="btn btn-reset" id="resetBtn">
                <i class="fas fa-sync"></i> Reset Streak
            </button>
        </div>
        
        <div class="log-box" id="logBox">
            <div class="log-entry info"><span class="time">[System]</span> Bot loaded</div>
            <div class="log-entry info"><span class="time">[System]</span> Ready to start</div>
        </div>
        
        <div class="footer">
            Protected by <a href="#">ANTOINE SECURITY</a> v3.0
        </div>
    </div>
    
    <script>
        let statusInterval = null;
        
        function updateUI(data) {
            document.getElementById('balance').textContent = (data.balance || 0).toFixed(8);
            document.getElementById('streak').textContent = data.streak || 0;
            document.getElementById('tiles').textContent = data.tilesCount || 0;
            
            if (data.running) {
                document.getElementById('statusIcon').textContent = '▶️';
                document.getElementById('statusText').textContent = 'Running';
                document.getElementById('statusSub').textContent = 'Bot is actively playing';
                document.getElementById('statusDot').className = 'status-dot running';
                document.getElementById('statusCard').className = 'status-card running';
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('startBtn').innerHTML = '<span class="loading-spinner"></span> Running...';
            } else {
                document.getElementById('statusIcon').textContent = '⏸️';
                document.getElementById('statusText').textContent = 'Stopped';
                document.getElementById('statusSub').textContent = 'Click Start to begin';
                document.getElementById('statusDot').className = 'status-dot stopped';
                document.getElementById('statusCard').className = 'status-card';
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('startBtn').innerHTML = '<i class="fas fa-play"></i> Start Bot';
            }
            
            if (data.loggedIn) {
                document.getElementById('loginStatus').textContent = '✅ Logged In';
                document.getElementById('loginStatus').className = 'value green';
            } else {
                document.getElementById('loginStatus').textContent = '⏳ Loading...';
                document.getElementById('loginStatus').className = 'value';
            }
        }
        
        function addLog(message, type = 'info') {
            const logBox = document.getElementById('logBox');
            const entry = document.createElement('div');
            const time = new Date().toLocaleTimeString();
            entry.className = `log-entry ${type}`;
            entry.innerHTML = `<span class="time">[${time}]</span> ${message}`;
            logBox.appendChild(entry);
            logBox.scrollTop = logBox.scrollHeight;
            while (logBox.children.length > 100) logBox.removeChild(logBox.firstChild);
        }
        
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                updateUI(data);
            } catch (e) {
                console.error('Status fetch error:', e);
            }
        }
        
        async function startBot() {
            addLog('▶️ Starting bot...', 'info');
            document.getElementById('startBtn').disabled = true;
            
            try {
                const res = await fetch('/api/start', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    addLog('✅ Bot started successfully', 'success');
                } else {
                    addLog(`❌ Failed: ${data.message}`, 'error');
                    document.getElementById('startBtn').disabled = false;
                }
            } catch (e) {
                addLog(`❌ Error: ${e.message}`, 'error');
                document.getElementById('startBtn').disabled = false;
            }
        }
        
        async function stopBot() {
            addLog('⏹️ Stopping bot...', 'info');
            document.getElementById('stopBtn').disabled = true;
            
            try {
                const res = await fetch('/api/stop', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    addLog('✅ Bot stopped', 'success');
                } else {
                    addLog(`❌ Failed: ${data.message}`, 'error');
                }
            } catch (e) {
                addLog(`❌ Error: ${e.message}`, 'error');
            }
            document.getElementById('stopBtn').disabled = false;
        }
        
        async function resetStreak() {
            addLog('🔄 Resetting streak...', 'info');
            try {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    addLog('✅ Streak reset to 0', 'success');
                } else {
                    addLog(`❌ Failed: ${data.message}`, 'error');
                }
            } catch (e) {
                addLog(`❌ Error: ${e.message}`, 'error');
            }
        }
        
        document.getElementById('startBtn').addEventListener('click', startBot);
        document.getElementById('stopBtn').addEventListener('click', stopBot);
        document.getElementById('resetBtn').addEventListener('click', resetStreak);
        
        fetchStatus();
        statusInterval = setInterval(fetchStatus, 2000);
        addLog('✅ Interface ready', 'success');
    </script>
</body>
</html>
"""

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/api/status')
def api_status():
    return jsonify(bot.get_status())

@app.route('/api/start', methods=['POST'])
def api_start():
    return jsonify(bot.start())

@app.route('/api/stop', methods=['POST'])
def api_stop():
    return jsonify(bot.stop())

@app.route('/api/reset', methods=['POST'])
def api_reset():
    return jsonify(bot.reset_streak())

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🤖 ANTOINE BOT v3.0 - Web Interface")
    print("=" * 60)
    print(f"📊 Interface: http://localhost:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port)
