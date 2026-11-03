import os
import time
import shutil
import random
import re
from playwright.sync_api import sync_playwright

PATH_TO_VIDEO_FOLDER = "./video"

def _safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "video"

CURSOR_SCRIPT = r"""
(() => {
    if (window.__cursorInjected) return;
    window.__cursorInjected = true;
    const init = () => {
        if (!document.body) return;
        const wrap = document.createElement('div');
        wrap.id = '__cursor_wrap';
        wrap.style.cssText = `
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 2147483647;
        `;
        const halo = document.createElement('div');
        halo.id = '__cursor_halo';
        halo.style.cssText = `
            position: absolute;
            width: 64px; height: 64px;
            margin-left: -32px; margin-top: -32px;
            border-radius: 50%;
            background: rgba(255, 220, 0, 0.35);
            pointer-events: none;
            transition: transform 0.02s linear;
        `;
        const arrow = document.createElement('div');
        arrow.id = '__cursor_arrow';
        arrow.style.cssText = `
            position: absolute;
            width: 32px; height: 32px;
            pointer-events: none;
            transition: transform 0.02s linear;
        `;
        arrow.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"
                 viewBox="0 0 32 32">
                <path d="M4 2 L4 26 L11 19 L16 30 L21 28 L16 17 L25 17 Z"
                      fill="white" stroke="black" stroke-width="2"
                      stroke-linejoin="round"/>
            </svg>
        `;
        wrap.appendChild(halo);
        wrap.appendChild(arrow);
        document.body.appendChild(wrap);
        window.__mouse = { x: 0, y: 0 };
        document.addEventListener('mousemove', (e) => {
            window.__mouse.x = e.clientX;
            window.__mouse.y = e.clientY;
            halo.style.left = e.clientX + 'px';
            halo.style.top  = e.clientY + 'px';
            arrow.style.left = e.clientX + 'px';
            arrow.style.top  = e.clientY + 'px';
        }, true);
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
"""

def _setup_context(browser, video_dir):
    context = browser.new_context(
        record_video_dir=video_dir,
        record_video_size={"width": 1280, "height": 720},
        viewport={"width": 1280, "height": 720},
    )
    context.add_init_script(CURSOR_SCRIPT)
    return context

def _smooth_move(page, x, y, steps=40, delay_ms=12):
    cur = page.evaluate("() => window.__mouse || {x:0, y:0}")
    sx, sy = cur["x"], cur["y"]
    for i in range(1, steps + 1):
        t = i / steps
        t = t * t * (3 - 2 * t)
        mx = sx + (x - sx) * t
        my = sy + (y - sy) * t
        page.mouse.move(mx, my)
        time.sleep(delay_ms / 1000)

def _click_with_ripple(page, x, y):
    page.evaluate(
        """({x, y}) => {
            const r = document.createElement('div');
            r.style.cssText = `
                position: fixed;
                left: ${x}px; top: ${y}px;
                width: 4px; height: 4px;
                margin-left: -2px; margin-top: -2px;
                border-radius: 50%;
                border: 2px solid rgba(255, 200, 0, 0.9);
                pointer-events: none;
                z-index: 2147483646;
                transition: all 0.6s ease-out;
            `;
            document.body.appendChild(r);
            requestAnimationFrame(() => {
                r.style.width = '64px';
                r.style.height = '64px';
                r.style.marginLeft = '-32px';
                r.style.marginTop = '-32px';
                r.style.opacity = '0';
            });
            setTimeout(() => r.remove(), 700);
        }""",
        {"x": x, "y": y},
    )
    page.mouse.click(x, y)

def ShowCallout(page, text, bgColor="yellow", textColor="black", fade=True):
    page.evaluate(
        """({text, bgColor, textColor, fade}) => {
            const c = document.createElement('div');
            c.textContent = text;
            c.style.cssText = `
                position: fixed;
                left: 40px; top: 40px;
                padding: 12px 20px;
                background: ${bgColor};
                color: ${textColor};
                font: 16pt sans-serif;
                border: 2px solid black;
                border-radius: 6px;
                pointer-events: none;
                z-index: 2147483646;
                opacity: ${fade ? 0 : 1};
                transition: opacity 2s ease;
            `;
            document.body.appendChild(c);
            if (fade) {
                requestAnimationFrame(() => (c.style.opacity = '1'));
                setTimeout(() => (c.style.opacity = '0'), 2500);
                setTimeout(() => c.remove(), 5000);
            } else {
                setTimeout(() => c.remove(), 4000);
            }
        }""",
        {"text": text, "bgColor": bgColor,
         "textColor": textColor, "fade": fade},
    )

def _type_humanlike(page, text):
    for ch in text:
        page.keyboard.type(ch)
        time.sleep(random.uniform(0.04, 0.14))

def CaptureVideo_Magento(
    url,
    company_name,
    language,
    country,
    postcode,
    city,
    street,
    house_no,
):
    os.makedirs(PATH_TO_VIDEO_FOLDER, exist_ok=True)
    safe_company = _safe_name(company_name)
    video_path_final = os.path.abspath(
        os.path.join(PATH_TO_VIDEO_FOLDER, f"{safe_company}.webm")
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = _setup_context(browser, PATH_TO_VIDEO_FOLDER)
            page = context.new_page()

            page.goto("https://html.duckduckgo.com/html/", wait_until="domcontentloaded")
            time.sleep(2.0)
            
            body_text = page.inner_text("body").lower()
            if "error" in body_text or "support email" in body_text or "captcha" in body_text or "unfortunately" in body_text:
                print(f"[{company_name}] ERROR: DuckDuckGo blocked the request.")
                context.close()
                browser.close()
                return None 

            ShowCallout(page, f"Searching for Magento in {city}", "yellow", "black")

            search_box = page.locator('input[name="q"]')
            search_box.wait_for(state="visible", timeout=15000)
            box = search_box.bounding_box()
            
            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2

            _smooth_move(page, target_x, target_y)
            _click_with_ripple(page, target_x, target_y)

            query = f"Magento developer in {city}"
            _type_humanlike(page, query)
            time.sleep(0.4)

            btn = page.locator('input[type="submit"]').first
            btn.wait_for(state="visible", timeout=5000)
            btn_box = btn.bounding_box()
            
            bx = btn_box["x"] + btn_box["width"] / 2
            by = btn_box["y"] + btn_box["height"] / 2
            
            _smooth_move(page, bx, by)
            _click_with_ripple(page, bx, by)

            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass

            first_result = page.locator('a.result__a').first
            first_result.wait_for(state="visible", timeout=20000)

            res_box = first_result.bounding_box()
            rx = res_box["x"] + res_box["width"] / 2
            ry = res_box["y"] + res_box["height"] / 2

            page.mouse.move(10, 10)
            time.sleep(0.2)
            _smooth_move(page, rx, ry)
            _click_with_ripple(page, rx, ry)

            time.sleep(1.5)

            video = page.video
            context.close()
            browser.close()

            if video is None:
                return None

            temp_path = video.path()
            for _ in range(50):
                if os.path.exists(temp_path):
                    break
                time.sleep(0.1)

            if os.path.exists(video_path_final):
                os.remove(video_path_final)
            shutil.move(temp_path, video_path_final)
            return video_path_final

    except Exception as e:
        print(f"[CaptureVideo_Magento] Error for '{company_name}': {e}")
        return None