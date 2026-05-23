# HexKiln ZCalculate Tool
# Byte-level hex operations: XOR, ADD, SUB
# Endian swap (LE ↔ BE)
# Adaptive output layout: landscape ↔ portrait
# i18n: English / 简体中文 (auto-detect + toggle)
# External lang overrides: place lang/en.json or lang/zh_CN.json next to this file
# Requires: Python 3.10+ — stdlib + customtkinter

import json
import locale
import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

# ==================== Appearance ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Color palette
C: dict[str, str] = {
    "bg": "#0d0f14",
    "panel": "#13161e",
    "border": "#1e2433",
    "input_bg": "#0a0c11",
    "accent": "#00d4aa",
    "accent2": "#e84393",
    "text": "#c8d8f0",
    "dim": "#4a5568",
    "good": "#39d353",
    "bad": "#ff5370",
    "hex_out": "#00d4aa",
    "dec_out": "#ffa040",
    "asc_out": "#a78bfa",
    "btn_bg": "#1a2030",
    "btn_hover": "#252d3d",
    # "sel_bg": "#1e3a5f",
}

MONO = ("Consolas", 11)
MONO_LG = ("Consolas", 13)
LBL_FONT = ("Consolas", 9)

# i18n strings
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "win_title": "HexKiln Calculate Tool",
        "app_title": "HexKiln",
        "app_subtitle": "  Binary Toolkit",
        "py_ver": "Python 3.10",

        "hex_input": "HEX INPUT",
        "placeholder": "e.g. AA 22 0x33 445566",

        "key": "KEY",
        "key_sub": "(hex / dec)",
        "key_hint": "← key for XOR / ADD / SUB",

        "op_label": "OPERATION",

        "mode_label": "MODE",
        "mode_bytewise": "Byte-by-byte",
        "mode_direct": "Direct (whole)",

        "op_xor": "XOR",
        "op_add": "ADD",
        "op_sub": "SUB",

        "btn_calc": "▶  CALCULATE",
        "btn_endian": "⇄  ENDIAN SWAP",
        "btn_clear": "✕  CLEAR",

        "out_hex": "HEX",
        "out_dec": "DEC",
        "out_ascii": "ASCII",

        "copy": "copy ⧉",

        "status_ready": "Ready.",
        "status_hint": "results shown as HEX · DEC · ASCII  ·  '·' = non-printable",

        "err_hex": "⚠  Invalid hex input.",
        "err_key": "⚠  Invalid key value.",
        "err_swap": "⚠  Invalid hex input for endian swap.",
        "err_generic": "⚠  Error: {}",

        "status_calc": "✓  {} ({}) · key=0x{} · {} byte(s) processed.",
        "mode_bw_name": "byte-by-byte",
        "mode_dr_name": "direct",

        "status_endian": "⇄  Endian swapped · {} byte(s): LE→BE / BE→LE",
        "status_cleared": "Cleared.",
        "status_copied": "✓  {} output copied to clipboard.",

        "dec_combined": "── combined (BE int): {}",
        "asc_printable": "── printable: {}/{} bytes",

        "lang_btn": "中文",
    },

    "zh_CN": {
        "win_title": "HexKiln 计算工具",
        "app_title": "HexKiln",
        "app_subtitle": "  二进制工具集",
        "py_ver": "Python 3.10",

        "hex_input": "十六进制输入",
        "placeholder": "示例：AA 22 0x33 445566",

        "key": "密钥",
        "key_sub": "（十六 / 十进制）",
        "key_hint": "← XOR / ADD / SUB 运算密钥",

        "op_label": "运算",

        "mode_label": "模式",
        "mode_bytewise": "逐字节",
        "mode_direct": "整体运算",

        "op_xor": "异或",
        "op_add": "加法",
        "op_sub": "减法",

        "btn_calc": "▶  计算",
        "btn_endian": "⇄  字节序转换",
        "btn_clear": "✕  清空",

        "out_hex": "HEX",
        "out_dec": "DEC",
        "out_ascii": "ASCII",

        "copy": "复制 ⧉",

        "status_ready": "就绪。",
        "status_hint": "结果以 HEX · DEC · ASCII 显示  ·  '·' = 不可打印字符",

        "err_hex": "⚠  无效的十六进制输入。",
        "err_key": "⚠  无效的密钥值。",
        "err_swap": "⚠  字节序转换：无效的十六进制输入。",
        "err_generic": "⚠  错误：{}",

        "status_calc": "✓  {} ({}) · 密钥=0x{} · 已处理 {} 字节。",
        "mode_bw_name": "逐字节",
        "mode_dr_name": "整体",

        "status_endian": "⇄  字节序已转换 · {} 字节：LE→BE / BE→LE",
        "status_cleared": "已清空。",
        "status_copied": "✓  {} 输出已复制到剪贴板。",

        "dec_combined": "── 合并值（大端整数）：{}",
        "asc_printable": "── 可打印：{}/{} 字节",

        "lang_btn": "English",
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
    try:
        code, _ = locale.getdefaultlocale()
        if code and code.lower().startswith("zh"):
            return "zh_CN"
    except Exception:
        pass
    return "en"


# ==================== Core logic ====================

def parse_hex(s: str) -> list[int] | None:
    s = s.replace(" ", "").replace(",", "").replace("0x", "").replace("0X", "")

    if not s:
        return None

    if len(s) % 2:
        s = "0" + s

    try:
        return list(bytes.fromhex(s))
    except ValueError:
        return None


def parse_key(s: str) -> int | None:
    s = s.strip()
    if not s:
        return None
    try:
        return int(s, 16)
    except ValueError:
        try:
            return int(s, 10)
        except ValueError:
            return None


def endian_swap(data: list[int]) -> list[int]:
    return data[::-1]


def op_bytewise(data: list[int], key: int, operation: str) -> list[int]:
    k = key & 0xFF
    result: list[int] = []
    for b in data:
        match operation:
            case "XOR":
                result.append(b ^ k)
            case "ADD":
                result.append((b + k) & 0xFF)
            case "SUB":
                result.append((b - k) & 0xFF)
    return result


def op_direct(data: list[int], key: int, operation: str) -> list[int]:
    length = len(data)
    val = int.from_bytes(bytes(data), "big")
    max_val = (1 << (length * 8)) - 1
    match operation:
        case "XOR":
            val = val ^ key
        case "ADD":
            val = (val + key) & max_val
        case "SUB":
            val = (val - key) & max_val
    return list(val.to_bytes(length, "big"))


def bytes_to_hex(data: list[int]) -> str:
    return " ".join(f"{b:02X}" for b in data)


def bytes_to_dec(data: list[int], combined_fmt: str) -> str:
    per_byte = " ".join(str(b) for b in data)
    combined = int.from_bytes(bytes(data), "big")
    return f"{per_byte}\n{combined_fmt.format(combined)}"


def bytes_to_ascii(data: list[int], printable_fmt: str) -> str:
    chars = "".join(chr(b) if 32 <= b < 127 else "·" for b in data)
    printable = sum(1 for b in data if 32 <= b < 127)
    return f"{chars}\n{printable_fmt.format(printable, len(data))}"


# ==================== UI helpers ====================

def hsep(parent: tk.Widget, colour: str = C["border"]) -> ctk.CTkFrame:
    f = ctk.CTkFrame(parent, fg_color=colour, corner_radius=0, height=1)
    f.pack(fill="x")
    return f


class HoverButton(ctk.CTkButton):
    def __init__(self, parent, text, command,
                 fg_color=C["btn_bg"], hover_color=C["btn_hover"],
                 text_color=C["text"], **kw):
        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=8,
            border_width=0,
            **kw,
        )


# ==================== Main application ====================

class HexForgeTool(ctk.CTk):

    def __init__(self):
        super().__init__()

        # i18n
        self._lang: str = _detect_lang()
        self._i18n_refs: list[tuple[tk.Widget, str, str]] = []

        # Operation / mode state
        self._op_var = tk.StringVar(value="XOR")
        self._mode_var = tk.StringVar(value="bytewise")

        # Adaptive layout state
        self._out_frame: ctk.CTkFrame | None = None
        self._out_panels: list[ctk.CTkFrame] = []

        # Last computed bytes (re-render on lang switch)
        self._last_result: list[int] | None = None

        # Status colour
        self._status_colour: str = C["dim"]

        self.configure(fg_color=C["bg"])
        self.title(self.T("win_title"))
        self.geometry("920x740")
        self.minsize(600, 520)

        self._build_ui()
        self._center_window(920, 740)

    # Translation helpers

    def T(self, key: str, *args) -> str:
        s = _STRINGS.get(self._lang, _STRINGS["en"]).get(key, key)
        return s.format(*args) if args else s

    def _reg(self, widget: tk.Widget, key: str, kwarg: str = "text") -> tk.Widget:
        self._i18n_refs.append((widget, key, kwarg))
        return widget

    def _switch_lang(self):
        self._lang = "zh_CN" if self._lang == "en" else "en"
        self._apply_lang()

    def _apply_lang(self):
        self.title(self.T("win_title"))

        for widget, key, kwarg in self._i18n_refs:
            try:
                widget.configure(**{kwarg: self.T(key)})
            except tk.TclError:
                pass

        if hasattr(self, "hex_input"):
            old_ph = getattr(self.hex_input, "_placeholder_text", "")
            cur = self.hex_input.get("1.0", "end-1c")
            new_ph = self.T("placeholder")
            self.hex_input._placeholder_text = new_ph
            if cur in ("", old_ph):
                self.hex_input.delete("1.0", "end")
                self.hex_input.insert("1.0", new_ph)
                self.hex_input.configure(text_color="#FFFFFF")

        if hasattr(self, "_status_lbl"):
            self._status_lbl.configure(text_color=self._status_colour)

        if self._last_result is not None:
            self._render_outputs(self._last_result)

    # Adaptive layout

    def _center_window(self, w: int, h: int):
        sx, sy = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sx - w) // 2}+{(sy - h) // 2}")

    def _relayout_outputs(self):
        if not self._out_panels or self._out_frame is None:
            return

        for i, panel in enumerate(self._out_panels):
            self._out_frame.grid_rowconfigure(i, weight=1)
            panel.grid(
                row=i,
                column=0,
                sticky="nsew",
                pady=3,
            )

        self._out_frame.grid_columnconfigure(0, weight=1)

    # UI construction

    def _build_ui(self):
        self._build_titlebar()
        hsep(self)
        content = ctk.CTkFrame(self, fg_color=C["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        self._build_input_section(content)
        self._build_controls(content)
        self._build_output_section(content)
        self._build_status_bar()
        self.title(self.T("win_title"))

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=C["bg"])
        bar.pack(fill="x", padx=20, pady=(10, 8))

        lft = ctk.CTkFrame(bar, fg_color=C["bg"])
        lft.pack(side="left")
        self._reg(
            ctk.CTkLabel(lft, text=self.T("app_title"), text_color=C["accent"], font=("Consolas", 18, "bold")),
            "app_title",
        ).pack(side="left")
        self._reg(
            ctk.CTkLabel(lft, text=self.T("app_subtitle"), text_color=C["dim"], font=("Consolas", 11)),
            "app_subtitle",
        ).pack(side="left", padx=(2, 0))

        rgt = ctk.CTkFrame(bar, fg_color=C["bg"])
        rgt.pack(side="right")

        self._reg(
            ctk.CTkLabel(rgt, text=self.T("py_ver"), text_color=C["dim"], font=LBL_FONT),
            "py_ver",
        ).pack(side="right", padx=(12, 0))

        self._lang_btn = HoverButton(
            rgt,
            text=self.T("lang_btn"),
            command=self._switch_lang,
            fg_color="#1a2236",
            hover_color="#252f45",
            text_color=C["accent2"],
            font=("Consolas", 9, "bold"),
            width=84,
            height=30,
        )
        self._lang_btn.pack(side="right")
        self._reg(self._lang_btn, "lang_btn")

    def _build_input_section(self, parent: tk.Frame):
        frame = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=12, border_width=1, border_color=C["border"])
        frame.pack(fill="x", pady=(0, 10))

        row1 = ctk.CTkFrame(frame, fg_color=C["panel"])
        row1.pack(fill="x", padx=14, pady=(12, 4))

        self._reg(
            ctk.CTkLabel(row1, text=self.T("hex_input"), text_color=C["accent"], font=("Consolas", 9, "bold")),
            "hex_input",
        ).pack(anchor="w")

        self.hex_input = ctk.CTkTextbox(
            row1,
            height=70,
            fg_color=C["input_bg"],
            text_color=C["text"],
            border_width=0,
            corner_radius=8,
            font=MONO_LG,
            wrap="word",
        )
        self.hex_input.pack(fill="x", pady=(4, 0))
        self._setup_placeholder(self.hex_input, self.T("placeholder"))

        row2 = ctk.CTkFrame(frame, fg_color=C["panel"])
        row2.pack(fill="x", padx=14, pady=(8, 12))

        key_meta = ctk.CTkFrame(row2, fg_color=C["panel"])
        key_meta.pack(side="left", anchor="n", padx=(0, 10))
        self._reg(
            ctk.CTkLabel(key_meta, text=self.T("key"), text_color=C["accent2"], font=("Consolas", 9, "bold")),
            "key",
        ).pack(anchor="w")
        self._reg(
            ctk.CTkLabel(key_meta, text=self.T("key_sub"), text_color=C["dim"], font=("Consolas", 8)),
            "key_sub",
        ).pack(anchor="w")

        self.key_input = ctk.CTkEntry(
            row2,
            fg_color=C["input_bg"],
            text_color=C["text"],
            border_width=0,
            corner_radius=8,
            font=MONO_LG,
            width=180,
        )
        self.key_input.pack(side="left", ipady=6, ipadx=6)
        self.key_input.insert(0, "0xFF")

        self._reg(
            ctk.CTkLabel(row2, text=self.T("key_hint"), text_color=C["dim"], font=LBL_FONT),
            "key_hint",
        ).pack(side="left", padx=(8, 0))

    def _build_controls(self, parent: tk.Frame):
        # Build operation, mode selection and action buttons
        # Stack vertically to avoid horizontal overflow on smaller windows.
        ctrl = ctk.CTkFrame(parent, fg_color=C["bg"])
        ctrl.pack(fill="x", pady=(0, 10), anchor="n")
        ctrl.grid_columnconfigure(0, weight=1)

        # Operation group
        op_lf = ctk.CTkFrame(
            ctrl,
            fg_color=C["bg"],
            corner_radius=10,
            border_width=1,
            border_color=C["border"],
        )
        op_lf.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        op_title = ctk.CTkLabel(op_lf, text=self.T("op_label"), text_color=C["dim"], font=LBL_FONT)
        op_title.pack(anchor="w", padx=10, pady=(8, 0))
        self._reg(op_title, "op_label")

        op_row = ctk.CTkFrame(op_lf, fg_color=C["bg"])
        op_row.pack(fill="x", padx=8, pady=8)

        self._rb_xor = ctk.CTkRadioButton(
            op_row,
            text=self.T("op_xor"),
            variable=self._op_var,
            value="XOR",
            fg_color=C["accent"],
            hover_color=C["accent"],
            text_color=C["text"],
            font=("Consolas", 10, "bold"),
        )
        self._rb_xor.pack(side="left", padx=(0, 8))
        self._reg(self._rb_xor, "op_xor")

        self._rb_add = ctk.CTkRadioButton(
            op_row,
            text=self.T("op_add"),
            variable=self._op_var,
            value="ADD",
            fg_color=C["good"],
            hover_color=C["good"],
            text_color=C["text"],
            font=("Consolas", 10, "bold"),
        )
        self._rb_add.pack(side="left", padx=(0, 8))
        self._reg(self._rb_add, "op_add")

        self._rb_sub = ctk.CTkRadioButton(
            op_row,
            text=self.T("op_sub"),
            variable=self._op_var,
            value="SUB",
            fg_color=C["bad"],
            hover_color=C["bad"],
            text_color=C["text"],
            font=("Consolas", 10, "bold"),
        )
        self._rb_sub.pack(side="left")
        self._reg(self._rb_sub, "op_sub")

        # Mode group
        mode_lf = ctk.CTkFrame(
            ctrl,
            fg_color=C["bg"],
            corner_radius=10,
            border_width=1,
            border_color=C["border"],
        )
        mode_lf.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        mode_title = ctk.CTkLabel(mode_lf, text=self.T("mode_label"), text_color=C["dim"], font=LBL_FONT)
        mode_title.pack(anchor="w", padx=10, pady=(8, 0))
        self._reg(mode_title, "mode_label")

        mode_row = ctk.CTkFrame(mode_lf, fg_color=C["bg"])
        mode_row.pack(fill="x", padx=8, pady=8)

        self._rb_bytewise = ctk.CTkRadioButton(
            mode_row,
            text=self.T("mode_bytewise"),
            variable=self._mode_var,
            value="bytewise",
            fg_color=C["accent"],
            hover_color=C["accent"],
            text_color=C["text"],
            font=MONO,
        )
        self._rb_bytewise.pack(side="left", padx=(0, 8))
        self._reg(self._rb_bytewise, "mode_bytewise")

        self._rb_direct = ctk.CTkRadioButton(
            mode_row,
            text=self.T("mode_direct"),
            variable=self._mode_var,
            value="direct",
            fg_color=C["accent2"],
            hover_color=C["accent2"],
            text_color=C["text"],
            font=MONO,
        )
        self._rb_direct.pack(side="left")
        self._reg(self._rb_direct, "mode_direct")

        # Action buttons row: use grid so it can shrink instead of overflowing
        btn_f = ctk.CTkFrame(ctrl, fg_color=C["bg"])
        btn_f.grid(row=2, column=0, sticky="ew")
        for i in range(3):
            btn_f.grid_columnconfigure(i, weight=1)

        self._btn_calc = HoverButton(
            btn_f,
            text=self.T("btn_calc"),
            command=self._calculate,
            fg_color="#0d2a1f",
            hover_color="#113d2c",
            text_color=C["good"],
            font=("Consolas", 10, "bold"),
        )
        self._btn_calc.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=2)
        self._reg(self._btn_calc, "btn_calc")

        self._btn_endian = HoverButton(
            btn_f,
            text=self.T("btn_endian"),
            command=self._endian_swap,
            fg_color="#1e1030",
            hover_color="#2d1a47",
            text_color=C["accent2"],
            font=("Consolas", 10, "bold"),
        )
        self._btn_endian.grid(row=0, column=1, sticky="ew", padx=(0, 6), ipady=2)
        self._reg(self._btn_endian, "btn_endian")

        self._btn_clear = HoverButton(
            btn_f,
            text=self.T("btn_clear"),
            command=self._clear,
            fg_color=C["btn_bg"],
            hover_color=C["btn_hover"],
            text_color=C["dim"],
            font=("Consolas", 10),
        )
        self._btn_clear.grid(row=0, column=2, sticky="ew", ipady=2)
        self._reg(self._btn_clear, "btn_clear")

    def _build_output_section(self, parent: tk.Frame):
        self._out_frame = ctk.CTkFrame(parent, fg_color=C["bg"])
        self._out_frame.pack(fill="both", expand=True, pady=(0, 10))

        panels_def = [
            ("out_hex", C["hex_out"], "hex_out"),
            ("out_dec", C["dec_out"], "dec_out"),
            ("out_ascii", C["asc_out"], "asc_out"),
        ]

        self._out_panels = []

        for label_key, colour, attr in panels_def:
            col = ctk.CTkFrame(
                self._out_frame,
                fg_color=C["panel"],
                corner_radius=12,
                border_width=1,
                border_color=colour,
            )
            self._out_panels.append(col)

            hdr = ctk.CTkFrame(col, fg_color=colour, corner_radius=10)
            hdr.pack(fill="x", padx=0, pady=0)

            title_lbl = ctk.CTkLabel(
                hdr,
                text=self.T(label_key),
                text_color=C["bg"],
                font=("Consolas", 10, "bold"),
            )
            title_lbl.pack(side="left", padx=8, pady=1)
            self._reg(title_lbl, label_key)

            copy_lbl = ctk.CTkLabel(
                hdr,
                text=self.T("copy"),
                text_color=C["bg"],
                font=("Consolas", 8),
                cursor="hand2",
            )
            copy_lbl.pack(side="right", padx=8, pady=2)
            copy_lbl.bind("<Button-1>", lambda e, a=attr: self._copy(a))
            self._reg(copy_lbl, "copy")

            txt = ctk.CTkTextbox(
                col,
                fg_color=C["input_bg"],
                text_color=colour,
                border_width=0,
                corner_radius=8,
                font=MONO_LG,
                wrap="word",
                height=120,
            )
            # txt.pack(fill="both", expand=True, padx=6, pady=6)
            txt.pack_propagate(False)
            txt.pack(fill="both", expand=True, padx=6, pady=(2, 6))
            txt.configure(state="disabled")
            setattr(self, attr, txt)

        self._relayout_outputs()

    def _build_status_bar(self):
        hsep(self)
        row = ctk.CTkFrame(self, fg_color=C["bg"])
        row.pack(fill="x", padx=20, pady=(4, 8))

        self.status_var = tk.StringVar(value=self.T("status_ready"))
        self._status_lbl = ctk.CTkLabel(row, textvariable=self.status_var, text_color=C["dim"], font=LBL_FONT,
                                        anchor="w")
        self._status_lbl.pack(side="left")

        self._hint_lbl = ctk.CTkLabel(row, text=self.T("status_hint"), text_color=C["dim"], font=LBL_FONT)
        self._hint_lbl.pack(side="right")
        self._reg(self._hint_lbl, "status_hint")

    # Placeholder

    def _setup_placeholder(self, widget: ctk.CTkTextbox, text: str):
        widget._placeholder_text = text
        widget.insert("1.0", text)
        # placeholder 也使用白色
        widget.configure(text_color="#FFFFFF")

        def on_in(_):
            if widget.get("1.0", "end-1c") == widget._placeholder_text:
                widget.delete("1.0", "end")
                widget.configure(text_color="#FFFFFF")

        def on_out(_):
            if not widget.get("1.0", "end-1c").strip():
                widget.configure(text_color="#FFFFFF")
                widget.delete("1.0", "end")
                widget.insert("1.0", widget._placeholder_text)

        widget.bind("<FocusIn>", on_in)
        widget.bind("<FocusOut>", on_out)

    def _get_hex_input(self) -> str:
        raw = self.hex_input.get("1.0", "end-1c")
        ph = getattr(self.hex_input, "_placeholder_text", "")
        return "" if raw == ph else raw

    # Output rendering

    def _set_output(self, widget: ctk.CTkTextbox, text: str):
        old = widget.get("1.0", "end-1c")

        if old == text:
            return

        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _render_outputs(self, result: list[int]):
        self._set_output(self.hex_out, bytes_to_hex(result))
        self._set_output(self.dec_out, bytes_to_dec(result, self.T("dec_combined")))
        self._set_output(self.asc_out, bytes_to_ascii(result, self.T("asc_printable")))

    # Status helper

    def _status(self, msg: str, colour: str = C["dim"]):
        self._status_colour = colour
        self.status_var.set(msg)
        self._status_lbl.configure(text_color=colour)

    # Actions

    def _calculate(self):
        data = parse_hex(self._get_hex_input())
        if data is None:
            self._status(self.T("err_hex"), C["bad"])
            return

        key = parse_key(self.key_input.get())
        if key is None:
            self._status(self.T("err_key"), C["bad"])
            return

        op = self._op_var.get()
        mode = self._mode_var.get()

        try:
            result = op_bytewise(data, key, op) if mode == "bytewise" else op_direct(data, key, op)
        except Exception as exc:
            self._status(self.T("err_generic", exc), C["bad"])
            return

        self._last_result = result
        self._render_outputs(result)

        mode_name = self.T("mode_bw_name") if mode == "bytewise" else self.T("mode_dr_name")
        self._status(self.T("status_calc", op, mode_name, f"{key:X}", len(data)), C["good"])

    def _endian_swap(self):
        data = parse_hex(self._get_hex_input())
        if data is None:
            self._status(self.T("err_swap"), C["bad"])
            return

        swapped = endian_swap(data)
        self._last_result = swapped

        self.hex_input.configure(text_color=C["text"])
        self.hex_input.delete("1.0", "end")
        self.hex_input.insert("1.0", bytes_to_hex(swapped))

        self._render_outputs(swapped)
        self._status(self.T("status_endian", len(data)), C["accent2"])

    def _clear(self):
        self._last_result = None

        ph = self.T("placeholder")
        self.hex_input._placeholder_text = ph

        # 永远白色
        self.hex_input.configure(text_color="#FFFFFF")

        self.hex_input.delete("1.0", "end")
        self.hex_input.insert("1.0", ph)

        self.hex_input.focus_set()
        self.hex_input.tag_add("sel", "1.0", "end-1c")
        self.hex_input.mark_set("insert", "1.0")
        self.hex_input.see("insert")

        self.key_input.delete(0, "end")
        self.key_input.insert(0, "0xFF")

        for attr in ("hex_out", "dec_out", "asc_out"):
            self._set_output(getattr(self, attr), "")

        self._status(self.T("status_cleared"), C["dim"])

    def _copy(self, attr: str):
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
