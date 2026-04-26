import tkinter as tk
from dataclasses import dataclass
from math import log

@dataclass
class Viewport:
    # 画面上でどこを見ているか（複素平面）
    center_x: float = -0.5
    center_y: float = 0.0
    # 1ピクセルあたり何だけ複素平面で進むか（解像度）
    scale: float = 3.0 / 800  # width=800 のとき、横幅3.0くらいを見る

class FractalExplorer:
    """
    最小限だけどちゃんと遊べるフラクタルエクスプローラ。

    構造イメージ:
      - Viewport: 「どこを見てるか」
      - pixel_to_complex: 「ピクセル → 複素数」
      - mandelbrot_iter / julia_iter: 「各点が何回で発散するか」
      - color_for_iter: 「発散までの回数 → 色」
      - render: 「全部のピクセルに対して上を回す」
    """
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height

        # --- フラクタルのパラメータ ---
        self.viewport = Viewport()
        self.max_iter = 200
        self.mode = "mandelbrot"   # or "julia"
        self.julia_c = complex(-0.4, 0.6)
        self.color_scheme = 0      # 0: グレー, 1: なめらかカラー

        # --- Tkinter の準備 ---
        self.root = tk.Tk()
        self.root.title("Python Fractal Explorer (Mandelbrot / Julia)")

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # ここにピクセルを書き込む
        self.img = tk.PhotoImage(width=self.width, height=self.height)
        self.canvas.create_image(0, 0, image=self.img, anchor=tk.NW)

        # ステータスバー
        self.status = tk.Label(self.root, text="", anchor="w")
        self.status.pack(fill=tk.X)

        # ドラッグ用
        self.drag_start_x = None
        self.drag_start_y = None
        self.viewport_start = None

        # --- イベント登録 ---
        # 左クリック → ズームイン
        self.canvas.bind("<Button-1>", self.on_left_click)
        # 中ボタンでパン
        self.canvas.bind("<ButtonPress-2>", self.on_middle_press)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_release)

        # マウスホイール（Windows / Mac）
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        # Linux 用
        self.canvas.bind("<Button-4>", self.on_mouse_wheel_linux)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel_linux)

        # キーボード
        self.root.bind("<Key>", self.on_key)

        # ウィンドウサイズ変更時
        self.canvas.bind("<Configure>", self.on_resize)

        self.update_status()
        self.render()

    # ============================================================
    #  論理1: ピクセル座標 → 複素数の対応
    # ============================================================
    def pixel_to_complex(self, px, py):
        """
        ピクセル(px, py)を複素平面上の座標に変換。
        アスペクト比が崩れないように、y方向だけ少し調整。
        """
        vp = self.viewport
        aspect = self.height / self.width
        x = vp.center_x + (px - self.width / 2) * vp.scale
        y = vp.center_y + (py - self.height / 2) * vp.scale * aspect
        return complex(x, y)

    # ============================================================
    #  論理2: 各点の「発散までの回数」を計算
    # ============================================================
    def mandelbrot_iter(self, c):
        """マンデルブロ集合: z_{n+1} = z_n^2 + c, z_0 = 0."""
        z = 0 + 0j
        for n in range(self.max_iter):
            if z.real * z.real + z.imag * z.imag > 4.0:  # |z|^2 > 4
                return n, z
            z = z * z + c
        return self.max_iter, z  # 発散しなかった（とみなす）

    def julia_iter(self, z0):
        """ジュリア集合: z_{n+1} = z_n^2 + c (c は固定)."""
        z = z0
        c = self.julia_c
        for n in range(self.max_iter):
            if z.real * z.real + z.imag * z.imag > 4.0:
                return n, z
            z = z * z + c
        return self.max_iter, z

    # ============================================================
    #  論理3: 回数 → 色
    # ============================================================
    def color_for_iter(self, n, z):
        """
        iteration 回数から色を決める関数。
        - n >= max_iter: 黒
        - n < max_iter: スキームに応じて色をつける
        """
        if n >= self.max_iter:
            return "#000000"  # セットの中身

        if self.color_scheme == 0:
            # 単純グレースケール
            v = int(255 * n / self.max_iter)
            return f"#{v:02x}{v:02x}{v:02x}"

        # スムーズ着色
        zn = abs(z)
        if zn == 0:
            mu = n
        else:
            # log log でバンディングを抑えるおまじない
            mu = n + 1 - log(log(zn)) / log(2)
        t = mu / self.max_iter  # 0 ~ 1 に正規化

        # t を簡易HSVにマッピング
        h = t * 6.0  # 0..6
        s = 1.0
        v = 1.0 if t < 1 else 0.0

        i = int(h) % 6
        f = h - int(h)
        p = v * (1 - s)
        q = v * (1 - f * s)
        r = v * (1 - (1 - f) * s)

        if i == 0:
            r, g, b = v, r, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, r
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = r, p, v
        else:
            r, g, b = v, p, q

        R = int(r * 255)
        G = int(g * 255)
        B = int(b * 255)
        return f"#{R:02x}{G:02x}{B:02x}"

    # ============================================================
    #  論理4: 全ピクセルを走査して描画
    # ============================================================
    def render(self):
        """PhotoImage にフラクタルを描くメインループ."""
        self.root.title(f"Python Fractal Explorer – {self.mode} – max_iter={self.max_iter}")
        for y in range(self.height):
            row_colors = []
            for x in range(self.width):
                c = self.pixel_to_complex(x, y)
                if self.mode == "mandelbrot":
                    n, z = self.mandelbrot_iter(c)
                else:
                    n, z = self.julia_iter(c)
                color = self.color_for_iter(n, z)
                row_colors.append(color)
            # 1行まとめて描くことで多少高速化
            line = "{" + " ".join(row_colors) + "}"
            self.img.put(line, to=(0, y))
        self.update_status()

    # ============================================================
    #  イベントハンドラ（UI 部分）
    # ============================================================
    def on_resize(self, event):
        """キャンバスサイズ変更時に画像を作り直す。"""
        if event.width == self.width and event.height == self.height:
            return
        self.width = max(50, event.width)
        self.height = max(50, event.height)
        self.img = tk.PhotoImage(width=self.width, height=self.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.img, anchor=tk.NW)
        self.render()

    def zoom_at(self, factor, px, py):
        """
        (px, py) を中心にズーム。
        factor < 1: ズームイン
        factor > 1: ズームアウト
        """
        z_click = self.pixel_to_complex(px, py)
        vp = self.viewport

        # スケールだけ変えると、写ってる範囲が z_click に寄る
        vp.scale *= factor
        vp.center_x = z_click.real
        vp.center_y = z_click.imag

        self.render()

    def on_left_click(self, event):
        # 左クリックで 0.5 倍ズームイン
        self.zoom_at(0.5, event.x, event.y)

    def on_mouse_wheel(self, event):
        # Windows / Mac 用
        factor = 0.8 if event.delta > 0 else 1.25
        self.zoom_at(factor, event.x, event.y)

    def on_mouse_wheel_linux(self, event):
        # Linux 用
        factor = 0.8 if event.num == 4 else 1.25
        self.zoom_at(factor, event.x, event.y)

    def on_middle_press(self, event):
        # パン開始
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.viewport_start = Viewport(
            center_x=self.viewport.center_x,
            center_y=self.viewport.center_y,
            scale=self.viewport.scale
        )

    def on_middle_drag(self, event):
        # 中ボタンを引きずっている間に視点を動かす
        if self.viewport_start is None:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        aspect = self.height / self.width
        self.viewport.center_x = self.viewport_start.center_x - dx * self.viewport.scale
        self.viewport.center_y = self.viewport_start.center_y - dy * self.viewport.scale * aspect
        self.render()

    def on_middle_release(self, event):
        self.viewport_start = None

    def on_key(self, event):
        key = event.keysym.lower()
        if key == "m":
            self.mode = "mandelbrot"
        elif key == "j":
            self.mode = "julia"
        elif key == "c":
            self.color_scheme = (self.color_scheme + 1) % 2
        elif key == "r":
            # 視点リセット
            self.viewport = Viewport()
        elif key in ("plus", "equal"):
            self.max_iter = int(self.max_iter * 1.3) + 1
        elif key == "minus":
            self.max_iter = max(20, int(self.max_iter / 1.3))
        self.render()

    def update_status(self):
        self.status.config(
            text=(
                f"mode: {self.mode} | center=({self.viewport.center_x:.4f}, "
                f"{self.viewport.center_y:.4f}) | scale={self.viewport.scale:.5f} | "
                f"max_iter={self.max_iter} | color_scheme={self.color_scheme}"
            )
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FractalExplorer()
    app.run()
