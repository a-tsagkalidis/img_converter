import os
import threading
import json
import tempfile
from PIL import Image
from tkinter import (
    filedialog, Button, Label, Scale, HORIZONTAL, messagebox, StringVar,
    BooleanVar, IntVar, Frame, Checkbutton, Entry, OptionMenu
)
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES


class ImageConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Image Converter — PNG/JPG → JPG/WebP")
        master.geometry("740x820")

        self.input_folder = StringVar()
        self.output_folder = StringVar()
        self.overwrite_existing = BooleanVar(value=True)
        self.process_subfolders = BooleanVar(value=False)
        self.process_png = BooleanVar(value=True)
        self.process_jpg = BooleanVar(value=True)
        self.output_format = StringVar(value="JPG")

        self.resize_enabled = BooleanVar(value=False)
        self.resize_mode = StringVar(value="Max dimension")
        self.resize_max_width = StringVar(value="1920")
        self.resize_max_height = StringVar(value="1080")
        self.resize_percent = IntVar(value=50)

        self.load_settings()

        # --- Input Folder Selection ---
        input_frame = Frame(master)
        input_frame.pack(pady=10, fill='x', padx=10)
        Label(input_frame, text="Input Folder:").pack(side='left', padx=(0, 5))
        self.input_entry = Entry(input_frame, textvariable=self.input_folder, width=50)
        self.input_entry.pack(side='left', expand=True, fill='x')
        Button(input_frame, text="Browse", command=self.select_input_folder).pack(side='left', padx=(5, 0))

        # --- Output Folder Selection ---
        output_frame = Frame(master)
        output_frame.pack(pady=10, fill='x', padx=10)
        Label(output_frame, text="Output Folder:").pack(side='left', padx=(0, 5))
        self.output_entry = Entry(output_frame, textvariable=self.output_folder, width=50)
        self.output_entry.pack(side='left', expand=True, fill='x')
        Button(output_frame, text="Browse", command=self.select_output_folder).pack(side='left', padx=(5, 0))

        # Drag-and-drop: drop a folder (or a file inside one) onto either entry to set it.
        for entry, var in ((self.input_entry, self.input_folder),
                           (self.output_entry, self.output_folder)):
            entry.drop_target_register(DND_FILES)
            entry.dnd_bind('<<Drop>>', lambda e, v=var: self._handle_drop(e, v))

        Label(master, text="Tip: drag a folder onto the Input or Output field.",
              fg='gray').pack(anchor='w', padx=12)

        # --- Options Frame ---
        options_frame = Frame(master, bd=2, relief='groove')
        options_frame.pack(pady=10, padx=10, fill='x')
        Label(options_frame, text="Conversion Options", font=("Arial", 10, "bold")).pack(pady=5)

        Checkbutton(options_frame, text="Overwrite existing files", variable=self.overwrite_existing).pack(anchor='w', padx=10)
        Checkbutton(options_frame, text="Process subfolders", variable=self.process_subfolders).pack(anchor='w', padx=10)

        formats_row = Frame(options_frame)
        formats_row.pack(anchor='w', padx=10, pady=(2, 6))
        Label(formats_row, text="Input formats:").pack(side='left')
        Checkbutton(formats_row, text="PNG", variable=self.process_png).pack(side='left', padx=4)
        Checkbutton(formats_row, text="JPG/JPEG", variable=self.process_jpg).pack(side='left', padx=4)

        output_row = Frame(options_frame)
        output_row.pack(anchor='w', padx=10, pady=(2, 8))
        Label(output_row, text="Output format:").pack(side='left')
        OptionMenu(output_row, self.output_format, "JPG", "WebP").pack(side='left', padx=4)

        # --- JPG Quality Slider ---
        quality_frame = Frame(master)
        quality_frame.pack(pady=10, fill='x', padx=10)
        self.quality_label = Label(quality_frame, text="Quality:")
        self.quality_label.pack(side='left', padx=(0, 5))
        self.quality_slider = Scale(quality_frame, from_=1, to=100, orient=HORIZONTAL, label="Quality %", length=300)
        self.quality_slider.set(90)
        self.quality_slider.pack(side='left', expand=True, fill='x')

        # --- Resize Frame ---
        resize_frame = Frame(master, bd=2, relief='groove')
        resize_frame.pack(pady=10, padx=10, fill='x')

        header_row = Frame(resize_frame)
        header_row.pack(fill='x', padx=10, pady=5)
        Checkbutton(header_row, text="Resize images", variable=self.resize_enabled,
                    command=self._update_resize_ui).pack(side='left')
        Label(header_row, text="Mode:").pack(side='left', padx=(20, 5))
        self.mode_menu = OptionMenu(header_row, self.resize_mode, "Max dimension", "Percentage",
                                    command=lambda *_: self._update_resize_ui())
        self.mode_menu.pack(side='left')

        self.dim_row = Frame(resize_frame)
        Label(self.dim_row, text="Max width:").pack(side='left')
        self.width_entry = Entry(self.dim_row, textvariable=self.resize_max_width, width=8)
        self.width_entry.pack(side='left', padx=(4, 12))
        Label(self.dim_row, text="Max height:").pack(side='left')
        self.height_entry = Entry(self.dim_row, textvariable=self.resize_max_height, width=8)
        self.height_entry.pack(side='left', padx=4)
        Label(self.dim_row, text="(blank = unlimited; aspect kept; no upscale)",
              fg='gray').pack(side='left', padx=(8, 0))

        self.pct_row = Frame(resize_frame)
        Label(self.pct_row, text="Scale:").pack(side='left')
        self.pct_slider = Scale(self.pct_row, from_=10, to=200, orient=HORIZONTAL,
                                variable=self.resize_percent, length=300)
        self.pct_slider.pack(side='left', expand=True, fill='x', padx=4)
        Label(self.pct_row, text="%").pack(side='left')

        self._update_resize_ui()

        # --- Convert Button ---
        self.convert_button = Button(master, text="Convert Images", command=self.start_conversion_thread, height=2)
        self.convert_button.pack(pady=20, padx=10, fill='x')

        # --- Progress Bar ---
        self.progress_frame = Frame(master)
        self.progress_frame.pack(pady=10, padx=10, fill='x')
        self.progress_label = Label(self.progress_frame, text="Ready to convert...")
        self.progress_label.pack(anchor='w')
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=HORIZONTAL, length=500, mode='determinate')
        self.progress_bar.pack(fill='x', expand=True)

        # --- Open Output Folder Button ---
        self.open_output_button = Button(master, text="Open Output Folder", command=self.open_output_folder, state='disabled')
        self.open_output_button.pack(pady=10, padx=10, fill='x')

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _update_resize_ui(self):
        enabled = self.resize_enabled.get()
        state = 'normal' if enabled else 'disabled'
        self.mode_menu.config(state=state)
        for w in (self.width_entry, self.height_entry, self.pct_slider):
            w.config(state=state)

        if self.resize_mode.get() == "Percentage":
            self.dim_row.pack_forget()
            self.pct_row.pack(fill='x', padx=10, pady=4)
        else:
            self.pct_row.pack_forget()
            self.dim_row.pack(fill='x', padx=10, pady=4)

    def _handle_drop(self, event, target_var):
        # event.data may contain multiple paths; tk.splitlist correctly handles braces around paths with spaces.
        paths = self.master.tk.splitlist(event.data)
        if not paths:
            return
        first = paths[0]
        if os.path.isdir(first):
            target_var.set(first)
        elif os.path.isfile(first):
            target_var.set(os.path.dirname(first))

    def load_settings(self):
        settings_file = "converter_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.input_folder.set(settings.get('last_input_folder', ''))
                    self.output_folder.set(settings.get('last_output_folder', ''))
            except json.JSONDecodeError:
                messagebox.showwarning("Settings Error", "Could not read settings file. It might be corrupted.")

    def save_settings(self):
        settings = {
            'last_input_folder': self.input_folder.get(),
            'last_output_folder': self.output_folder.get()
        }
        with open("converter_settings.json", 'w') as f:
            json.dump(settings, f)

    def on_closing(self):
        self.save_settings()
        self.master.destroy()

    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def open_output_folder(self):
        output_path = self.output_folder.get()
        if output_path and os.path.exists(output_path):
            try:
                if os.name == 'nt':
                    os.startfile(output_path)
                elif os.uname().sysname == 'Darwin':
                    os.system(f'open "{output_path}"')
                else:
                    os.system(f'xdg-open "{output_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open output folder: {e}")
        else:
            messagebox.showwarning("Warning", "Output folder not found or not selected.")

    def _build_resize_params(self):
        if not self.resize_enabled.get():
            return None
        if self.resize_mode.get() == "Percentage":
            return ('percent', max(1, self.resize_percent.get()))
        w_str = self.resize_max_width.get().strip()
        h_str = self.resize_max_height.get().strip()
        try:
            max_w = int(w_str) if w_str else None
            max_h = int(h_str) if h_str else None
        except ValueError:
            raise ValueError("Max width / height must be whole numbers.")
        if max_w is not None and max_w <= 0:
            max_w = None
        if max_h is not None and max_h <= 0:
            max_h = None
        return ('max_dim', max_w, max_h)

    @staticmethod
    def _apply_resize(img, resize):
        if resize is None:
            return img
        if resize[0] == 'percent':
            pct = resize[1] / 100.0
            new_size = (max(1, int(img.width * pct)), max(1, int(img.height * pct)))
            if new_size == img.size:
                return img
            return img.resize(new_size, Image.Resampling.LANCZOS)
        # max_dim: shrink-to-fit, never upscale
        _, max_w, max_h = resize
        if not max_w and not max_h:
            return img
        scale = 1.0
        if max_w:
            scale = min(scale, max_w / img.width)
        if max_h:
            scale = min(scale, max_h / img.height)
        if scale >= 1.0:
            return img
        new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        return img.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def _prepare_image(img, output_format):
        has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
        if output_format == "WebP":
            # WebP supports transparency, so keep the alpha channel.
            if has_alpha:
                return img if img.mode == 'RGBA' else img.convert('RGBA')
            return img if img.mode == 'RGB' else img.convert('RGB')
        # JPEG has no alpha channel; composite onto white if there's transparency.
        if has_alpha:
            rgba = img.convert('RGBA')
            bg = Image.new('RGB', rgba.size, 'white')
            bg.paste(rgba, mask=rgba.split()[-1])
            return bg
        if img.mode != 'RGB':
            return img.convert('RGB')
        return img

    @staticmethod
    def _save_image(img, path, output_format, quality):
        if output_format == "WebP":
            img.save(path, "WEBP", quality=quality)
        else:
            img.save(path, "JPEG", quality=quality, optimize=True)

    def start_conversion_thread(self):
        input_path = self.input_folder.get()
        output_path = self.output_folder.get()
        jpg_quality = self.quality_slider.get()

        if not input_path:
            messagebox.showwarning("Missing Input", "Please select an input folder.")
            return
        if not output_path:
            messagebox.showwarning("Missing Output", "Please select an output folder.")
            return
        if not (self.process_png.get() or self.process_jpg.get()):
            messagebox.showwarning("No Input Format", "Select at least one input format (PNG or JPG/JPEG).")
            return

        try:
            resize = self._build_resize_params()
        except ValueError as e:
            messagebox.showerror("Invalid Resize", str(e))
            return

        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
            except OSError as e:
                messagebox.showerror("Folder Creation Error", f"Could not create output folder: {e}")
                return

        self.convert_button.config(state="disabled")
        self.open_output_button.config(state="disabled")
        self.quality_slider.config(state="disabled")

        self.progress_bar['value'] = 0
        self.progress_label.config(text="Scanning files...")
        self.master.update_idletasks()

        exts = []
        if self.process_png.get():
            exts.append(".png")
        if self.process_jpg.get():
            exts.extend([".jpg", ".jpeg"])

        conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_path, jpg_quality, tuple(exts),
                  self.overwrite_existing.get(), self.process_subfolders.get(),
                  resize, self.output_format.get()),
            daemon=True,
        )
        conversion_thread.start()
        self.master.after(100, self.check_conversion_thread, conversion_thread)

    def _run_conversion(self, input_folder, output_folder, quality, exts,
                        overwrite, process_subfolders, resize, output_format):
        out_ext = ".webp" if output_format == "WebP" else ".jpg"
        files_to_convert = []
        if process_subfolders:
            for root, _, files in os.walk(input_folder):
                for file in files:
                    if file.lower().endswith(exts):
                        files_to_convert.append(os.path.join(root, file))
        else:
            for file in os.listdir(input_folder):
                full = os.path.join(input_folder, file)
                if os.path.isfile(full) and file.lower().endswith(exts):
                    files_to_convert.append(full)

        total_files = len(files_to_convert)
        converted_count = 0
        skipped_count = 0

        self.master.after(0, lambda: self.progress_bar.config(maximum=max(total_files, 1)))

        if total_files == 0:
            self.master.after(0, lambda: messagebox.showinfo(
                "No Files", "No matching images found in the selected input folder."))
            self.master.after(0, self._conversion_finished)
            return

        for src_path in files_to_convert:
            relative_path = os.path.relpath(src_path, input_folder)

            if process_subfolders:
                output_sub_dir = os.path.dirname(relative_path)
                current_output_folder = os.path.join(output_folder, output_sub_dir)
            else:
                current_output_folder = output_folder

            if not os.path.exists(current_output_folder):
                try:
                    os.makedirs(current_output_folder)
                except OSError as e:
                    self.master.after(0, lambda err=e, p=current_output_folder:
                                      messagebox.showerror("Folder Creation Error",
                                                           f"Could not create subfolder {p}: {err}"))
                    continue

            stem = os.path.splitext(os.path.basename(src_path))[0]
            out_path = os.path.join(current_output_folder, stem + out_ext)

            same_file = os.path.abspath(src_path) == os.path.abspath(out_path)

            if os.path.exists(out_path) and not overwrite and not same_file:
                skipped_count += 1
                self.master.after(0, lambda fn=os.path.basename(src_path):
                                  self.progress_label.config(text=f"Skipping: {fn} (already exists)"))
                self.master.after(0, lambda: self.progress_bar.step(1))
                continue
            if same_file and not overwrite:
                skipped_count += 1
                self.master.after(0, lambda fn=os.path.basename(src_path):
                                  self.progress_label.config(text=f"Skipping: {fn} (would overwrite source)"))
                self.master.after(0, lambda: self.progress_bar.step(1))
                continue

            try:
                with Image.open(src_path) as img:
                    img.load()
                    img = self._prepare_image(img, output_format)
                    img = self._apply_resize(img, resize)

                    if same_file:
                        # Write to a temp file in the same folder, then atomically replace.
                        fd, tmp_path = tempfile.mkstemp(suffix=out_ext, dir=current_output_folder)
                        os.close(fd)
                        try:
                            self._save_image(img, tmp_path, output_format, quality)
                            os.replace(tmp_path, out_path)
                        except Exception:
                            if os.path.exists(tmp_path):
                                try:
                                    os.remove(tmp_path)
                                except OSError:
                                    pass
                            raise
                    else:
                        self._save_image(img, out_path, output_format, quality)

                converted_count += 1
                self.master.after(0, lambda fn=os.path.basename(src_path), q=quality:
                                  self.progress_label.config(text=f"Converting: {fn} ({q}%)"))
                self.master.after(0, lambda: self.progress_bar.step(1))

            except Exception as e:
                self.master.after(0, lambda fn=os.path.basename(src_path), error=e:
                                  messagebox.showerror("Conversion Error", f"Could not convert {fn}:\n{error}"))
                self.master.after(0, lambda: self.progress_bar.step(1))

        self.master.after(0, lambda: messagebox.showinfo(
            "Conversion Complete",
            f"Converted {converted_count} of {total_files} images to {output_format}."
            + (f"\nSkipped: {skipped_count}" if skipped_count else "")
        ))
        self.master.after(0, self._conversion_finished)

    def _conversion_finished(self):
        self.convert_button.config(state="normal")
        self.open_output_button.config(state="normal")
        self.quality_slider.config(state="normal")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Conversion finished. Ready to convert again.")

    def check_conversion_thread(self, thread):
        if thread.is_alive():
            self.master.after(100, self.check_conversion_thread, thread)
        else:
            self._conversion_finished()


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
