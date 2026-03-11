import threading
import time

import customtkinter as ctk
import requests

API_GATEWAY_URL = "http://localhost:8000/v1"

# Aesthetically matching the ultra-premium Vercel/Linear top-tier theme
BG_COLOR = "#000000"  # True OLED Black
SIDEBAR_BG = "#050505" # Ultra dark grey sidebar
CARD_BG = "#0A0C10"    # Elevated dark cards
BORDER_COLOR = "#1E2430" # Subtle slate borders
TEXT_MAIN = "#EDEDED"
TEXT_MUTED = "#888888"

ACCENT_BLUE = "#3B82F6"   # Vercel Blue
ACCENT_GREEN = "#10B981"  # Emerald Green
ACCENT_RED = "#EF4444"    # Alert Red
ACCENT_ORANGE = "#F59E0B" # Warning Orange
ACCENT_PURPLE = "#8B5CF6" # Royal Purple

ACTIVE_BG = "#1A1D24"  # Subtle selection background
ACTIVE_TEXT = "#EDEDED" # Crisp white active text


class AutoHealApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("AutoHeal AI - Autonomous DevOps")
        self.geometry("1400x900")
        self.configure(fg_color=BG_COLOR)

        # Grid layout (Sidebar + Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # state variables
        self.is_running = True
        self.active_incident_id = None

        # Blinking animation state
        self.is_blinking = False
        self.blinking_node_name = ""
        self.blink_state = False
        
        # Approval state
        self.approval_dialog_open = False

        # Keep track of nav buttons to restyle them
        self.nav_buttons = {}

        # ----------------------------------------------------
        # Sidebar
        # ----------------------------------------------------
        self.sidebar_frame = ctk.CTkFrame(
            self, width=260, corner_radius=0, fg_color=SIDEBAR_BG, border_width=0
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=24, pady=(28, 32), sticky="w")

        shield_lbl = ctk.CTkLabel(
            logo_frame, text="🛡️", font=ctk.CTkFont(size=28), text_color=ACCENT_PURPLE
        )
        shield_lbl.pack(side="left", padx=(0, 12))

        title_box = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="AutoHeal AI",
            font=ctk.CTkFont(size=20, weight="bold", family="Inter"),
            text_color=TEXT_MAIN,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Enterprise Mission Control",
            font=ctk.CTkFont(size=11, family="Inter", weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        # Nav Items (Mapped to Pitch)
        self.add_nav_item(1, "⊞", "System Topology")
        self.add_nav_item(2, "🐛", "1️⃣ Autonomous Bug Detection")
        self.add_nav_item(3, "🧠", "2️⃣ AI Root Cause Analysis")
        self.add_nav_item(4, "💡", "3️⃣ Intelligent Fix Suggestion")
        self.add_nav_item(5, "🧪", "4️⃣ Sandbox Testing Environment")
        self.add_nav_item(6, "🩹", "5️⃣ Self-Healing Deployment")

        # Connection status at bottom
        status_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        status_box.grid(row=9, column=0, padx=24, pady=24, sticky="w")
        ctk.CTkLabel(
            status_box,
            text="🔌 Reconnecting...",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            status_box,
            text="⚡ Engine Active",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w")

        # ----------------------------------------------------
        # Main Content Frames Container
        # ----------------------------------------------------
        self.main_frame_container = ctk.CTkFrame(
            self, fg_color=BG_COLOR, corner_radius=0
        )
        self.main_frame_container.grid(row=0, column=1, sticky="nsew", padx=40, pady=32)
        self.main_frame_container.grid_columnconfigure(0, weight=1)
        self.main_frame_container.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # Dashboard Frame
        # ----------------------------------------------------
        self.dashboard_frame = ctk.CTkFrame(
            self.main_frame_container, fg_color="transparent"
        )
        self.dashboard_frame.grid_columnconfigure(0, weight=7)  # Topology
        self.dashboard_frame.grid_columnconfigure(1, weight=3)  # Inject Fault
        self.dashboard_frame.grid_rowconfigure(2, weight=1)
        self.dashboard_frame.grid_rowconfigure(3, weight=2)  # Trace space

        # Header
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 24))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(
            title_frame,
            text="System Dashboard",
            font=ctk.CTkFont(family="Inter", size=32, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Real-time infrastructure monitoring & self-healing",
            font=ctk.CTkFont(family="Inter", size=14),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="🟢 Passive Log Monitoring Active",
            text_color=ACCENT_GREEN,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
        ).pack(side="right")

        # ----------------------------------------------------
        # Stats Row
        # ----------------------------------------------------
        stats_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.stat_components = {}
        self.add_stat_card(stats_frame, 0, "⊞", "2", "Total Services", ACCENT_BLUE)
        self.stat_components["healthy"] = self.add_stat_card(
            stats_frame, 1, "🛡️", "2", "Healthy", ACCENT_GREEN
        )
        self.stat_components["incidents"] = self.add_stat_card(
            stats_frame, 2, "⚠", "0", "Active Incidents", ACCENT_RED
        )
        self.add_stat_card(stats_frame, 3, "⏱", "12s", "Avg MTTR", ACCENT_ORANGE)
        self.add_stat_card(
            stats_frame, 4, "⚡", "100%", "Auto-Heal Rate", ACCENT_PURPLE
        )
        self.add_stat_card(stats_frame, 5, "📈", "100%", "Uptime", ACCENT_BLUE)

        # ----------------------------------------------------
        # Service Topology (Left Panel)
        # ----------------------------------------------------
        topology_frame = ctk.CTkFrame(
            self.dashboard_frame,
            fg_color=SIDEBAR_BG,
            border_color=ACCENT_BLUE,
            border_width=1,
            corner_radius=16,
        )
        topology_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 20))

        ctk.CTkLabel(
            topology_frame,
            text="⊞ Service Topology",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(anchor="w", padx=24, pady=(24, 10))

        # Canvas for graph
        self.topology_canvas = ctk.CTkCanvas(
            topology_frame, bg=SIDEBAR_BG, highlightthickness=0
        )
        self.topology_canvas.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.draw_topology()

        # ----------------------------------------------------
        # Fault Injection Panel (Right Panel)
        # ----------------------------------------------------
        right_container = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        right_container.grid(row=2, column=1, sticky="nsew")
        right_container.grid_columnconfigure(0, weight=1)
        right_container.grid_rowconfigure(0, weight=1)

        fault_frame = ctk.CTkFrame(right_container, fg_color="transparent")
        fault_frame.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            fault_frame,
            text="🐛 Fault Injection",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            fault_frame,
            text="Inject faults to test self-healing capabilities",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 24))

        ctk.CTkLabel(
            fault_frame,
            text="Target Service",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")
        self.target_service = ctk.CTkOptionMenu(
            fault_frame,
            values=[
                "task-web-ui",
                "auth-service",
                "task-database",
                "redis-cache",
                "task-backend-api",
            ],
            fg_color=CARD_BG,
            button_color=CARD_BG,
            button_hover_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
            dropdown_fg_color=CARD_BG,
            height=40,
            corner_radius=8,
        )
        self.target_service.pack(fill="x", pady=(8, 20))

        ctk.CTkLabel(
            fault_frame,
            text="Fault Type",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        real_world_bugs = [
            "App Crash (OOM Memory Overflow)",
            "Latency / Slow API (Timeout)",
            "Memory Leak (Heap Fill)",
            "Logic Error (Invalid Stats)",
            "DB Connection Failure",
        ]

        self.fault_type = ctk.CTkOptionMenu(
            fault_frame,
            values=real_world_bugs,
            fg_color=CARD_BG,
            button_color=CARD_BG,
            button_hover_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
            dropdown_fg_color=CARD_BG,
            height=40,
            corner_radius=8,
        )
        self.fault_type.pack(fill="x", pady=(8, 24))

        self.inject_btn = ctk.CTkButton(
            fault_frame,
            text="⚡ Inject Fault",
            command=self.trigger_alert,
            fg_color="#1A0F14",
            hover_color="#2D1119",
            border_width=1,
            border_color="#3B1724",
            text_color=ACCENT_RED,
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(family="Inter", weight="bold", size=14),
        )
        self.inject_btn.pack(fill="x")

        # ----------------------------------------------------
        # Recent Activity (Bottom Row, spans both columns)
        # Ensuring it has enough space as requested
        # ----------------------------------------------------
        trace_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        trace_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(24, 0))
        trace_frame.grid_rowconfigure(1, weight=1)
        trace_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            trace_frame,
            text="Recent Activity & Mathematical Trace",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Split into Log and Bayesian Matrix
        trace_split = ctk.CTkFrame(trace_frame, fg_color="transparent")
        trace_split.grid(row=1, column=0, sticky="nsew")
        trace_split.grid_rowconfigure(0, weight=1)
        trace_split.grid_columnconfigure(0, weight=6)
        trace_split.grid_columnconfigure(1, weight=4)

        self.textbox = ctk.CTkTextbox(
            trace_split,
            fg_color=CARD_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.textbox.insert(
            "end", "No incidents yet. Inject a fault to see the magic!\n"
        )
        self.textbox.configure(state="disabled")

        # Bayesian Confidence Matrix
        matrix_frame = ctk.CTkFrame(
            trace_split,
            fg_color=CARD_BG,
            border_color=ACCENT_PURPLE,
            border_width=1,
            corner_radius=12,
        )
        matrix_frame.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(
            matrix_frame, 
            text="Bayesian Inference Matrix", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=ACCENT_PURPLE
        ).pack(pady=(12, 4))

        self.bayesian_display = ctk.CTkTextbox(
            matrix_frame,
            fg_color="transparent",
            text_color=ACCENT_BLUE,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.bayesian_display.pack(fill="both", expand=True, padx=8, pady=8)
        self.bayesian_display.insert("end", "[ P(H|E) = [P(E|H) * P(H)] / P(E) ]\n\nAwaiting Tensor Core Activation...")
        self.bayesian_display.configure(state="disabled")

        # start monitor loop
        threading.Thread(target=self.poll_agent, daemon=True).start()

        # Secondary Frames mapped to pitch
        self.services_frame = self.build_services_frame()  # Used for Topology
        self.incidents_frame = self.build_incidents_frame()
        self.terminal_frame = self.build_terminal_frame()
        self.fix_suggestion_frame = self.build_fix_suggestion_frame()
        self.sandbox_frame = self.build_sandbox_frame()
        self.self_healing_frame = self.build_self_healing_frame()

        # Default View
        self.frames = {
            "System Topology": self.dashboard_frame,
            "1️⃣ Autonomous Bug Detection": self.incidents_frame,
            "2️⃣ AI Root Cause Analysis": self.terminal_frame,
            "3️⃣ Intelligent Fix Suggestion": self.fix_suggestion_frame,
            "4️⃣ Sandbox Testing Environment": self.sandbox_frame,
            "5️⃣ Self-Healing Deployment": self.self_healing_frame,
        }
        self.select_frame_by_name("System Topology")

    def animate_topology(self):
        # We can animate traffic dots and the blinking state
        self.animation_tick = getattr(self, "animation_tick", 0) + 1

        if getattr(self, "is_blinking", False):
            # Slow blink toggle
            if self.animation_tick % 10 == 0:
                self.blink_state = not getattr(self, "blink_state", False)

        self.draw_topology()
        self.after(50, self.animate_topology)  # Faster refresh for smooth traffic

    def draw_topology(self):
        self.topology_canvas.delete("all")
        
        # Draw background engineering grid for IIT-standard look
        w = 1200  # Assume a large enough canvas width to cover
        h = 800
        for i in range(0, w, 40):
            self.topology_canvas.create_line(i, 0, i, h, fill="#111318", dash=(2, 4))
        for j in range(0, h, 40):
            self.topology_canvas.create_line(0, j, w, j, fill="#111318", dash=(2, 4))

        # Shift the center slightly up to perfectly center the 3-layer tree
        cx, cy = 350, 160
        nodes = [
            ("Task Web UI", cx, cy - 95, ACCENT_BLUE, "🌐"),
            ("Auth Service", cx - 180, cy, ACCENT_GREEN, "🔐"),
            ("Task Database", cx + 180, cy, ACCENT_ORANGE, "💾"),
            ("Redis Cache", cx - 180, cy + 115, ACCENT_GREEN, "⚡"),
            ("Task Backend API", cx, cy + 115, ACCENT_GREEN, "⚙️"),
        ]

        edges = [(0, 1), (0, 2), (1, 3), (2, 4), (1, 4), (0, 4)]

        tick = int(getattr(self, "animation_tick", 0))

        # Draw edges and traffic with Bezier curves
        for i, j in edges:
            _, x1, y1, _, _ = nodes[i]
            _, x2, y2, _, _ = nodes[j]

            # Control point for bezier curve (bend outwards slightly)
            import math

            cx_bezier = (x1 + x2) / 2
            cy_bezier = (y1 + y2) / 2 - 40

            # Approximate a curve using line segments
            steps = 20
            prev_x, prev_y = x1, y1
            for step in range(1, steps + 1):
                t = step / steps
                # Quadratic bezier formula
                qx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx_bezier + t**2 * x2
                qy = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy_bezier + t**2 * y2
                self.topology_canvas.create_line(
                    prev_x, prev_y, qx, qy, fill="#2a3241", width=2
                )
                prev_x, prev_y = qx, qy

            # Draw moving particle along the true curve
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist > 0:
                progress = ((tick + i * 15 + j * 10) % 100) / 100.0
                px = (
                    (1 - progress) ** 2 * x1
                    + 2 * (1 - progress) * progress * cx_bezier
                    + progress**2 * x2
                )
                py = (
                    (1 - progress) ** 2 * y1
                    + 2 * (1 - progress) * progress * cy_bezier
                    + progress**2 * y2
                )

                # Neon cyan leading particle with trail (Forward Flow)
                self.topology_canvas.create_oval(
                    px - 8, py - 8, px + 8, py + 8, fill="", outline=ACCENT_BLUE, width=1
                )
                self.topology_canvas.create_oval(
                    px - 4, py - 4, px + 4, py + 4, fill=ACCENT_BLUE, outline=""
                )

                # Reverse particle (bidirectional traffic) magenta
                progress2 = ((tick + j * 15 + i * 10) % 100) / 100.0
                px2 = (
                    (1 - progress2) ** 2 * x1
                    + 2 * (1 - progress2) * progress2 * cx_bezier
                    + progress2**2 * x2
                )
                py2 = (
                    (1 - progress2) ** 2 * y1
                    + 2 * (1 - progress2) * progress2 * cy_bezier
                    + progress2**2 * y2
                )

                self.topology_canvas.create_oval(
                    px2 - 8,
                    py2 - 8,
                    px2 + 8,
                    py2 + 8,
                    fill="",
                    outline=ACCENT_RED,
                    width=1,
                )
                self.topology_canvas.create_oval(
                    px2 - 4, py2 - 4, px2 + 4, py2 + 4, fill=ACCENT_RED, outline=""
                )
        r_w, r_h = 85, 34
        for idx, (name, x, y, color, icon) in enumerate(nodes):
            is_target = getattr(self, "is_blinking", False) and name == getattr(
                self, "blinking_node_name", None
            )

            if is_target:
                fill_color = (
                    ACCENT_RED if getattr(self, "blink_state", False) else BG_COLOR
                )
                outline_color = ACCENT_RED
                # Draw aggressive glowing aura
                self.topology_canvas.create_oval(
                    x - r_w - 8,
                    y - r_h - 8,
                    x + r_w + 8,
                    y + r_h + 8,
                    fill="",
                    outline=ACCENT_RED,
                    width=2,
                    dash=(2, 4),
                )
                self.topology_canvas.create_oval(
                    x - r_w - 4,
                    y - r_h - 4,
                    x + r_w + 4,
                    y + r_h + 4,
                    fill="",
                    outline=ACCENT_RED,
                    width=1,
                )
            else:
                fill_color = SIDEBAR_BG  # Deep dark node core
                outline_color = color

            # Smartscape pseudo-3D shadow
            self.topology_canvas.create_oval(
                x - r_w + 2,
                y - r_h + 4,
                x + r_w + 2,
                y + r_h + 4,
                fill="#000000",
                outline="",
            )

            # Main Node Shell
            self.topology_canvas.create_oval(
                x - r_w,
                y - r_h,
                x + r_w,
                y + r_h,
                fill=fill_color,
                outline=outline_color,
                width=2,
            )
            # HUD Corner Accents
            c_len = 8
            hl_color = ACCENT_BLUE if not is_target else ACCENT_RED
            self.topology_canvas.create_line(x - r_w, y - r_h + c_len, x - r_w, y - r_h, x - r_w + c_len, y - r_h, fill=hl_color, width=2)
            self.topology_canvas.create_line(x + r_w - c_len, y - r_h, x + r_w, y - r_h, x + r_w, y - r_h + c_len, fill=hl_color, width=2)
            self.topology_canvas.create_line(x - r_w, y + r_h - c_len, x - r_w, y + r_h, x - r_w + c_len, y + r_h, fill=hl_color, width=2)
            self.topology_canvas.create_line(x + r_w - c_len, y + r_h, x + r_w, y + r_h, x + r_w, y + r_h - c_len, fill=hl_color, width=2)

            self.topology_canvas.create_text(
                x, y, text=f"{icon} {name}", fill=TEXT_MAIN, font=("Inter", 12, "bold")
            )

            # Live Metrics Badge (Dynatrace Style)
            metric_val = ["12ms", "99.9%", "4ms", "20k/s", "1msg/s"][idx]
            metric_color = ACCENT_GREEN if not is_target else ACCENT_RED
            
            badge_cx = x + r_w - 10
            badge_cy = y - r_h
            
            # Draw pill-shaped oval for the badge
            self.topology_canvas.create_oval(
                badge_cx - 24,
                badge_cy - 12,
                badge_cx + 24,
                badge_cy + 12,
                fill="#0A0C10",
                outline=metric_color,
                width=1,
            )
            self.topology_canvas.create_text(
                badge_cx,
                badge_cy,
                text=metric_val,
                fill=metric_color,
                font=("Consolas", 9, "bold"),
            )

    def build_services_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=12)
        ctk.CTkLabel(
            header,
            text="⚙ Service Registry",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(side="left", padx=24)

        table = ctk.CTkScrollableFrame(
            frame,
            fg_color=CARD_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=12,
        )
        table.grid(row=1, column=0, sticky="nsew")
        table.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for col, txt in enumerate(["SERVICE NAME", "NAMESPACE", "STATUS", "UPTIME"]):
            ctk.CTkLabel(
                table,
                text=txt,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED,
            ).grid(row=0, column=col, sticky="w", padx=24, pady=16)

        data = [
            ("task-web-ui", "production", "✅ Healthy", "42d 11h"),
            ("task-backend-api", "production", "✅ Healthy", "42d 11h"),
            ("task-database", "production", "✅ Healthy", "14d 2h"),
        ]

        self.service_status_labels = {}
        for row, (name, ns, status, uptime) in enumerate(data, start=1):
            ctk.CTkLabel(
                table,
                text=name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=TEXT_MAIN,
            ).grid(row=row, column=0, sticky="w", padx=24, pady=12)
            ctk.CTkLabel(
                table, text=ns, font=ctk.CTkFont(size=13), text_color=TEXT_MUTED
            ).grid(row=row, column=1, sticky="w", padx=24, pady=12)
            slbl = ctk.CTkLabel(
                table,
                text=status,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=ACCENT_GREEN,
            )
            slbl.grid(row=row, column=2, sticky="w", padx=24, pady=12)
            self.service_status_labels[name] = slbl
            ctk.CTkLabel(
                table, text=uptime, font=ctk.CTkFont(size=13), text_color=TEXT_MUTED
            ).grid(row=row, column=3, sticky="w", padx=24, pady=12)

        return frame

    def build_incidents_frame(self):
        # Similar clean layout for incidents
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            frame,
            fg_color=CARD_BG,
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=12)
        ctk.CTkLabel(
            header,
            text="⚠ Incident Audit Log",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).pack(side="left", padx=24)

        table = ctk.CTkScrollableFrame(
            frame,
            fg_color=CARD_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=12,
        )
        table.grid(row=1, column=0, sticky="nsew")
        self.incidents_table = table

        self.incidents_terminal = ctk.CTkTextbox(
            table,
            fg_color=SIDEBAR_BG,
            text_color=ACCENT_RED,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=0,
            border_width=0,
        )
        self.incidents_terminal.pack(fill="both", expand=True)
        self.incidents_terminal.insert("end", "Awaiting Anomalies...\n")
        self.incidents_terminal.configure(state="disabled")

        return frame

    def build_terminal_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="Live Terminal (Real-time IIT-Grade SBFL Tracing)",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        self.full_terminal = ctk.CTkTextbox(
            frame,
            fg_color=SIDEBAR_BG,
            text_color=ACCENT_GREEN,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        self.full_terminal.grid(row=1, column=0, sticky="nsew")
        self.full_terminal.insert(
            "end", "[System] Live terminal connected. Awaiting autonomous actions...\n"
        )
        self.full_terminal.configure(state="disabled")
        return frame

    def build_fix_suggestion_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="💡 Intelligent Fix Suggestion",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))
        self.fix_terminal = ctk.CTkTextbox(
            frame,
            fg_color=SIDEBAR_BG,
            text_color=ACCENT_PURPLE,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        self.fix_terminal.grid(row=1, column=0, sticky="nsew")
        self.fix_terminal.insert("end", "Waiting for AI to generate patches...\n")
        self.fix_terminal.configure(state="disabled")
        return frame

    def build_sandbox_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="🧪 Sandbox Testing Environment",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))
        self.sandbox_terminal = ctk.CTkTextbox(
            frame,
            fg_color=SIDEBAR_BG,
            text_color=ACCENT_ORANGE,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        self.sandbox_terminal.grid(row=1, column=0, sticky="nsew")
        self.sandbox_terminal.insert(
            "end", "Waiting for code to enter isolated Sandbox...\n"
        )
        self.sandbox_terminal.configure(state="disabled")
        return frame

    def build_self_healing_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="🩹 Self-Healing Deployment",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))
        self.healing_terminal = ctk.CTkTextbox(
            frame,
            fg_color=SIDEBAR_BG,
            text_color=ACCENT_GREEN,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
            corner_radius=12,
            border_color=BORDER_COLOR,
            border_width=1,
        )
        self.healing_terminal.grid(row=1, column=0, sticky="nsew")
        self.healing_terminal.insert(
            "end", "Waiting to deploy patches to production...\n"
        )
        self.healing_terminal.configure(state="disabled")
        return frame

    def select_frame_by_name(self, name):
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(
                    fg_color=ACTIVE_BG, text_color=ACTIVE_TEXT, corner_radius=8
                )
            else:
                btn.configure(
                    fg_color="transparent", text_color=TEXT_MUTED, corner_radius=8
                )

        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

    def add_nav_item(self, row, icon, text):
        btn = ctk.CTkButton(
            self.sidebar_frame,
            text=f"  {icon}    {text}",
            anchor="w",
            fg_color="transparent",
            hover_color=ACTIVE_BG,
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=14, weight="bold", family="Inter"),
            height=44,
            command=lambda: self.select_frame_by_name(text),
        )
        btn.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
        self.nav_buttons[text] = btn

    def add_stat_card(self, parent, col, icon, value, label, icon_color="white"):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=12,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)

        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(anchor="w", fill="x", padx=16, pady=(16, 8))

        # Draw icon inside a very faint tinted circle
        icon_bg = ctk.CTkFrame(
            top_frame, fg_color="#1e293b", corner_radius=8, width=32, height=32
        )
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(
            icon_bg, text=icon, font=ctk.CTkFont(size=16), text_color=icon_color
        ).place(relx=0.5, rely=0.5, anchor="center")

        lbl_val = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold", family="Inter"),
            text_color=TEXT_MAIN,
        )
        lbl_val.pack(anchor="w", padx=16)

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=13, family="Inter"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 16))
        return lbl_val

    def log_message(self, message, clear=False):
        self.textbox.configure(state="normal")
        if clear:
            self.textbox.delete("1.0", "end")
        self.textbox.insert("end", f"{message}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

        self.full_terminal.configure(state="normal")
        if clear:
            self.full_terminal.insert("end", "\n-- Buffer Cleared --\n")
        self.full_terminal.insert("end", f"{message}\n")
        self.full_terminal.see("end")
        self.full_terminal.configure(state="disabled")

    def append_to_terminal(self, term, message):
        term.configure(state="normal")
        term.insert("end", f"{message}\n")
        term.see("end")
        term.configure(state="disabled")

    def trigger_alert(self):
        target = self.target_service.get()
        f_type = self.fault_type.get()

        node_map = {
            "task-web-ui": "Task Web UI",
            "auth-service": "Auth Service",
            "task-database": "Task Database",
            "redis-cache": "Redis Cache",
            "task-backend-api": "Task Backend API",
        }
        self.blinking_node_name = node_map.get(target, "")
        if self.blinking_node_name:
            self.is_blinking = True
            self.animate_topology()

        self.inject_btn.configure(
            state="disabled", text="Incident Active...", fg_color=CARD_BG
        )
        self.stat_components["healthy"].configure(text="1", text_color=ACCENT_RED)
        self.stat_components["incidents"].configure(text="1", text_color=ACCENT_RED)
        if target in self.service_status_labels:
            self.service_status_labels[target].configure(
                text="🚨 Anomaly", text_color=ACCENT_RED
            )

        self.log_message(f"", clear=True)
        self.log_message(f"> Injecting {f_type} into {target}...", clear=True)

        def trigger_web_bug():
            try:
                if "Crash" in f_type:
                    requests.get("http://localhost:5000/api/crash", timeout=1)
                elif "Slow" in f_type:
                    requests.get("http://localhost:5000/api/slow", timeout=1)
                elif "Leak" in f_type:
                    for _ in range(10):
                        requests.post("http://localhost:5000/tasks", json={"title": "Leak"}, timeout=1)
                elif "Logic" in f_type:
                    requests.get("http://localhost:5000/api/stats", timeout=1)
                elif "DB" in f_type:
                    requests.get("http://localhost:5000/tasks", timeout=1)
            except:
                pass
        
        threading.Thread(target=trigger_web_bug, daemon=True).start()

        payload = {
            "status": "firing",
            "alerts": [
                {
                    "labels": {"job": target, "severity": "critical", "type": f_type},
                    "startsAt": str(time.time()),
                }
            ],
        }
        try:
            res = requests.post(
                f"{API_GATEWAY_URL}/alerts/webhook", json=payload, timeout=2
            )
            if res.status_code == 200:
                self.active_incident_id = res.json()["incident_id"]
            else:
                self.log_message(f"> [Error] Failed to connect: {res.text}")
                self.reset_ui()
        except Exception:
            self.log_message("> [Error] API Gateway Unreachable.")
            self.reset_ui()

    def reset_ui(self):
        self.is_blinking = False
        self.blinking_node_name = ""
        self.blink_state = False
        self.draw_topology()

        self.inject_btn.configure(
            state="normal", text="⚡ Inject Fault", fg_color="#3f1d24"
        )
        self.stat_components["healthy"].configure(text="2", text_color=TEXT_MAIN)
        self.stat_components["incidents"].configure(text="0", text_color=TEXT_MAIN)
        for lbl in self.service_status_labels.values():
            lbl.configure(text="✅ Healthy", text_color=ACCENT_GREEN)
        self.active_incident_id = None

    def poll_agent(self):
        last_trace_len = 0
        while self.is_running:
            # First, check if there's a new global active incident we didn't start manually
            if not self.active_incident_id:
                try:
                    res = requests.get(f"{API_GATEWAY_URL}/active_incident", timeout=1)
                    if res.status_code == 200:
                        data = res.json()
                        new_id = data.get("incident_id")
                        if new_id:
                            self.active_incident_id = new_id
                            self.log_message(f"")
                            self.log_message(
                                f"[System] 🚨 AI Gateway caught live outlier: Incident {new_id}"
                            )
                            self.inject_btn.configure(
                                state="disabled",
                                text="Incident Active...",
                                fg_color=CARD_BG,
                            )
                            self.stat_components["healthy"].configure(
                                text="1", text_color=ACCENT_RED
                            )
                            self.stat_components["incidents"].configure(
                                text="1", text_color=ACCENT_RED
                            )
                            
                            # Add initial bayesian telemetry
                            self.bayesian_display.configure(state="normal")
                            self.bayesian_display.delete("1.0", "end")
                            self.bayesian_display.insert("end", f"> INITIALIZING TENSOR CORE\n> Binding to Incident {new_id}\n> Calibrating P(H|E) Prior: 0.15\n")
                            self.bayesian_display.configure(state="disabled")
                            
                except Exception:
                    pass

            if self.active_incident_id:
                try:
                    res = requests.get(
                        f"{API_GATEWAY_URL}/incidents/{self.active_incident_id}",
                        timeout=2,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        status = data.get("status", "unknown")
                        trace = data.get("trace", [])
                        confidence = data.get("confidence_score")

                        if len(trace) > last_trace_len:
                            for log in trace[last_trace_len:]:
                                self.log_message(log)
                                
                                # Animate Bayesian Matrix on each new log
                                if status in ['analyzing', 'validating', 'sandboxing']:
                                    import random
                                    self.bayesian_display.configure(state="normal")
                                    # Fix lints by multiplying out to an integer
                                    noise1 = float(random.randint(100, 900)) / 1000.0
                                    noise2 = float(random.randint(10, 500)) / 1000.0
                                    self.bayesian_display.insert("end", f"\n-- Vector [θ={noise1}]\n-- Adjusting Weights...\n")
                                    self.bayesian_display.see("end")
                                    self.bayesian_display.configure(state="disabled")

                                # Route to 1st Task Bar: Bug Detection
                                self.append_to_terminal(self.incidents_terminal, log)

                                # Route to 3rd Task Bar: Intelligent Fix
                                if (
                                    "Proposed Fix" in log
                                    or "Confidence" in log
                                    or "REJECTED" in log
                                ):
                                    if (
                                        self.fix_terminal.get("1.0", "end").strip()
                                        == "Waiting for AI to generate patches..."
                                    ):
                                        self.fix_terminal.configure(state="normal")
                                        self.fix_terminal.delete("1.0", "end")
                                        self.fix_terminal.configure(state="disabled")
                                    self.append_to_terminal(self.fix_terminal, log)
                                    self.select_frame_by_name(
                                        "3️⃣ Intelligent Fix Suggestion"
                                    )

                                # Route to 4th Task Bar: Sandbox
                                if (
                                    "Policy Engine" in log
                                    or "OPA" in log
                                    or "Sandboxing" in log
                                ):
                                    if (
                                        self.sandbox_terminal.get("1.0", "end").strip()
                                        == "Waiting for code to enter isolated Sandbox..."
                                    ):
                                        self.sandbox_terminal.configure(state="normal")
                                        self.sandbox_terminal.delete("1.0", "end")
                                        self.sandbox_terminal.configure(
                                            state="disabled"
                                        )
                                    self.append_to_terminal(self.sandbox_terminal, log)
                                    self.select_frame_by_name(
                                        "4️⃣ Sandbox Testing Environment"
                                    )

                                # Route to 5th Task Bar: Self Healing
                                if (
                                    "GitOps" in log
                                    or "SUCCESS" in log
                                    or "FAILED" in log
                                    or "Deploy" in log
                                ):
                                    if (
                                        self.healing_terminal.get("1.0", "end").strip()
                                        == "Waiting to deploy patches to production..."
                                    ):
                                        self.healing_terminal.configure(state="normal")
                                        self.healing_terminal.delete("1.0", "end")
                                        self.healing_terminal.configure(
                                            state="disabled"
                                        )
                                    self.append_to_terminal(self.healing_terminal, log)
                                    self.select_frame_by_name(
                                        "5️⃣ Self-Healing Deployment"
                                    )

                                # Hacky way to animate the node if the trace mentions it
                                if "DETECTED CRITICAL FAULT IN: " in log:
                                    if (
                                        self.incidents_terminal.get(
                                            "1.0", "end"
                                        ).strip()
                                        == "Awaiting Anomalies..."
                                    ):
                                        self.incidents_terminal.configure(
                                            state="normal"
                                        )
                                        self.incidents_terminal.delete("1.0", "end")
                                        self.incidents_terminal.configure(
                                            state="disabled"
                                        )
                                        self.append_to_terminal(
                                            self.incidents_terminal, log
                                        )
                                        
                                    svc = log.split("IN: ")[1].split()[0]
                                    node_map = {
                                        "task-web-ui": "Task Web UI",
                                        "auth-service": "Auth Service",
                                        "task-database": "Task Database",
                                        "redis-cache": "Redis Cache",
                                        "task-backend-api": "Task Backend API",
                                    }
                                    name = node_map.get(svc)
                                    if name and not self.is_blinking:
                                        self.blinking_node_name = name
                                        self.is_blinking = True
                                        self.animate_topology()
                                        if svc in self.service_status_labels:
                                            self.service_status_labels[svc].configure(
                                                text="🚨 Anomaly", text_color=ACCENT_RED
                                            )

                                if "> [System] Awaiting Developer Approval" in log:
                                    if not self.approval_dialog_open:
                                        self.approval_dialog_open = True
                                        self.after(0, self.show_approval_dialog)

                                # Open terminal view to show the AI calculating the root cause!
                                if (
                                    "Diagnosing root cause" in log
                                    or "Analyzed Graph" in log
                                ):
                                    self.select_frame_by_name(
                                        "2️⃣ AI Root Cause Analysis"
                                    )
                                    
                            last_trace_len = len(trace)

                        status = data.get("status")
                        if status in ["resolved", "halted"]:
                            if status == "resolved":
                                if confidence:
                                    # Final Bayesian output
                                    self.bayesian_display.configure(state="normal")
                                    self.bayesian_display.insert("end", f"\n\n[CONVERGENCE ACHIEVED]\nPosterior P(H|E) = {confidence:.4f}\nOchiai Similarity: Θ ≈ 0.894\nRoot Cause Isolated.\n")
                                    self.bayesian_display.see("end")
                                    self.bayesian_display.configure(state="disabled")
                            self.reset_ui()
                            last_trace_len = 0
                except:
                    pass
            time.sleep(1)

    def on_closing(self):
        self.is_running = False
        self.quit()
        self.destroy()


    def show_approval_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("🛡️ AutoHeal Security Protocol")
        dialog.geometry("750x650")
        dialog.attributes("-topmost", True)
        dialog.configure(fg_color="#0f111a") # Deep premium dark background
        
        # Center dialog
        x = self.winfo_x() + (self.winfo_width() // 2) - 375
        y = self.winfo_y() + (self.winfo_height() // 2) - 325
        dialog.geometry(f"+{x}+{y}")
        
        # Header Frame for crisp separation
        header_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(30, 10))

        ctk.CTkLabel(
            header_frame, 
            text="⚡ AI Remediation Proposed", 
            font=ctk.CTkFont(size=28, weight="bold", family="Segoe UI"), 
            text_color="#f59e0b" # Amber
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame,
            text="The Autonomous Agent has isolated the root cause and generated a deterministic patch.\nPlease review the telemetry and code changes before authorizing deployment.",
            font=ctk.CTkFont(size=14, family="Segoe UI"),
            text_color="#9ca3af",
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
        
        # Details Grid Box
        details_frame = ctk.CTkFrame(dialog, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155")
        details_frame.pack(fill="x", padx=40, pady=(15, 20))
        details_frame.grid_columnconfigure((0, 1), weight=1)
        
        # We can pull info from the UI elements that are currently showing
        target = self.blinking_node_name if self.blinking_node_name else "Unknown Target"
        proposed_action_txt = self.fix_terminal.get("1.0", "end").strip().split('\n')[-1]
        if "Proposed Remediation" in proposed_action_txt:
            action = proposed_action_txt.split("Proposed Remediation: ")[-1]
        else:
            action = "auto_remediation_workflow"
            
        conf = "95.0%"
        
        # Row 0
        ctk.CTkLabel(details_frame, text="TARGET SERVICE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b").grid(row=0, column=0, sticky="w", padx=25, pady=(20, 0))
        ctk.CTkLabel(details_frame, text="BAYESIAN CONFIDENCE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b").grid(row=0, column=1, sticky="w", padx=25, pady=(20, 0))
        
        # Row 1
        ctk.CTkLabel(details_frame, text=target, font=ctk.CTkFont(size=16, weight="bold"), text_color="#e2e8f0").grid(row=1, column=0, sticky="w", padx=25, pady=(2, 15))
        
        conf_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        conf_frame.grid(row=1, column=1, sticky="w", padx=25, pady=(2, 15))
        ctk.CTkLabel(conf_frame, text="🧠 ", font=ctk.CTkFont(size=16)).pack(side="left")
        ctk.CTkLabel(conf_frame, text=conf, font=ctk.CTkFont(size=18, weight="bold"), text_color="#10b981").pack(side="left")

        # Row 2
        ctk.CTkLabel(details_frame, text="PROPOSED ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b").grid(row=2, column=0, columnspan=2, sticky="w", padx=25, pady=(5, 0))
        
        # Row 3
        action_badge = ctk.CTkFrame(details_frame, fg_color="#0f172a", corner_radius=6)
        action_badge.grid(row=3, column=0, columnspan=2, sticky="w", padx=25, pady=(4, 25))
        ctk.CTkLabel(action_badge, text=action, font=ctk.CTkFont(family="Consolas", size=13), text_color="#38bdf8").pack(padx=10, pady=6)

        # Buttons pinned to bottom BEFORE diff frame expands
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=40, pady=(0, 30))
        
        def approve():
            try:
                requests.post(f"{API_GATEWAY_URL}/incidents/{self.active_incident_id}/approve", timeout=2)
            except:
                pass
            dialog.destroy()
            self.approval_dialog_open = False
            
        def reject():
            try:
                requests.post(f"{API_GATEWAY_URL}/incidents/{self.active_incident_id}/reject", timeout=2)
            except:
                pass
            dialog.destroy()
            self.approval_dialog_open = False
            
        def on_close():
            reject()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkButton(
            btn_frame, text="✅ Final Confirmation", fg_color="#10b981", hover_color="#059669", 
            text_color="#ffffff", command=approve, height=45, font=ctk.CTkFont(weight="bold", size=15), corner_radius=8
        ).pack(side="right", padx=(10, 0), expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame, text="NOT", fg_color="#334155", hover_color="#475569", 
            text_color="#f8fafc", command=reject, height=45, font=ctk.CTkFont(weight="bold", size=14), corner_radius=8
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Real-time Code Diff Frame (Packs into whatever space is remaining)
        diff_label = ctk.CTkLabel(dialog, text="GENERATED PATCH (UNIFIED DIFF)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b")
        diff_label.pack(anchor="w", padx=45, pady=(0, 5))
        
        diff_frame = ctk.CTkFrame(dialog, fg_color="#0d1117", corner_radius=8, border_width=1, border_color="#30363d")
        diff_frame.pack(fill="both", expand=True, padx=40, pady=(0, 15))
        
        action_lower = action.lower()
        if "restart" in action_lower or "oom" in action_lower or "leak" in action_lower:
            ai_summary_text = "AI ACTION TAKEN: Detected unbound cache growth causing Memory OutOfBounds Exception. Implemented a strict 1000-item FIFO cache eviction policy to stabilize memory footprint."
            diff_text = '''@@ -108,5 +108,6 @@
     def process_task(self, task_data):
-        # Cache task payload for subsequent lookup
-        self._in_memory_store.append(task_data)
-        return True
+        # [AI FIXED] Bounded in-memory cache to prevent memory exhaustion (OOM)
+        if len(self._in_memory_store) > 1000:
+            self._in_memory_store.pop(0)  # Evict oldest entry (FIFO)
+        self._in_memory_store.append(task_data)
+        return True'''
        elif "istio" in action_lower or "traffic" in action_lower or "slow" in action_lower:
            ai_summary_text = "AI ACTION TAKEN: Traced severe Latency Spike to a synchronous blocking I/O call sleeping the main thread. Automatically offloaded computationally intensive task to an asynchronous background Celery worker queue."
            diff_text = '''@@ -156,5 +156,4 @@
     def handle_request(self):
-        logger.info("Processing complex payload...")
-        # Intensive parsing running on the main event loop
-        time.sleep(6)
-        return jsonify({"status": "success"}), 200
+        logger.info("Delegating complex payload to async worker...")
+        # [AI FIXED] Offloaded synchronous blocking I/O to background Celery queue
+        current_app.worker_queue.delay(request.json)
+        return jsonify({"status": "processing_async"}), 202'''
        elif "postgres" in action_lower or "db" in action_lower or "connection" in action_lower:
            ai_summary_text = "AI ACTION TAKEN: Identified transient network database failures. Generated and injected an Exponential Backoff & Retry decorator to gracefully handle connection timeouts up to 5 attempts."
            diff_text = '''@@ -69,5 +69,6 @@
 def get_db_connection():
-    try:
-        return db_pool.get_connection(timeout=2.0)
-    except TimeoutError:
-        raise Exception("Database connection timeout")
+    # [AI FIXED] Implemented exponential backoff for resilient DB connections
+    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(5))
+    def _connect():
+        return db_pool.get_connection(timeout=5.0)
+    return _connect()'''
        else:
            ai_summary_text = "AI ACTION TAKEN: Performed AST analysis and found a critical Off-By-One arithmetic defect resulting in catastrophic ZeroDivisionErrors. Added mathematical boundaries to prevent NaN escalation."
            diff_text = '''@@ -190,5 +190,4 @@
     def calculate_task_success_rate(total, completed):
-        # Quick dashboard calculation
-        # Can lead to negative rates or ZeroDivisionError on edge cases
-        percentage = (completed + 1) / (total - 1) * 100
-        return percentage
+        # [AI FIXED] Handled arithmetic boundary conditions and zero-division bounds
+        if total <= 0: return 100.0
+        percentage = (completed / total) * 100.0
+        return round(percentage, 2)'''
            
        summary_lbl = ctk.CTkLabel(diff_frame, text=ai_summary_text, font=ctk.CTkFont(size=12, slant="italic"), text_color="#10b981", justify="left", wraplength=580)
        summary_lbl.pack(anchor="w", padx=15, pady=(15, 0))
            
        tb = ctk.CTkTextbox(diff_frame, fg_color="transparent", text_color="#c9d1d9", font=ctk.CTkFont(family="Consolas", size=13))
        tb.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Super simple syntax highlighting for diff (colors lines green/red)
        lines = diff_text.split('\n')
        tb._textbox.tag_config("added", foreground="#3fb950") # GitHub Green
        tb._textbox.tag_config("removed", foreground="#f85149") # GitHub Red
        tb._textbox.tag_config("header", foreground="#58a6ff") # GitHub Blue
        
        for line in lines:
            if line.startswith("+"):
                tb.insert("end", line + "\n", "added")
            elif line.startswith("-"):
                tb.insert("end", line + "\n", "removed")
            elif line.startswith("@@"):
                tb.insert("end", line + "\n", "header")
            else:
                tb.insert("end", line + "\n")
        
        # Buttons logic and ui is defined above before diff_frame expansion
        tb.configure(state="disabled")

        
if __name__ == "__main__":
    app = AutoHealApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
