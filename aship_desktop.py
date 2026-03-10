import customtkinter as ctk
import requests
import threading
import time

API_GATEWAY_URL = "http://localhost:8000/v1"

# Aesthetically matching the provided React web app screenshot
BG_COLOR = "#0f1115"
SIDEBAR_BG = "#13151a"
CARD_BG = "#181a20"
BORDER_COLOR = "#222630"
TEXT_MAIN = "#f8fafc"
TEXT_MUTED = "#94a3b8"

ACCENT_BLUE = "#3b82f6"
ACCENT_GREEN = "#10b981"
ACCENT_RED = "#f43f5e"
ACCENT_ORANGE = "#f59e0b"
ACCENT_PURPLE = "#8b5cf6"

ACTIVE_BG = "#1e1b4b" # The purple-ish active sidebar background
ACTIVE_TEXT = "#e0e7ff"

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
        
        # Keep track of nav buttons to restyle them
        self.nav_buttons = {}

        # ----------------------------------------------------
        # Sidebar
        # ----------------------------------------------------
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=SIDEBAR_BG, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)
        
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=24, pady=(28, 32), sticky="w")
        
        shield_lbl = ctk.CTkLabel(logo_frame, text="🛡️", font=ctk.CTkFont(size=28), text_color=ACCENT_PURPLE)
        shield_lbl.pack(side="left", padx=(0,12))
        
        title_box = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="AutoHeal AI", font=ctk.CTkFont(size=20, weight="bold", family="Inter"), text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Autonomous DevOps", font=ctk.CTkFont(size=12, family="Inter"), text_color=TEXT_MUTED).pack(anchor="w")

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
        ctk.CTkLabel(status_box, text="🔌 Reconnecting...", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(status_box, text="⚡ Engine Active", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w")

        # ----------------------------------------------------
        # Main Content Frames Container
        # ----------------------------------------------------
        self.main_frame_container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_frame_container.grid(row=0, column=1, sticky="nsew", padx=40, pady=32)
        self.main_frame_container.grid_columnconfigure(0, weight=1)
        self.main_frame_container.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # Dashboard Frame
        # ----------------------------------------------------
        self.dashboard_frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        self.dashboard_frame.grid_columnconfigure(0, weight=7)  # Topology
        self.dashboard_frame.grid_columnconfigure(1, weight=3)  # Inject Fault
        self.dashboard_frame.grid_rowconfigure(2, weight=1)
        self.dashboard_frame.grid_rowconfigure(3, weight=2) # Trace space

        # Header
        header_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="System Dashboard", font=ctk.CTkFont(family="Inter", size=28, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Real-time infrastructure monitoring & self-healing", font=ctk.CTkFont(family="Inter", size=14), text_color=TEXT_MUTED).pack(anchor="w")
        
        ctk.CTkLabel(header_frame, text="🟢 Passive Log Monitoring Active", text_color=ACCENT_GREEN, font=ctk.CTkFont(size=14, weight="bold")).pack(side="right")

        # ----------------------------------------------------
        # Stats Row
        # ----------------------------------------------------
        stats_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 24))
        stats_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        self.stat_components = {}
        self.add_stat_card(stats_frame, 0, "⊞", "2", "Total Services", ACCENT_BLUE)
        self.stat_components['healthy'] = self.add_stat_card(stats_frame, 1, "🛡️", "2", "Healthy", ACCENT_GREEN)
        self.stat_components['incidents'] = self.add_stat_card(stats_frame, 2, "⚠", "0", "Active Incidents", ACCENT_RED)
        self.add_stat_card(stats_frame, 3, "⏱", "12s", "Avg MTTR", ACCENT_ORANGE)
        self.add_stat_card(stats_frame, 4, "⚡", "100%", "Auto-Heal Rate", ACCENT_PURPLE)
        self.add_stat_card(stats_frame, 5, "📈", "100%", "Uptime", ACCENT_BLUE)

        # ----------------------------------------------------
        # Service Topology (Left Panel)
        # ----------------------------------------------------
        topology_frame = ctk.CTkFrame(self.dashboard_frame, fg_color=CARD_BG, border_color=BORDER_COLOR, border_width=1, corner_radius=12)
        topology_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 20))
        
        ctk.CTkLabel(topology_frame, text="⊞ Service Topology", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=24, pady=(24, 10))
        
        # Canvas for graph
        self.topology_canvas = ctk.CTkCanvas(topology_frame, bg=CARD_BG, highlightthickness=0)
        self.topology_canvas.pack(fill="both", expand=True, padx=20, pady=(0,20))
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
        
        ctk.CTkLabel(fault_frame, text="🐛 Fault Injection", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", pady=(0,4))
        ctk.CTkLabel(fault_frame, text="Inject faults to test self-healing capabilities", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(anchor="w", pady=(0,24))

        ctk.CTkLabel(fault_frame, text="Target Service", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(anchor="w")
        self.target_service = ctk.CTkOptionMenu(fault_frame, values=["api-gateway", "auth-service", "prod-billing-db", "redis-cache", "kafka-eventbus"], fg_color=CARD_BG, button_color=CARD_BG, button_hover_color=BORDER_COLOR, text_color=TEXT_MAIN, dropdown_fg_color=CARD_BG, height=40, corner_radius=8)
        self.target_service.pack(fill="x", pady=(8, 20))

        ctk.CTkLabel(fault_frame, text="Fault Type", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(anchor="w")
        
        real_world_bugs = [
            # Infrastructure & Resources
            "Memory Leak (OOM Kill)", 
            "CPU Spike (100% Load)", 
            "Disk Space Exhaustion (100% Full)",
            # Networking & Connectivity
            "Network Latency (5000ms+)", 
            "DNS Resolution Failure", 
            "BGP Route Flapping",
            "TCP Connection Refused (Port Blocked)",
            # Database & State
            "DB Connection Pool Exhaustion", 
            "Deadlock / Row Lock Timeout", 
            "Redis Cache Eviction Storm",
            "Kafka Partition Leader Election Failure",
            # Security & Auth
            "Expired TLS Certificate", 
            "OAuth Token Validation Failure", 
            "IAM Missing Permissions (Access Denied)",
            # App Layer
            "Null Pointer Exception Mapping", 
            "Goroutine Leak (Thread Starvation)",
            "Third-Party API Rate Limit Exceeded"
        ]
        
        self.fault_type = ctk.CTkOptionMenu(fault_frame, values=real_world_bugs, fg_color=CARD_BG, button_color=CARD_BG, button_hover_color=BORDER_COLOR, text_color=TEXT_MAIN, dropdown_fg_color=CARD_BG, height=40, corner_radius=8)
        self.fault_type.pack(fill="x", pady=(8, 24))

        self.inject_btn = ctk.CTkButton(fault_frame, text="⚡ Inject Fault", command=self.trigger_alert, fg_color="#3f1d24", hover_color="#4c1d2a", text_color=ACCENT_RED, height=44, corner_radius=8, font=ctk.CTkFont(family="Inter", weight="bold", size=14))
        self.inject_btn.pack(fill="x")

        # ----------------------------------------------------
        # Recent Activity (Bottom Row, spans both columns)
        # Ensuring it has enough space as requested
        # ----------------------------------------------------
        trace_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        trace_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(24, 0))
        trace_frame.grid_rowconfigure(1, weight=1)
        trace_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(trace_frame, text="Recent Activity", font=ctk.CTkFont(family="Inter", size=16, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0, 12))
        
        self.textbox = ctk.CTkTextbox(trace_frame, fg_color=CARD_BG, text_color=TEXT_MUTED, font=ctk.CTkFont(family="Consolas", size=13), wrap="word", corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.textbox.grid(row=1, column=0, sticky="nsew")
        self.textbox.insert("end", "No incidents yet. Inject a fault to see the magic!\n")
        self.textbox.configure(state="disabled")

        # start monitor loop
        threading.Thread(target=self.poll_agent, daemon=True).start()
        
        # Secondary Frames mapped to pitch
        self.services_frame = self.build_services_frame() # Used for Topology
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
            "5️⃣ Self-Healing Deployment": self.self_healing_frame
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
        # Shift the center slightly up to perfectly center the 3-layer tree
        cx, cy = 350, 160
        nodes = [
            ("API Gateway", cx, cy-95, ACCENT_BLUE, "🌐"),
            ("Auth Service", cx-180, cy, ACCENT_GREEN, "🔐"),
            ("Billing DB", cx+180, cy, ACCENT_GREEN, "💾"),
            ("Redis Cache", cx-180, cy+115, ACCENT_GREEN, "⚡"),
            ("Kafka EventBus", cx, cy+115, ACCENT_ORANGE, "📨")
        ]
        
        edges = [(0, 1), (0, 2), (1, 3), (2, 4), (1, 4), (0, 4)]
        
        tick = getattr(self, "animation_tick", 0)
        
        # Draw edges and traffic with Bezier curves
        for (i, j) in edges:
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
                qx = (1-t)**2 * x1 + 2*(1-t)*t * cx_bezier + t**2 * x2
                qy = (1-t)**2 * y1 + 2*(1-t)*t * cy_bezier + t**2 * y2
                self.topology_canvas.create_line(prev_x, prev_y, qx, qy, fill="#2a3241", width=2)
                prev_x, prev_y = qx, qy
            
            # Draw moving particle along the true curve
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist > 0:
                progress = ((tick + i*15 + j*10) % 100) / 100.0
                px = (1-progress)**2 * x1 + 2*(1-progress)*progress * cx_bezier + progress**2 * x2
                py = (1-progress)**2 * y1 + 2*(1-progress)*progress * cy_bezier + progress**2 * y2
                
                # Neon cyan leading particle with trail
                self.topology_canvas.create_oval(px-6, py-6, px+6, py+6, fill="", outline="#00f2fe", width=1)
                self.topology_canvas.create_oval(px-3, py-3, px+3, py+3, fill="#00f2fe", outline="")
                
                # Reverse particle (bidirectional traffic) magenta
                progress2 = ((tick + j*15 + i*10) % 100) / 100.0
                px2 = (1-progress2)**2 * x1 + 2*(1-progress2)*progress2 * cx_bezier + progress2**2 * x2
                py2 = (1-progress2)**2 * y1 + 2*(1-progress2)*progress2 * cy_bezier + progress2**2 * y2
                
                self.topology_canvas.create_oval(px2-6, py2-6, px2+6, py2+6, fill="", outline="#fe0979", width=1)
                self.topology_canvas.create_oval(px2-3, py2-3, px2+3, py2+3, fill="#fe0979", outline="")            
        r_w, r_h = 75, 28
        for idx, (name, x, y, color, icon) in enumerate(nodes):
            is_target = getattr(self, "is_blinking", False) and name == getattr(self, "blinking_node_name", None)
            
            if is_target:
                fill_color = ACCENT_RED if getattr(self, "blink_state", False) else BG_COLOR
                outline_color = ACCENT_RED
                # Draw aggressive glowing aura
                self.topology_canvas.create_rectangle(x-r_w-8, y-r_h-8, x+r_w+8, y+r_h+8, fill="", outline=ACCENT_RED, width=2, dash=(2, 4))
                self.topology_canvas.create_rectangle(x-r_w-4, y-r_h-4, x+r_w+4, y+r_h+4, fill="", outline=ACCENT_RED, width=1)
            else:
                fill_color = "#0a0c10" # Deep dark node core
                outline_color = color
                
            # Smartscape pseudo-3D shadow
            self.topology_canvas.create_rectangle(x-r_w+2, y-r_h+4, x+r_w+2, y+r_h+4, fill="#000000", outline="")
            
            # Main Node
            self.topology_canvas.create_rectangle(x-r_w, y-r_h, x+r_w, y+r_h, fill=fill_color, outline=outline_color, width=2)
            self.topology_canvas.create_text(x, y, text=f"{icon} {name}", fill=TEXT_MAIN, font=("Inter", 12, "bold"))
            
            # Live Metrics Badge (Dynatrace Style)
            metric_val = ["12ms", "99.9%", "4ms", "20k/s", "1msg/s"][idx]
            metric_color = ACCENT_GREEN if not is_target else ACCENT_RED
            self.topology_canvas.create_rectangle(x+r_w-20, y-r_h-12, x+r_w+25, y-r_h+4, fill="#12161f", outline=metric_color, width=1)
            self.topology_canvas.create_text(x+r_w+2, y-r_h-4, text=metric_val, fill=metric_color, font=("Consolas", 9, "bold"))
    def build_services_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=12)
        ctk.CTkLabel(header, text="⚙ Service Registry", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).pack(side="left", padx=24)

        table = ctk.CTkScrollableFrame(frame, fg_color=CARD_BG, border_color=BORDER_COLOR, border_width=1, corner_radius=12)
        table.grid(row=1, column=0, sticky="nsew")
        table.grid_columnconfigure((0,1,2,3), weight=1)

        for col, txt in enumerate(["SERVICE NAME", "NAMESPACE", "STATUS", "UPTIME"]):
            ctk.CTkLabel(table, text=txt, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).grid(row=0, column=col, sticky="w", padx=24, pady=16)

        data = [
            ("api-gateway", "production", "✅ Healthy", "42d 11h"),
            ("auth-service", "production", "✅ Healthy", "42d 11h"),
            ("prod-billing-db", "production", "✅ Healthy", "14d 2h"),
        ]
        
        self.service_status_labels = {}
        for row, (name, ns, status, uptime) in enumerate(data, start=1):
            ctk.CTkLabel(table, text=name, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_MAIN).grid(row=row, column=0, sticky="w", padx=24, pady=12)
            ctk.CTkLabel(table, text=ns, font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).grid(row=row, column=1, sticky="w", padx=24, pady=12)
            slbl = ctk.CTkLabel(table, text=status, font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_GREEN)
            slbl.grid(row=row, column=2, sticky="w", padx=24, pady=12)
            self.service_status_labels[name] = slbl
            ctk.CTkLabel(table, text=uptime, font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).grid(row=row, column=3, sticky="w", padx=24, pady=12)

        return frame

    def build_incidents_frame(self):
        # Similar clean layout for incidents
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=12)
        ctk.CTkLabel(header, text="⚠ Incident Audit Log", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).pack(side="left", padx=24)
        
        table = ctk.CTkScrollableFrame(frame, fg_color=CARD_BG, border_color=BORDER_COLOR, border_width=1, corner_radius=12)
        table.grid(row=1, column=0, sticky="nsew")
        self.incidents_table = table
        
        self.incidents_terminal = ctk.CTkTextbox(table, fg_color=SIDEBAR_BG, text_color=ACCENT_RED, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=0, border_width=0)
        self.incidents_terminal.pack(fill="both", expand=True)
        self.incidents_terminal.insert("end", "Awaiting Anomalies...\n")
        self.incidents_terminal.configure(state="disabled")
        
        return frame

    def build_terminal_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(frame, text="Live Terminal (Real-time AI Tracing)", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0,20))

        self.full_terminal = ctk.CTkTextbox(frame, fg_color=SIDEBAR_BG, text_color=ACCENT_GREEN, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.full_terminal.grid(row=1, column=0, sticky="nsew")
        self.full_terminal.insert("end", "[System] Live terminal connected. Awaiting autonomous actions...\n")
        self.full_terminal.configure(state="disabled")
        return frame

    def build_fix_suggestion_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(frame, text="💡 Intelligent Fix Suggestion", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0,20))
        self.fix_terminal = ctk.CTkTextbox(frame, fg_color=SIDEBAR_BG, text_color=ACCENT_PURPLE, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.fix_terminal.grid(row=1, column=0, sticky="nsew")
        self.fix_terminal.insert("end", "Waiting for AI to generate patches...\n")
        self.fix_terminal.configure(state="disabled")
        return frame

    def build_sandbox_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(frame, text="🧪 Sandbox Testing Environment", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0,20))
        self.sandbox_terminal = ctk.CTkTextbox(frame, fg_color=SIDEBAR_BG, text_color=ACCENT_ORANGE, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.sandbox_terminal.grid(row=1, column=0, sticky="nsew")
        self.sandbox_terminal.insert("end", "Waiting for code to enter isolated Sandbox...\n")
        self.sandbox_terminal.configure(state="disabled")
        return frame

    def build_self_healing_frame(self):
        frame = ctk.CTkFrame(self.main_frame_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(frame, text="🩹 Self-Healing Deployment", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0,20))
        self.healing_terminal = ctk.CTkTextbox(frame, fg_color=SIDEBAR_BG, text_color=ACCENT_GREEN, font=ctk.CTkFont(family="Consolas", size=14), wrap="word", corner_radius=12, border_color=BORDER_COLOR, border_width=1)
        self.healing_terminal.grid(row=1, column=0, sticky="nsew")
        self.healing_terminal.insert("end", "Waiting to deploy patches to production...\n")
        self.healing_terminal.configure(state="disabled")
        return frame

    def select_frame_by_name(self, name):
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=ACTIVE_BG, text_color=ACTIVE_TEXT, corner_radius=8)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED, corner_radius=8)
        
        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

    def add_nav_item(self, row, icon, text):
        btn = ctk.CTkButton(self.sidebar_frame, text=f"  {icon}    {text}", anchor="w", fg_color="transparent", hover_color=ACTIVE_BG, text_color=TEXT_MUTED, font=ctk.CTkFont(size=14, weight="bold", family="Inter"), height=44, command=lambda: self.select_frame_by_name(text))
        btn.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
        self.nav_buttons[text] = btn

    def add_stat_card(self, parent, col, icon, value, label, icon_color="white"):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, border_color=BORDER_COLOR, border_width=1, corner_radius=12)
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(anchor="w", fill="x", padx=16, pady=(16, 8))
        
        # Draw icon inside a very faint tinted circle
        icon_bg = ctk.CTkFrame(top_frame, fg_color="#1e293b", corner_radius=8, width=32, height=32)
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon, font=ctk.CTkFont(size=16), text_color=icon_color).place(relx=0.5, rely=0.5, anchor="center")
        
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold", family="Inter"), text_color=TEXT_MAIN)
        lbl_val.pack(anchor="w", padx=16)
        
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=13, family="Inter"), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 16))
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
            "api-gateway": "API Gateway",
            "auth-service": "Auth Service",
            "prod-billing-db": "Billing DB",
            "redis-cache": "Redis Cache",
            "kafka-eventbus": "Kafka EventBus"
        }
        self.blinking_node_name = node_map.get(target, "")
        if self.blinking_node_name:
            self.is_blinking = True
            self.animate_topology()
        
        self.inject_btn.configure(state="disabled", text="Incident Active...", fg_color=CARD_BG)
        self.stat_components['healthy'].configure(text="1", text_color=ACCENT_RED)
        self.stat_components['incidents'].configure(text="1", text_color=ACCENT_RED)
        if target in self.service_status_labels:
            self.service_status_labels[target].configure(text="🚨 Anomaly", text_color=ACCENT_RED)

        self.log_message(f"", clear=True)
        self.log_message(f"> Injecting {f_type} into {target}...", clear=True)

        payload = {
            "status": "firing",
            "alerts": [{"labels": {"job": target, "severity": "critical", "type": f_type}, "startsAt": str(time.time())}]
        }
        try:
            res = requests.post(f"{API_GATEWAY_URL}/alerts/webhook", json=payload, timeout=2)
            if res.status_code == 200:
                self.active_incident_id = res.json()['incident_id']
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
        
        self.inject_btn.configure(state="normal", text="⚡ Inject Fault", fg_color="#3f1d24")
        self.stat_components['healthy'].configure(text="2", text_color=TEXT_MAIN)
        self.stat_components['incidents'].configure(text="0", text_color=TEXT_MAIN)
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
                            self.log_message(f"[System] 🚨 AI Gateway caught live outlier: Incident {new_id}")
                            self.inject_btn.configure(state="disabled", text="Incident Active...", fg_color=CARD_BG)
                            self.stat_components['healthy'].configure(text="1", text_color=ACCENT_RED)
                            self.stat_components['incidents'].configure(text="1", text_color=ACCENT_RED)
                except Exception:
                    pass

            if self.active_incident_id:
                try:
                    res = requests.get(f"{API_GATEWAY_URL}/incidents/{self.active_incident_id}", timeout=2)
                    if res.status_code == 200:
                        data = res.json()
                        trace = data.get("trace", [])
                        
                        if len(trace) > last_trace_len:
                            for log in trace[last_trace_len:]:
                                self.log_message(log)
                                
                                # Route to 1st Task Bar: Bug Detection 
                                self.append_to_terminal(self.incidents_terminal, log)
                                
                                # Route to 3rd Task Bar: Intelligent Fix
                                if "Proposed Fix" in log or "Confidence" in log or "REJECTED" in log:
                                    if self.fix_terminal.get("1.0", "end").strip() == "Waiting for AI to generate patches...":
                                        self.fix_terminal.configure(state="normal")
                                        self.fix_terminal.delete("1.0", "end")
                                        self.fix_terminal.configure(state="disabled")
                                    self.append_to_terminal(self.fix_terminal, log)
                                    self.select_frame_by_name("3️⃣ Intelligent Fix Suggestion")

                                # Route to 4th Task Bar: Sandbox
                                if "Policy Engine" in log or "OPA" in log or "Sandboxing" in log:
                                    if self.sandbox_terminal.get("1.0", "end").strip() == "Waiting for code to enter isolated Sandbox...":
                                        self.sandbox_terminal.configure(state="normal")
                                        self.sandbox_terminal.delete("1.0", "end")
                                        self.sandbox_terminal.configure(state="disabled")
                                    self.append_to_terminal(self.sandbox_terminal, log)
                                    self.select_frame_by_name("4️⃣ Sandbox Testing Environment")

                                # Route to 5th Task Bar: Self Healing
                                if "GitOps" in log or "SUCCESS" in log or "FAILED" in log:
                                    if self.healing_terminal.get("1.0", "end").strip() == "Waiting to deploy patches to production...":
                                        self.healing_terminal.configure(state="normal")
                                        self.healing_terminal.delete("1.0", "end")
                                        self.healing_terminal.configure(state="disabled")
                                    self.append_to_terminal(self.healing_terminal, log)
                                    self.select_frame_by_name("5️⃣ Self-Healing Deployment")
                                
                                # Hacky way to animate the node if the trace mentions it
                                if "DETECTED CRITICAL FAULT IN: " in log:
                                    if self.incidents_terminal.get("1.0", "end").strip() == "Awaiting Anomalies...":
                                        self.incidents_terminal.configure(state="normal")
                                        self.incidents_terminal.delete("1.0", "end")
                                        self.incidents_terminal.configure(state="disabled")
                                        self.append_to_terminal(self.incidents_terminal, log)

                                    svc = log.split("IN: ")[1].split()[0]
                                    node_map = {
                                        "api-gateway": "API Gateway",
                                        "auth-service": "Auth Service",
                                        "prod-billing-db": "Billing DB",
                                        "redis-cache": "Redis Cache",
                                        "kafka-eventbus": "Kafka EventBus"
                                    }
                                    name = node_map.get(svc)
                                    if name and not self.is_blinking:
                                        self.blinking_node_name = name
                                        self.is_blinking = True
                                        self.animate_topology()
                                        if svc in self.service_status_labels:
                                            self.service_status_labels[svc].configure(text="🚨 Anomaly", text_color=ACCENT_RED)
                                            
                                # Open terminal view to show the AI calculating the root cause!
                                if "Diagnosing root cause" in log or "Analyzed Graph" in log:
                                    self.select_frame_by_name("2️⃣ AI Root Cause Analysis")

                        status = data.get("status")
                        if status in ["resolved", "halted"]:
                            self.reset_ui()
                            last_trace_len = 0
                except:
                    pass
            time.sleep(1)

    def on_closing(self):
        self.is_running = False
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = AutoHealApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
