import os
import threading
import json
from PIL import Image
from tkinter import (
    Tk, filedialog, Button, Label, Scale, HORIZONTAL, messagebox, StringVar,
    BooleanVar, Frame, Checkbutton, Entry
)
from tkinter import ttk  # Import ttk for themed widgets like Progressbar

class PNGtoJPGConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("PNG to JPG Converter")
        master.geometry("700x650") # Increased window size for more elements

        self.input_folder = StringVar()
        self.output_folder = StringVar()
        self.overwrite_existing = BooleanVar(value=True) # Default to overwrite
        self.process_subfolders = BooleanVar(value=False) # Default to not process subfolders

        self.load_settings() # Load last used folders on startup

        # --- Input Folder Selection ---
        input_frame = Frame(master)
        input_frame.pack(pady=10, fill='x', padx=10)

        Label(input_frame, text="Input Folder:").pack(side='left', padx=(0, 5))
        self.input_entry = Entry(input_frame, textvariable=self.input_folder, width=50, state='readonly')
        self.input_entry.pack(side='left', expand=True, fill='x')
        Button(input_frame, text="Browse", command=self.select_input_folder).pack(side='left', padx=(5, 0))

        # --- Output Folder Selection ---
        output_frame = Frame(master)
        output_frame.pack(pady=10, fill='x', padx=10)

        Label(output_frame, text="Output Folder:").pack(side='left', padx=(0, 5))
        self.output_entry = Entry(output_frame, textvariable=self.output_folder, width=50, state='readonly')
        self.output_entry.pack(side='left', expand=True, fill='x')
        Button(output_frame, text="Browse", command=self.select_output_folder).pack(side='left', padx=(5, 0))

        # --- Options Frame ---
        options_frame = Frame(master, bd=2, relief='groove')
        options_frame.pack(pady=10, padx=10, fill='x')

        Label(options_frame, text="Conversion Options", font=("Arial", 10, "bold")).pack(pady=5)

        Checkbutton(options_frame, text="Overwrite existing JPGs", variable=self.overwrite_existing).pack(anchor='w', padx=10)
        Checkbutton(options_frame, text="Process subfolders", variable=self.process_subfolders).pack(anchor='w', padx=10)

        # --- JPG Quality Slider ---
        quality_frame = Frame(master)
        quality_frame.pack(pady=10, fill='x', padx=10)

        self.quality_label = Label(quality_frame, text="JPG Quality:")
        self.quality_label.pack(side='left', padx=(0, 5))
        self.quality_slider = Scale(quality_frame, from_=1, to=100, orient=HORIZONTAL, label="Quality %", length=300)
        self.quality_slider.set(90)  # Default quality to 90%
        self.quality_slider.pack(side='left', expand=True, fill='x')

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

        master.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close event

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
                # Platform-independent way to open a folder
                if os.name == 'nt':  # For Windows
                    os.startfile(output_path)
                elif os.uname().sysname == 'Darwin':  # For macOS
                    os.system(f'open "{output_path}"')
                else:  # For Linux/Unix
                    os.system(f'xdg-open "{output_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open output folder: {e}")
        else:
            messagebox.showwarning("Warning", "Output folder not found or not selected.")

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
        
        # Ensure output folder exists before starting
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
            except OSError as e:
                messagebox.showerror("Folder Creation Error", f"Could not create output folder: {e}")
                return

        # Disable buttons during conversion
        self.convert_button.config(state="disabled")
        self.open_output_button.config(state="disabled")
        self.input_entry.config(state="disabled")
        self.output_entry.config(state="disabled")
        self.quality_slider.config(state="disabled")

        self.progress_bar['value'] = 0
        self.progress_label.config(text="Scanning files...")
        self.master.update_idletasks() # Update GUI immediately

        # Start conversion in a separate thread to keep GUI responsive
        conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_path, jpg_quality,
                  self.overwrite_existing.get(), self.process_subfolders.get())
        )
        conversion_thread.start()

        # Periodically check if the thread is alive
        self.master.after(100, self.check_conversion_thread, conversion_thread)

    def _run_conversion(self, input_folder, output_folder, quality, overwrite, process_subfolders):
        # Collect all PNG files
        png_files_to_convert = []
        if process_subfolders:
            for root, _, files in os.walk(input_folder):
                for file in files:
                    if file.lower().endswith(".png"):
                        png_files_to_convert.append(os.path.join(root, file))
        else:
            for file in os.listdir(input_folder):
                if file.lower().endswith(".png"):
                    png_files_to_convert.append(os.path.join(input_folder, file))

        total_files = len(png_files_to_convert)
        converted_count = 0

        self.master.after(0, lambda: self.progress_bar.config(maximum=total_files))

        if total_files == 0:
            self.master.after(0, lambda: messagebox.showinfo("No Files", "No PNG files found in the selected input folder."))
            self.master.after(0, self._conversion_finished)
            return

        for i, png_path in enumerate(png_files_to_convert):
            relative_path = os.path.relpath(png_path, input_folder)
            
            # Construct output path preserving subfolder structure if applicable
            if process_subfolders:
                output_sub_dir = os.path.dirname(relative_path)
                current_output_folder = os.path.join(output_folder, output_sub_dir)
            else:
                current_output_folder = output_folder

            if not os.path.exists(current_output_folder):
                try:
                    os.makedirs(current_output_folder)
                except OSError as e:
                    self.master.after(0, lambda: messagebox.showerror("Folder Creation Error", f"Could not create subfolder {current_output_folder}: {e}"))
                    continue # Skip this file

            jpg_filename = os.path.basename(png_path)[:-4] + ".jpg"
            jpg_path = os.path.join(current_output_folder, jpg_filename)

            # Overwrite logic
            if os.path.exists(jpg_path) and not overwrite:
                self.master.after(0, lambda fn=os.path.basename(png_path):
                                  self.progress_label.config(text=f"Skipping: {fn} (already exists)"))
                self.master.after(0, lambda: self.progress_bar.step(1))
                continue # Skip this file

            try:
                img = Image.open(png_path)
                
                if img.mode == 'RGBA':
                    new_img = Image.new("RGB", img.size, "white")
                    new_img.paste(img, (0, 0), img)
                    img = new_img
                
                img.save(jpg_path, "JPEG", quality=quality)
                converted_count += 1
                self.master.after(0, lambda fn=os.path.basename(png_path), q=quality:
                                  self.progress_label.config(text=f"Converting: {fn} ({q}%)"))
                self.master.after(0, lambda: self.progress_bar.step(1))

            except Exception as e:
                self.master.after(0, lambda fn=os.path.basename(png_path), error=e:
                                  messagebox.showerror("Conversion Error", f"Could not convert {fn}:\n{error}"))
                # Still step the progress bar even on error to indicate progress
                self.master.after(0, lambda: self.progress_bar.step(1))

        self.master.after(0, lambda: messagebox.showinfo(
            "Conversion Complete",
            f"Converted {converted_count} of {total_files} PNG images to JPG."
        ))
        self.master.after(0, self._conversion_finished)

    def _conversion_finished(self):
        # Re-enable buttons and reset progress bar
        self.convert_button.config(state="normal")
        self.open_output_button.config(state="normal")
        self.input_entry.config(state="readonly")
        self.output_entry.config(state="readonly")
        self.quality_slider.config(state="normal")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Conversion finished. Ready to convert again.")

    def check_conversion_thread(self, thread):
        if thread.is_alive():
            self.master.after(100, self.check_conversion_thread, thread)
        else:
            self._conversion_finished()


if __name__ == "__main__":
    root = Tk()
    app = PNGtoJPGConverterApp(root)
    root.mainloop()