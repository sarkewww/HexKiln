# HexKiln Calculate Tool
# Byte-level hex operations: XOR, ADD, SUB
# Endian swap (LE ↔ BE)
# Adaptive output layout: landscape ↔ portrait
# i18n: English / 简体中文 (auto-detect + toggle)
# External lang overrides: place lang/en.json or lang/zh_CN.json next to this file
# Requires: Python 3.10+ — stdlib only (tkinter built-in)

import tkinter as tk
import sys
import locale
import json
from pathlib import Path

# Color palette
C: dict[str, str] = {
    "bg":        "#0d0f14",
    "panel":     "#13161e",
    "border":    "#1e2433",
    "input_bg":  "#0a0c11",
    "accent":    "#00d4aa",
    "accent2":   "#e84393",
    "text":      "#c8d8f0",
    "dim":       "#4a5568",
    "good":      "#39d353",
    "bad":       "#ff5370",
    "hex_out":   "#00d4aa",
    "dec_out":   "#ffa040",
    "asc_out":   "#a78bfa",
    "btn_bg":    "#1a2030",
    "btn_hover": "#252d3d",
    "sel_bg":    "#1e3a5f",
}

MONO     = ("Consolas", 11)
MONO_LG  = ("Consolas", 13)
LBL_FONT = ("Consolas", 9)

# i18n strings
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "win_title":      "HexKiln Calculate Tool",
        "app_title":      "⬡ HexKiln",
        "app_subtitle":   "  Binary Toolkit",
        "py_ver":         "Python 3.10",

        "hex_input":      "HEX INPUT",
        "placeholder":    "e.g. AA 22 0x33 445566",

        "key":            "KEY",
        "key_sub":        "(hex / dec)",
        "key_hint":       "← key for XOR / ADD / SUB",

        "op_label":       "OPERATION",

        "mode_label":     "MODE",
        "mode_bytewise":  "Byte-by-byte",
        "mode_direct":    "Direct (whole)",

        "btn_calc":       "▶  CALCULATE",
        "btn_endian":     "⇄  ENDIAN SWAP",
        "btn_clear":      "✕  CLEAR",

        "out_hex":        "HEX",
        "out_dec":        "DEC",
        "out_ascii":      "ASCII",

        "copy":           "copy ⧉",

        "status_ready":   "Ready.",
        "status_hint":    "results shown as HEX · DEC · ASCII  ·  '·' = non-printable",

        "err_hex":        "⚠  Invalid hex input.",
        "err_key":        "⚠  Invalid key value.",
        "err_swap":       "⚠  Invalid hex input for endian swap.",
        "err_generic":    "⚠  Error: {}",

        "status_calc":    "✓  {} ({}) · key=0x{} · {} byte(s) processed.",
        "mode_bw_name":   "byte-by-byte",
        "mode_dr_name":   "direct",

        "status_endian":  "⇄  Endian swapped · {} byte(s): LE→BE / BE→LE",
        "status_cleared": "Cleared.",
        "status_copied":  "✓  {} output copied to clipboard.",

        "dec_combined":   "── combined (BE int): {}",
        "asc_printable":  "── printable: {}/{} bytes",

        "lang_btn":       "中文",
    },

    "zh_CN": {
        "win_title":      "HexKiln 计算工具",
        "app_title":      "⬡ HexKiln",
        "app_subtitle":   "  二进制工具集",
        "py_ver":         "Python 3.10",

        "hex_input":      "十六进制输入",
        "placeholder":    "示例：AA 22 0x33 445566",

        "key":            "密钥",
        "key_sub":        "（十六 / 十进制）",
        "key_hint":       "← XOR / ADD / SUB 运算密钥",

        "op_label":       "运算",

        "mode_label":     "模式",
        "mode_bytewise":  "逐字节",
        "mode_direct":    "整体运算",

        "btn_calc":       "▶  计算",
        "btn_endian":     "⇄  字节序转换",
        "btn_clear":      "✕  清空",

        "out_hex":        "HEX",
        "out_dec":        "DEC",
        "out_ascii":      "ASCII",

        "copy":           "复制 ⧉",

        "status_ready":   "就绪。",
        "status_hint":    "结果以 HEX · DEC · ASCII 显示  ·  '·' = 不可打印字符",

        "err_hex":        "⚠  无效的十六进制输入。",
        "err_key":        "⚠  无效的密钥值。",
        "err_swap":       "⚠  字节序转换：无效的十六进制输入。",
        "err_generic":    "⚠  错误：{}",

        "status_calc":    "✓  {} ({}) · 密钥=0x{} · 已处理 {} 字节。",
        "mode_bw_name":   "逐字节",
        "mode_dr_name":   "整体",

        "status_endian":  "⇄  字节序已转换 · {} 字节：LE→BE / BE→LE",
        "status_cleared": "已清空。",
        "status_copied":  "✓  {} 输出已复制到剪贴板。",

        "dec_combined":   "── 合并值（大端整数）：{}",
        "asc_printable":  "── 可打印：{}/{} 字节",

        "lang_btn":       "English",
    },
}

# Load external lang overrides from ./lang/<code>.json
_LANG_DIR = Path(__file__).parent / "lang"
for _code in list(_STRINGS):
    _p = _LANG_DIR / f"{_code}.json"
    if _p.exists():
        try:
            with open(_p, encoding="utf-8") as _f:
                _ext = json.load(_f)
                _ext.pop("_comment", None)
                _STRINGS[_code].update(_ext)
        except Exception:
            pass


def _detect_lang() -> str:
    # Return 'zh_CN' when OS locale is Chinese, else 'en'
    try:
        code, _ = locale.getdefaultlocale()
        if code and code.lower().startswith("zh"):
            return "zh_CN"
    except Exception:
        pass
    return "en"


# Core logic

def parse_hex(s: str) -> list[int] | None:
    # Parse hex string to byte list. Accepts spaces, commas, 0x prefix.
    s = s.replace(" ", "").replace(",", "").replace("0x", "").replace("0X", "")
    if not s:
        return None
    if len(s) % 2 != 0:
        s = "0" + s
    try:
        return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]
    except ValueError:
        return None


def parse_key(s: str) -> int | None:
    # Parse key string to integer (hex or decimal)
    s = s.strip()
    if not s:
        return None
    try:
        return int(s, 16) if s.startswith(("0x", "0X")) else int(s, 16)
    except ValueError:
        try:
            return int(s, 10)
        except ValueError:
            return None


def endian_swap(data: list[int]) -> list[int]:
    # Reverse byte order (LE↔BE)
    return list(reversed(data))


def op_bytewise(data: list[int], key: int, operation: str) -> list[int]:
    # Apply operation byte-by-byte with key masked to 0xFF
    k = key & 0xFF
    result: list[int] = []
    for b in data:
        match operation:
            case "XOR": result.append(b ^ k)
            case "ADD": result.append((b + k) & 0xFF)
            case "SUB": result.append((b - k) & 0xFF)
    return result


def op_direct(data: list[int], key: int, operation: str) -> list[int]:
    # Apply operation on the whole integer value
    length  = len(data)
    val     = int.from_bytes(bytes(data), "big")
    max_val = (1 << (length * 8)) - 1
    match operation:
        case "XOR": val = val ^ key
        case "ADD": val = (val + key) & max_val
        case "SUB": val = (val - key) & max_val
    return list(val.to_bytes(length, "big"))


def bytes_to_hex(data: list[int]) -> str:
    # Format bytes as hex string
    return " ".join(f"{b:02X}" for b in data)


def bytes_to_dec(data: list[int], combined_fmt: str) -> str:
    # Format bytes as decimal with combined BE int
    per_byte = " ".join(str(b) for b in data)
    combined = int.from_bytes(bytes(data), "big")
    return f"{per_byte}\n{combined_fmt.format(combined)}"


def bytes_to_ascii(data: list[int], printable_fmt: str) -> str:
    # Format bytes as ASCII with non-printable shown as '·'
    chars     = "".join(chr(b) if 32 <= b < 127 else "·" for b in data)
    printable = sum(1 for b in data if 32 <= b < 127)
    return f"{chars}\n{printable_fmt.format(printable, len(data))}"


# UI helpers

class HoverButton(tk.Label):
    # Flat clickable label with hover highlight

    def __init__(self, parent, text, command,
                 bg_normal=C["btn_bg"], bg_hover=C["btn_hover"],
                 fg=C["text"], **kw):
        resolved_font = kw.pop("font", LBL_FONT)
        super().__init__(parent, text=text, bg=bg_normal, fg=fg,
                         cursor="hand2", padx=14, pady=6,
                         font=resolved_font, **kw)
        self._cmd = command
        self._n, self._h = bg_normal, bg_hover
        self.bind("<Enter>",    lambda _: self.config(bg=self._h))
        self.bind("<Leave>",    lambda _: self.config(bg=self._n))
        self.bind("<Button-1>", lambda _: self._cmd())


def hsep(parent: tk.Widget, colour: str = C["border"]) -> tk.Frame:
    # Create horizontal separator line
    f = tk.Frame(parent, bg=colour, height=1)
    f.pack(fill="x")
    return f


# Main application

class HexForgeTool(tk.Tk):

    def __init__(self):
        super().__init__()

        # i18n
        self._lang: str = _detect_lang()
        self._i18n_refs: list[tuple[tk.Widget, str, str]] = []

        # Operation / mode state
        self._op_var   = tk.StringVar(value="XOR")
        self._mode_var = tk.StringVar(value="bytewise")

        # Adaptive layout state
        self._layout_mode: str       = ""
        self._out_frame:   tk.Frame | None = None
        self._out_panels:  list[tk.Frame]  = []
        self._resize_job:  str | None      = None

        # Last computed bytes (re-render on lang switch)
        self._last_result: list[int] | None = None

        # Status colour
        self._status_colour: str = C["dim"]

        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.minsize(600, 520)

        self._build_ui()
        self._center_window(920, 740)
        self.bind("<Configure>", self._on_resize_debounced)

    # Translation helpers

    def T(self, key: str, *args) -> str:
        # Get translated string for current language
        s = _STRINGS.get(self._lang, _STRINGS["en"]).get(key, key)
        return s.format(*args) if args else s

    def _reg(self, widget: tk.Widget, key: str, kwarg: str = "text") -> tk.Widget:
        # Register widget for language refresh
        self._i18n_refs.append((widget, key, kwarg))
        return widget

    def _switch_lang(self):
        # Toggle between English and Chinese
        self._lang = "zh_CN" if self._lang == "en" else "en"
        self._apply_lang()

    def _apply_lang(self):
        # Apply current language to all registered widgets
        self.title(self.T("win_title"))

        for widget, key, kwarg in self._i18n_refs:
            try:
                widget.config(**{kwarg: self.T(key)})
            except tk.TclError:
                pass

        # Update placeholder
        if hasattr(self, "hex_input"):
            old_ph = getattr(self.hex_input, "_placeholder_text", "")
            cur    = self.hex_input.get("1.0", "end-1c")
            new_ph = self.T("placeholder")
            self.hex_input._placeholder_text = new_ph
            if cur in ("", old_ph):
                self.hex_input.config(fg=C["dim"])
                self.hex_input.delete("1.0", "end")
                self.hex_input.insert("1.0", new_ph)

        # Restore status colour
        if hasattr(self, "_status_lbl"):
            self._status_lbl.config(fg=self._status_colour)

        # Re-render outputs with new format strings
        if self._last_result is not None:
            self._render_outputs(self._last_result)

    # Adaptive layout

    def _center_window(self, w: int, h: int):
        # Center window on screen
        sx, sy = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sx - w) // 2}+{(sy - h) // 2}")

    def _on_resize_debounced(self, event: tk.Event):
        # Debounced resize handler for layout switching
        if event.widget is not self:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(
            80, lambda: self._check_layout(event.width, event.height)
        )

    def _check_layout(self, w: int, h: int):
        # Switch layout mode based on aspect ratio
        new_mode = "landscape" if w >= h else "portrait"
        if new_mode != self._layout_mode:
            self._layout_mode = new_mode
            self._relayout_outputs()

    def _relayout_outputs(self):
        # Re-arrange output panels in grid layout
        if not self._out_panels:
            return

        for panel in self._out_panels:
            panel.pack_forget()
            panel.grid_forget()

        # Configure grid: 3 equal rows
        for i in range(3):
            self._out_frame.grid_rowconfigure(i, weight=1, uniform="out")
        self._out_frame.grid_columnconfigure(0, weight=1)

        for i, panel in enumerate(self._out_panels):
            panel.grid(row=i, column=0, sticky="nsew",
                       pady=(0 if i == 0 else 3, 0 if i == 2 else 3))

    # UI construction

    def _build_ui(self):
        # Build the complete UI
        self._build_titlebar()
        hsep(self)
        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        self._build_input_section(content)
        self._build_controls(content)
        self._build_output_section(content)
        self._build_status_bar()
        self.title(self.T("win_title"))

    def _build_titlebar(self):
        # Build title bar with app title and language toggle
        bar = tk.Frame(self, bg=C["bg"], pady=10)
        bar.pack(fill="x", padx=20)

        lft = tk.Frame(bar, bg=C["bg"])
        lft.pack(side="left")
        self._reg(
            tk.Label(lft, text=self.T("app_title"), fg=C["accent"],
                     bg=C["bg"], font=("Consolas", 18, "bold")),
            "app_title",
        ).pack(side="left")
        self._reg(
            tk.Label(lft, text=self.T("app_subtitle"), fg=C["dim"],
                     bg=C["bg"], font=("Consolas", 11)),
            "app_subtitle",
        ).pack(side="left", padx=(2, 0))

        rgt = tk.Frame(bar, bg=C["bg"])
        rgt.pack(side="right")

        self._reg(
            tk.Label(rgt, text=self.T("py_ver"), fg=C["dim"],
                     bg=C["bg"], font=LBL_FONT),
            "py_ver",
        ).pack(side="right", padx=(12, 0))

        # Language toggle button
        self._lang_btn = HoverButton(
            rgt, text=self.T("lang_btn"),
            command=self._switch_lang,
            bg_normal="#1a2236", bg_hover="#252f45",
            fg=C["accent2"],
            font=("Consolas", 9, "bold"),
        )
        self._lang_btn.pack(side="right")
        self._reg(self._lang_btn, "lang_btn")

    def _build_input_section(self, parent: tk.Frame):
        # Build hex input and key input area
        frame = tk.Frame(parent, bg=C["panel"],
                         highlightbackground=C["border"],
                         highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10))

        # Hex input
        row1 = tk.Frame(frame, bg=C["panel"])
        row1.pack(fill="x", padx=14, pady=(12, 4))

        self._reg(
            tk.Label(row1, text=self.T("hex_input"), fg=C["accent"],
                     bg=C["panel"], font=("Consolas", 9, "bold")),
            "hex_input",
        ).pack(anchor="w")

        self.hex_input = tk.Text(
            row1, height=3, bg=C["input_bg"], fg=C["text"],
            insertbackground=C["accent"], font=MONO_LG,
            relief="flat", pady=6, padx=8,
            selectbackground=C["sel_bg"],
        )
        self.hex_input.pack(fill="x", pady=(4, 0))
        self._setup_placeholder(self.hex_input, self.T("placeholder"))

        # Key input
        row2 = tk.Frame(frame, bg=C["panel"])
        row2.pack(fill="x", padx=14, pady=(8, 12))

        key_meta = tk.Frame(row2, bg=C["panel"])
        key_meta.pack(side="left", anchor="n", padx=(0, 10))
        self._reg(
            tk.Label(key_meta, text=self.T("key"), fg=C["accent2"],
                     bg=C["panel"], font=("Consolas", 9, "bold")),
            "key",
        ).pack(anchor="w")
        self._reg(
            tk.Label(key_meta, text=self.T("key_sub"), fg=C["dim"],
                     bg=C["panel"], font=("Consolas", 8)),
            "key_sub",
        ).pack(anchor="w")

        self.key_input = tk.Entry(
            row2, bg=C["input_bg"], fg=C["text"],
            insertbackground=C["accent2"], font=MONO_LG,
            relief="flat", width=20, selectbackground=C["sel_bg"],
        )
        self.key_input.pack(side="left", ipady=5, ipadx=6)
        self.key_input.insert(0, "0xFF")

        self._reg(
            tk.Label(row2, text=self.T("key_hint"), fg=C["dim"],
                     bg=C["panel"], font=LBL_FONT),
            "key_hint",
        ).pack(side="left", padx=(8, 0))

    def _build_controls(self, parent: tk.Frame):
        # Build operation, mode selection and action buttons
        ctrl = tk.Frame(parent, bg=C["bg"])
        ctrl.pack(fill="x", pady=(0, 10))

        # Operation radio group
        op_lf = tk.LabelFrame(ctrl, fg=C["dim"], bg=C["bg"],
                               font=LBL_FONT, bd=1, relief="flat")
        op_lf.pack(side="left", padx=(0, 10))
        self._reg(op_lf, "op_label", "text")

        for op, fg_col in [("XOR", C["accent"]), ("ADD", C["good"]), ("SUB", C["bad"])]:
            tk.Radiobutton(
                op_lf, text=op, variable=self._op_var, value=op,
                bg=C["bg"], fg=fg_col, selectcolor=C["input_bg"],
                activebackground=C["bg"],
                font=("Consolas", 10, "bold"), pady=4, padx=8,
            ).pack(side="left")

        # Mode radio group
        mode_lf = tk.LabelFrame(ctrl, fg=C["dim"], bg=C["bg"],
                                  font=LBL_FONT, bd=1, relief="flat")
        mode_lf.pack(side="left", padx=(0, 10))
        self._reg(mode_lf, "mode_label", "text")

        self._rb_bytewise = tk.Radiobutton(
            mode_lf, text=self.T("mode_bytewise"),
            variable=self._mode_var, value="bytewise",
            bg=C["bg"], fg=C["text"], selectcolor=C["input_bg"],
            activebackground=C["bg"], font=MONO, pady=4, padx=8,
        )
        self._rb_bytewise.pack(side="left")
        self._reg(self._rb_bytewise, "mode_bytewise")

        self._rb_direct = tk.Radiobutton(
            mode_lf, text=self.T("mode_direct"),
            variable=self._mode_var, value="direct",
            bg=C["bg"], fg=C["text"], selectcolor=C["input_bg"],
            activebackground=C["bg"], font=MONO, pady=4, padx=8,
        )
        self._rb_direct.pack(side="left")
        self._reg(self._rb_direct, "mode_direct")

        # Action buttons
        btn_f = tk.Frame(ctrl, bg=C["bg"])
        btn_f.pack(side="left", padx=(4, 0))

        self._btn_calc = HoverButton(
            btn_f, text=self.T("btn_calc"), command=self._calculate,
            bg_normal="#0d2a1f", bg_hover="#113d2c", fg=C["good"],
            font=("Consolas", 10, "bold"),
        )
        self._btn_calc.pack(side="left", padx=(0, 6))
        self._reg(self._btn_calc, "btn_calc")

        self._btn_endian = HoverButton(
            btn_f, text=self.T("btn_endian"), command=self._endian_swap,
            bg_normal="#1e1030", bg_hover="#2d1a47", fg=C["accent2"],
            font=("Consolas", 10, "bold"),
        )
        self._btn_endian.pack(side="left", padx=(0, 6))
        self._reg(self._btn_endian, "btn_endian")

        self._btn_clear = HoverButton(
            btn_f, text=self.T("btn_clear"), command=self._clear,
            bg_normal=C["btn_bg"], bg_hover=C["btn_hover"], fg=C["dim"],
            font=("Consolas", 10),
        )
        self._btn_clear.pack(side="left")
        self._reg(self._btn_clear, "btn_clear")

    def _build_output_section(self, parent: tk.Frame):
        # Build output panels (HEX, DEC, ASCII)
        self._out_frame = tk.Frame(parent, bg=C["bg"])
        self._out_frame.pack(fill="both", expand=True, pady=(0, 10))

        panels_def = [
            ("out_hex",   C["hex_out"], "hex_out"),
            ("out_dec",   C["dec_out"], "dec_out"),
            ("out_ascii", C["asc_out"], "asc_out"),
        ]

        self._out_panels = []

        for label_key, colour, attr in panels_def:
            col = tk.Frame(
                self._out_frame, bg=C["panel"],
                highlightbackground=colour, highlightthickness=1,
            )
            self._out_panels.append(col)

            # Coloured header
            hdr = tk.Frame(col, bg=colour)
            hdr.pack(fill="x")

            title_lbl = tk.Label(
                hdr, text=self.T(label_key),
                fg=C["bg"], bg=colour,
                font=("Consolas", 10, "bold"), pady=5, padx=6,
            )
            title_lbl.pack(side="left")
            self._reg(title_lbl, label_key)

            copy_lbl = tk.Label(
                hdr, text=self.T("copy"),
                fg=C["bg"], bg=colour,
                font=("Consolas", 8), cursor="hand2", padx=8,
            )
            copy_lbl.pack(side="right")
            copy_lbl.bind("<Button-1>", lambda e, a=attr: self._copy(a))
            self._reg(copy_lbl, "copy")

            # Scrollable text output
            txt = tk.Text(
                col, bg=C["input_bg"], fg=colour,
                font=MONO_LG, relief="flat",
                pady=8, padx=8, wrap="word",
                selectbackground=C["sel_bg"],
                state="disabled",
            )
            txt.pack(fill="both", expand=True, padx=6, pady=6)
            setattr(self, attr, txt)

        self._relayout_outputs()

    def _build_status_bar(self):
        # Build status bar at bottom
        hsep(self)
        row = tk.Frame(self, bg=C["bg"], pady=4)
        row.pack(fill="x", padx=20)

        self.status_var = tk.StringVar(value=self.T("status_ready"))
        self._status_lbl = tk.Label(
            row, textvariable=self.status_var,
            fg=C["dim"], bg=C["bg"], font=LBL_FONT, anchor="w",
        )
        self._status_lbl.pack(side="left")

        self._hint_lbl = tk.Label(
            row, text=self.T("status_hint"),
            fg=C["dim"], bg=C["bg"], font=LBL_FONT,
        )
        self._hint_lbl.pack(side="right")
        self._reg(self._hint_lbl, "status_hint")

    # Placeholder

    def _setup_placeholder(self, widget: tk.Text, text: str):
        # Setup placeholder text behavior
        widget._placeholder_text = text
        widget.insert("1.0", text)
        widget.config(fg=C["dim"])

        def on_in(_):
            if widget.get("1.0", "end-1c") == widget._placeholder_text:
                widget.delete("1.0", "end")
                widget.config(fg=C["text"])

        def on_out(_):
            if not widget.get("1.0", "end-1c").strip():
                widget.config(fg=C["dim"])
                widget.delete("1.0", "end")
                widget.insert("1.0", widget._placeholder_text)

        widget.bind("<FocusIn>",  on_in)
        widget.bind("<FocusOut>", on_out)

    def _get_hex_input(self) -> str:
        # Get actual hex input, ignoring placeholder text
        raw = self.hex_input.get("1.0", "end-1c")
        ph  = getattr(self.hex_input, "_placeholder_text", "")
        return "" if raw == ph else raw

    # Output rendering

    def _set_output(self, widget: tk.Text, text: str):
        # Set text in disabled output widget
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _render_outputs(self, result: list[int]):
        # Render bytes to all three output panels
        self._set_output(self.hex_out, bytes_to_hex(result))
        self._set_output(self.dec_out,
                         bytes_to_dec(result, self.T("dec_combined")))
        self._set_output(self.asc_out,
                         bytes_to_ascii(result, self.T("asc_printable")))

    # Status helper

    def _status(self, msg: str, colour: str = C["dim"]):
        # Update status bar message and colour
        self._status_colour = colour
        self.status_var.set(msg)
        self._status_lbl.config(fg=colour)

    # Actions

    def _calculate(self):
        # Perform hex calculation
        data = parse_hex(self._get_hex_input())
        if data is None:
            self._status(self.T("err_hex"), C["bad"])
            return

        key = parse_key(self.key_input.get())
        if key is None:
            self._status(self.T("err_key"), C["bad"])
            return

        op   = self._op_var.get()
        mode = self._mode_var.get()

        try:
            result = (op_bytewise(data, key, op) if mode == "bytewise"
                      else op_direct(data, key, op))
        except Exception as exc:
            self._status(self.T("err_generic", exc), C["bad"])
            return

        self._last_result = result
        self._render_outputs(result)

        mode_name = (self.T("mode_bw_name") if mode == "bytewise"
                     else self.T("mode_dr_name"))
        self._status(
            self.T("status_calc", op, mode_name, f"{key:X}", len(data)),
            C["good"],
        )

    def _endian_swap(self):
        # Perform endian swap on hex input
        data = parse_hex(self._get_hex_input())
        if data is None:
            self._status(self.T("err_swap"), C["bad"])
            return

        swapped = endian_swap(data)
        self._last_result = swapped

        self.hex_input.config(fg=C["text"])
        self.hex_input.delete("1.0", "end")
        self.hex_input.insert("1.0", bytes_to_hex(swapped))

        self._render_outputs(swapped)
        self._status(self.T("status_endian", len(data)), C["accent2"])

    def _clear(self):
        # Clear all inputs and outputs
        self._last_result = None

        ph = self.T("placeholder")
        self.hex_input._placeholder_text = ph

        self.hex_input.config(fg=C["dim"])
        self.hex_input.delete("1.0", "end")
        self.hex_input.insert("1.0", ph)

        self.hex_input.focus_set()
        self.hex_input.tag_add("sel", "1.0", "end-1c")
        self.hex_input.mark_set("insert", "1.0")

        self.key_input.delete(0, "end")
        self.key_input.insert(0, "0xFF")

        for attr in ("hex_out", "dec_out", "asc_out"):
            self._set_output(getattr(self, attr), "")

        self._status(self.T("status_cleared"), C["dim"])

    def _copy(self, attr: str):
        # Copy output panel content to clipboard
        text = getattr(self, attr).get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        label = attr.replace("_out", "").upper()
        self._status(self.T("status_copied", label), C["accent"])


# Entry point

if __name__ == "__main__":
    if sys.version_info < (3, 10):
        sys.exit("HexForge requires Python 3.10 or newer.")
    app = HexForgeTool()
    app.mainloop()