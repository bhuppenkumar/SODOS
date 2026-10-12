import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import ImageTk
from app import core

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SODOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SODOS - Secure Offline Document Optimization System")
        self.geometry("750x750")
        self.resizable(False, False)

        # Application State Variables
        self.current_mode = None
        self.selected_files = []
        self.base_preview_items = []  # List of PIL images or metadata tuples
        self.tk_preview_imgs = []
        self.preview_widgets = []
        self.page_rotations = {}
        self.deleted_pages = set()

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)

        self.show_home_screen()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def toggle_theme(self, value):
        ctk.set_appearance_mode("Dark" if value else "Light")

    # ------------------ HOME SCREEN ------------------
    def show_home_screen(self):
        self.clear_container()

        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(header, text="SODOS Utility Hub", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left")

        theme_switch = ctk.CTkSwitch(header, text="Dark Mode", command=lambda: self.toggle_theme(theme_switch.get()))
        theme_switch.select()
        theme_switch.pack(side="right")

        sub_label = ctk.CTkLabel(
            self.main_container, text="Select an offline tool to get started:", font=ctk.CTkFont(size=13)
        )
        sub_label.pack(pady=(0, 15))

        grid = ctk.CTkFrame(self.main_container, fg_color="transparent")
        grid.pack(pady=5)

        btn_specs = [
            ("📄 Compress PDF", "COMPRESS_PDF", 0, 0),
            ("🖼️ Compress Image", "COMPRESS_IMG", 0, 1),
            ("📑 Merge PDFs", "MERGE_PDF", 1, 0),
            ("✂️ Split PDF Range", "SPLIT_PDF", 1, 1),
            ("🖼️➡️📄 Images to PDF", "IMG_TO_PDF", 2, 0),
            ("📄➡️🖼️ PDF to Images", "PDF_TO_IMG", 2, 1),
            ("🔒 Password Protect PDF", "ENCRYPT_PDF", 3, 0)
        ]

        for text, mode, r, c in btn_specs:
            btn = ctk.CTkButton(
                grid, text=text, font=ctk.CTkFont(size=14, weight="bold"),
                width=290, height=70, command=lambda m=mode: self.start_workflow(m)
            )
            btn.grid(row=r, column=c, padx=12, pady=10)

        status = ctk.CTkLabel(self.main_container, text="100% Offline • Live Multi-Page Previews • Auto Metadata Stripping", font=ctk.CTkFont(size=11))
        status.pack(side="bottom", pady=12)

    # ------------------ WORKFLOW SCREEN ------------------
    def start_workflow(self, mode):
        self.current_mode = mode
        self.selected_files = []
        self.base_preview_items = []
        self.tk_preview_imgs = []
        self.preview_widgets = []
        self.page_rotations = {}
        self.deleted_pages = set()
        self.clear_container()

        top_bar = ctk.CTkFrame(self.main_container, height=45)
        top_bar.pack(fill="x", padx=10, pady=10)

        back_btn = ctk.CTkButton(top_bar, text="← Home", width=70, command=self.show_home_screen)
        back_btn.pack(side="left", padx=10, pady=5)

        titles = {
            "COMPRESS_PDF": "Compress PDF Document",
            "COMPRESS_IMG": "Compress Image File",
            "MERGE_PDF": "Merge Multiple PDFs",
            "SPLIT_PDF": "Split / Extract PDF Pages",
            "IMG_TO_PDF": "Convert Images to PDF",
            "PDF_TO_IMG": "Extract PDF Pages as PNG Images",
            "ENCRYPT_PDF": "Password Protect PDF Document"
        }
        title_label = ctk.CTkLabel(top_bar, text=titles[mode], font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=15)

        self.file_frame = ctk.CTkFrame(self.main_container)
        self.file_frame.pack(fill="x", padx=20, pady=5)

        self.btn_select_file = ctk.CTkButton(self.file_frame, text="Choose File(s)", command=self.select_files)
        self.btn_select_file.pack(side="left", padx=15, pady=10)

        self.lbl_file_name = ctk.CTkLabel(self.file_frame, text="No file selected", font=ctk.CTkFont(size=12))
        self.lbl_file_name.pack(side="left", padx=10)

        self.workspace_frame = ctk.CTkFrame(self.main_container)
        self.workspace_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

    def select_files(self):
        if self.current_mode in ["COMPRESS_PDF", "SPLIT_PDF", "PDF_TO_IMG", "ENCRYPT_PDF"]:
            path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
            if path:
                self.selected_files = [path]
                size_mb = os.path.getsize(path) / (1024 * 1024)
                self.lbl_file_name.configure(text=f"{os.path.basename(path)} ({size_mb:.2f} MB)")
                self.base_preview_items = core.get_all_pdf_previews(path)
                self.build_unified_preview_workspace()

        elif self.current_mode == "COMPRESS_IMG":
            path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
            if path:
                self.selected_files = [path]
                size_mb = os.path.getsize(path) / (1024 * 1024)
                self.lbl_file_name.configure(text=f"{os.path.basename(path)} ({size_mb:.2f} MB)")
                img_preview = core.get_image_preview(path)
                self.base_preview_items = [img_preview] if img_preview else []
                self.build_unified_preview_workspace()

        elif self.current_mode == "MERGE_PDF":
            paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
            if len(paths) >= 1:
                self.selected_files = list(paths)
                self.lbl_file_name.configure(text=f"{len(paths)} PDF file(s) selected")
                # Structure: tuple of (f_idx, p_idx, fname, pil_img)
                self.base_preview_items = core.get_multiple_pdf_previews(paths)
                self.build_unified_preview_workspace()

        elif self.current_mode == "IMG_TO_PDF":
            paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png")])
            if len(paths) >= 1:
                self.selected_files = list(paths)
                self.lbl_file_name.configure(text=f"{len(paths)} image(s) selected")
                # Structure: tuple of (fname, pil_img)
                self.base_preview_items = core.get_image_previews(paths)
                self.build_unified_preview_workspace()

    # ------------------ UNIFIED PREVIEW WORKSPACE ------------------
    def build_unified_preview_workspace(self):
        for widget in self.workspace_frame.winfo_children():
            widget.destroy()

        # Left Column: Scrollable All-Page / All-File Gallery
        left_col = ctk.CTkFrame(self.workspace_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        total_count = len(self.base_preview_items)
        gallery_title = ctk.CTkLabel(left_col, text=f"Scroll Previews ({total_count} Total)", font=ctk.CTkFont(weight="bold"))
        gallery_title.pack(anchor="w", pady=(0, 5))

        self.scroll_gallery = ctk.CTkScrollableFrame(left_col, width=280)
        self.scroll_gallery.pack(fill="both", expand=True)

        # Right Column: Tool Controls
        right_col = ctk.CTkFrame(self.workspace_frame)
        right_col.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Build Tool-Specific Control Widgets
        if self.current_mode in ["COMPRESS_PDF", "COMPRESS_IMG"]:
            target_lbl = ctk.CTkLabel(right_col, text="Target File Size:", font=ctk.CTkFont(weight="bold"))
            target_lbl.pack(anchor="w", padx=10, pady=(10, 2))

            size_input_frame = ctk.CTkFrame(right_col, fg_color="transparent")
            size_input_frame.pack(fill="x", padx=10, pady=5)

            self.entry_size_val = ctk.CTkEntry(size_input_frame, width=90)
            self.entry_size_val.insert(0, "2.0")
            self.entry_size_val.pack(side="left", padx=(0, 10))

            self.unit_selector = ctk.CTkSegmentedButton(size_input_frame, values=["MB", "KB"])
            self.unit_selector.set("MB")
            self.unit_selector.pack(side="left")

            b_lbl = ctk.CTkLabel(right_col, text="Brightness:", font=ctk.CTkFont(size=12))
            b_lbl.pack(anchor="w", padx=10, pady=(12, 0))
            self.slider_b = ctk.CTkSlider(right_col, from_=0.5, to=1.8, command=lambda v: self.update_live_gallery())
            self.slider_b.set(1.0)
            self.slider_b.pack(fill="x", padx=10, pady=2)

            c_lbl = ctk.CTkLabel(right_col, text="Contrast:", font=ctk.CTkFont(size=12))
            c_lbl.pack(anchor="w", padx=10, pady=(8, 0))
            self.slider_c = ctk.CTkSlider(right_col, from_=0.5, to=2.0, command=lambda v: self.update_live_gallery())
            self.slider_c.set(1.0)
            self.slider_c.pack(fill="x", padx=10, pady=2)

            s_lbl = ctk.CTkLabel(right_col, text="Improve Sharpness:", font=ctk.CTkFont(size=12, weight="bold"))
            s_lbl.pack(anchor="w", padx=10, pady=(8, 0))
            self.slider_s = ctk.CTkSlider(right_col, from_=0.5, to=3.0, command=lambda v: self.update_live_gallery())
            self.slider_s.set(1.0)
            self.slider_s.pack(fill="x", padx=10, pady=2)

            btn_execute = ctk.CTkButton(
                right_col, text="Compress & Save As...", fg_color="green", hover_color="darkgreen",
                font=ctk.CTkFont(weight="bold"), command=self.execute_compression
            )
            btn_execute.pack(fill="x", padx=10, pady=20)

        elif self.current_mode == "SPLIT_PDF":
            range_lbl = ctk.CTkLabel(right_col, text="Enter Page Range:", font=ctk.CTkFont(weight="bold"))
            range_lbl.pack(anchor="w", padx=10, pady=(15, 2))

            hint_lbl = ctk.CTkLabel(right_col, text="Examples: '5-10' or '1, 3, 5-8'", font=ctk.CTkFont(size=11), text_color="gray")
            hint_lbl.pack(anchor="w", padx=10, pady=(0, 5))

            self.entry_range = ctk.CTkEntry(right_col, placeholder_text=f"e.g. 1-{total_count}")
            self.entry_range.insert(0, f"1-{total_count}")
            self.entry_range.pack(fill="x", padx=10, pady=5)

            self.split_mode_selector = ctk.CTkOptionMenu(
                right_col, values=["Extract Range into 1 PDF", "Split Range into Individual PDFs"]
            )
            self.split_mode_selector.pack(fill="x", padx=10, pady=15)

            btn_execute_split = ctk.CTkButton(
                right_col, text="Execute Split & Save", fg_color="green", hover_color="darkgreen",
                font=ctk.CTkFont(weight="bold"), command=self.execute_split
            )
            btn_execute_split.pack(fill="x", padx=10, pady=20)

        elif self.current_mode == "ENCRYPT_PDF":
            pass_lbl = ctk.CTkLabel(right_col, text="Enter Password to Protect PDF:", font=ctk.CTkFont(weight="bold"))
            pass_lbl.pack(anchor="w", padx=10, pady=(30, 5))

            self.entry_pass = ctk.CTkEntry(right_col, show="*", width=200)
            self.entry_pass.pack(fill="x", padx=10, pady=5)

            btn_action = ctk.CTkButton(
                right_col, text="Protect & Save PDF", fg_color="green", hover_color="darkgreen",
                font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.execute_simple_action
            )
            btn_action.pack(fill="x", padx=10, pady=30)

        else: # MERGE_PDF, IMG_TO_PDF, PDF_TO_IMG
            info_lbl = ctk.CTkLabel(
                right_col, text="Review page/file previews.\nUse 🔄 90° or 🗑️ Delete to adjust before saving.",
                font=ctk.CTkFont(size=12)
            )
            info_lbl.pack(pady=30, padx=10)

            btn_action = ctk.CTkButton(
                right_col, text="Execute & Save Destination", fg_color="green", hover_color="darkgreen",
                font=ctk.CTkFont(size=14, weight="bold"), height=42, command=self.execute_simple_action
            )
            btn_action.pack(fill="x", padx=10, pady=20)

        self.render_initial_gallery()

    def render_initial_gallery(self):
        self.preview_widgets = []
        for idx, item in enumerate(self.base_preview_items):
            card = ctk.CTkFrame(self.scroll_gallery)
            card.pack(fill="x", pady=8, padx=5)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=5, pady=2)

            # Determine title text based on data structure
            if self.current_mode == "MERGE_PDF":
                f_idx, p_idx, fname, _ = item
                label_text = f"{fname[:10]}... P.{p_idx + 1}"
            elif self.current_mode in ["IMG_TO_PDF"]:
                fname, _ = item
                label_text = f"{fname[:12]}..."
            else:
                label_text = f"Page {idx + 1}"

            p_lbl = ctk.CTkLabel(top_row, text=label_text, font=ctk.CTkFont(size=11, weight="bold"))
            p_lbl.pack(side="left")

            # Miniature Delete Icon (🗑️) + Rotate 90° (🔄) on every preview card
            btn_del = ctk.CTkButton(
                top_row, text="🗑️", width=34, fg_color="#D32F2F", hover_color="#9A0007",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda i=idx, c=card: self.delete_page(i, c)
            )
            btn_del.pack(side="right", padx=2)

            btn_rot = ctk.CTkButton(top_row, text="🔄 90°", width=48, command=lambda i=idx: self.rotate_page(i))
            btn_rot.pack(side="right", padx=2)

            img_label = ctk.CTkLabel(card, text="")
            img_label.pack(pady=4)
            self.preview_widgets.append(img_label)

        self.update_live_gallery()

    def rotate_page(self, idx):
        self.page_rotations[idx] = (self.page_rotations.get(idx, 0) + 90) % 360
        self.update_live_gallery()

    def delete_page(self, idx, card_widget):
        self.deleted_pages.add(idx)
        card_widget.destroy()

    def update_live_gallery(self):
        if not self.base_preview_items:
            return

        b = self.slider_b.get() if hasattr(self, 'slider_b') else 1.0
        c = self.slider_c.get() if hasattr(self, 'slider_c') else 1.0
        s = self.slider_s.get() if hasattr(self, 'slider_s') else 1.0
        self.tk_preview_imgs = []

        for idx, item in enumerate(self.base_preview_items):
            if idx in self.deleted_pages:
                continue

            # Extract PIL image object
            if isinstance(item, tuple):
                pil_img = item[-1]
            else:
                pil_img = item

            ang = self.page_rotations.get(idx, 0)
            mod_pil = core.apply_effects_to_preview(pil_img, brightness=b, contrast=c, sharpness=s, angle=ang)
            if mod_pil:
                tk_img = ImageTk.PhotoImage(mod_pil)
                self.tk_preview_imgs.append(tk_img)
                if idx < len(self.preview_widgets) and self.preview_widgets[idx].winfo_exists():
                    self.preview_widgets[idx].configure(image=tk_img)

    # ------------------ EXECUTION ROUTINES ------------------
    def execute_compression(self):
        try:
            val = float(self.entry_size_val.get())
            unit = self.unit_selector.get()
            target_bytes = val * (1024 * 1024) if unit == "MB" else val * 1024
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric target size.")
            return

        src_file = self.selected_files[0]
        ext = ".pdf" if self.current_mode == "COMPRESS_PDF" else ".jpg"
        out_path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(f"{ext.upper()} File", f"*{ext}")])
        if not out_path:
            return

        b = self.slider_b.get()
        c = self.slider_c.get()
        s = self.slider_s.get()
        orig_size_mb = os.path.getsize(src_file) / (1024 * 1024)

        if self.current_mode == "COMPRESS_PDF":
            core.compress_pdf_to_target(
                src_file, out_path, target_bytes, brightness=b, contrast=c, sharpness=s,
                page_rotations=self.page_rotations, deleted_pages=self.deleted_pages
            )
        else:
            ang = self.page_rotations.get(0, 0)
            core.compress_image_to_target(src_file, out_path, target_bytes, brightness=b, contrast=c, sharpness=s, angle=ang)

        new_size_mb = os.path.getsize(out_path) / (1024 * 1024)
        messagebox.showinfo("Success", f"File compressed & metadata stripped!\nOriginal: {orig_size_mb:.2f} MB\nOutput: {new_size_mb:.2f} MB")

    def execute_split(self):
        range_str = self.entry_range.get().strip()
        total_count = len(self.base_preview_items)
        page_indices = core.parse_page_ranges(range_str, total_count)

        if not page_indices:
            messagebox.showerror("Error", f"Invalid range entered. Pages are 1 to {total_count}.")
            return

        mode = self.split_mode_selector.get()
        src_file = self.selected_files[0]

        if mode == "Extract Range into 1 PDF":
            out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")])
            if out_path:
                core.extract_pdf_range(src_file, out_path, page_indices, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", f"Extracted pages into single PDF!")
        else:
            out_folder = filedialog.askdirectory(title="Select Output Folder")
            if out_folder:
                core.split_pdf_pages_individual(src_file, out_folder, page_indices, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", f"Split pages into separate files!")

    def execute_simple_action(self):
        if self.current_mode == "MERGE_PDF":
            out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")])
            if out_path:
                core.merge_pdfs_advanced(self.selected_files, out_path, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", "PDFs merged successfully!")

        elif self.current_mode == "IMG_TO_PDF":
            out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")])
            if out_path:
                core.images_to_pdf(self.selected_files, out_path, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", "Images converted to PDF successfully!")

        elif self.current_mode == "PDF_TO_IMG":
            out_folder = filedialog.askdirectory(title="Select Destination Directory")
            if out_folder:
                core.pdf_to_images(self.selected_files[0], out_folder, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", "PDF pages extracted as PNG images!")

        elif self.current_mode == "ENCRYPT_PDF":
            pwd = self.entry_pass.get().strip()
            if not pwd:
                messagebox.showerror("Error", "Please enter a password.")
                return
            out_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")])
            if out_path:
                core.encrypt_pdf(self.selected_files[0], out_path, pwd, page_rotations=self.page_rotations, deleted_pages=self.deleted_pages)
                messagebox.showinfo("Success", "PDF protected with password successfully!")