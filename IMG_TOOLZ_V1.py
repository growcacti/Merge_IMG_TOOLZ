import os
import sys
import json
import tkinter as tk
from tkinter import Tk, filedialog, ttk, StringVar, messagebox, simpledialog, Menu, END, Label, Listbox, Toplevel, Button, Frame, Checkbutton,BooleanVar
from glob import glob
from PIL import Image, ImageTk



Image.MAX_IMAGE_PIXELS = None

class Image_Thumbnail_Toolz:
    def __init__(self, root, json_file="pathmarks.json"):
        self.root = root
        self.json_file = json_file
        self.path_var = StringVar()

        self.bookmarks = self.load_bookmarks()
        self.image_paths = []
        self.selected_images = []
        self.merged_image = None
        self.setup_gui()
        self.top = Toplevel(self.root)
        self.top.title("Selected Files")
        self.top.geometry("400x300")

        self.listbox = Listbox(self.top, width=50, height=15)
        self.listbox.grid(row=1,column=1)
        self.remove_btn = Button(self.top,bd=7,bg="orchid", text="Remove Selected", command=lambda: self.remove_selected(self.listbox))
        self.remove_btn.grid(row=2,column=2)

        self.close_btn = Button(self.top,bd=7,bg="bisque", text="Close", command=self.top.destroy)
        self.close_btn.grid(row=2,column=3)
        self.x = 180
        self.y = 180
    def setup_gui(self):
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Browse", command=self.browse_path)
        file_menu.add_command(label="Save Bookmark", command=self.save_bookmarks)
        file_menu.add_command(label="Delete Bookmark", command=self.delete_bookmark)
        file_menu.add_command(label="Add Bookmark", command=self.add_bookmark)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        tools_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Get Images", command=self.get_images)
        tools_menu.add_command(label="Merge Images", command=self.merge_images)
        tools_menu.add_command(label="Show Selected Files", command=self.show_selected_files)
        view_menu =  Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Views", menu=view_menu)
        view_menu.add_command(label="Thumnails 64x66", command=self.change_thumbnail_size1)
        view_menu.add_command(label="Thumnails 128x128", command=self.change_thumbnail_size2)
        view_menu.add_command(label="Thumnails 180x180", command=self.change_thumbnail_size3)
        view_menu.add_command(label="Thumnails 256x256", command=self.change_thumbnail_size4)
        self.dir_path = ttk.Entry(self.root, textvariable=self.path_var, width=50)
        self.dir_path.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.dir_path.insert(0, os.getcwd())
        self.btn_browse = Button(self.root, bd=8, bg="azure", text="Get Images", command=self.get_images)
        self.btn_browse.grid(row=14, column=0, padx=5)
        self.bookmark_var = StringVar()
        tk.Label(self.root, text="Bookmarks Drop Down").grid(row=15,column=2)
        self.bookmark_combo = ttk.Combobox(self.root, textvariable=self.bookmark_var, values=list(self.bookmarks.keys()))
        self.bookmark_combo.grid(row=16, column=2, columnspan=2, sticky="ew", padx=5, pady=5)
        self.bookmark_combo.bind("<<ComboboxSelected>>", self.select_bookmark)


        self.var_recursive = BooleanVar(value=False)
        self.check_recursive = Checkbutton(self.root, text="Recursive View", variable=self.var_recursive, command=self.update_mode_label)
        self.check_recursive.grid(row=13, column=4, padx=5)
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=16, column=4, columnspan=2, pady=5, sticky="ew")
        self.progress_label = tk.Label(self.root, text="if loading please wait... Progress Bar")
        self.progress_label.grid(row=15, column=4)
        self.mode_label = tk.Label(self.root, text=self.var_recursive)
        self.mode_label.grid(row=13, column=5)

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=6, rowspan=4,sticky="nsew", padx=5, pady=5)
        self.v_scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.v_scroll.grid(row=1, column=8, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.h_scroll.grid(row=11, column=0, columnspan=4, sticky="ew")
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)


        self.frame_thumbnails = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_thumbnails, anchor="nw")
        self.frame_thumbnails.bind("<Configure>", lambda e: self.canvas.config(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.clear_selection_btn = Button(self.root, bd=7,text="Clear Selection", command=self.clear_selection)
        self.clear_selection_btn.grid(row=14, column=2, padx=5, pady=5)

        self.save_merged_btn = Button(self.root,bd=6,bg="skyblue", text="Save Merged Image", command=self.save_merged_image)
        self.save_merged_btn.grid(row=14, column=3, padx=5, pady=5)
        self.view_selected_btn = Button(self.root,bd=5,bg="thistle", text="View Selected Files", command=self.show_selected_files)
        self.view_selected_btn.grid(row=14, column=4, padx=5, pady=5)
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)
        self.display_selected_thumbnails()
    def adjust_entry_width(self):
        path_length = len(self.path_var.get())
        self.dir_path.config(width=max(50, path_length))


    def load_bookmarks(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as file:
                return json.load(file)
        return {}

    def save_bookmarks(self):
        try:
            with open(self.json_file, "w") as file:
                json.dump(self.bookmarks, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save bookmarks: {e}")

    def delete_bookmark(self):
        selected = self.path_var.get()
        if selected in self.bookmarks:
            del self.bookmarks[selected]
            self.save_bookmarks()
            messagebox.showinfo("Bookmark Deleted", "Bookmark deleted successfully.")

    def add_bookmark(self):
        path = self.path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Invalid Path", "Select a valid path before adding a bookmark.")
            return

        name = simpledialog.askstring("Bookmark Name", "Enter a name for the bookmark:")
        if name:
            self.bookmarks[name] = path
            self.save_bookmarks()
            messagebox.showinfo("bokkmark added")

      
    def save_bookmarks(self):
        try:
            with open(self.json_file, "w") as file:
                json.dump(self.bookmarks, file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save bookmarks: {e}")

    def delete_bookmark(self):
        selected = self.bookmark_var.get()
        if selected in self.bookmarks:
            del self.bookmarks[selected]
            self.update_bookmarks()
            messagebox.showinfo("Bookmark Deleted", f"Bookmark '{selected}' deleted successfully.")

    def select_bookmark(self, event=None):
        selected = self.bookmark_var.get()
        if selected in self.bookmarks:
            self.path_var.set(self.bookmarks[selected])
            self.adjust_entry_width()

    def use_path(self):
        path = self.path_var.get()
        if os.path.exists(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path], check=True)
                elif sys.platform.startswith("linux"):
                    subprocess.run(["xdg-open", path], check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open path: {e}")

    def load_bookmarks(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as file:
                return json.load(file)
        return {}

    def update_bookmarks(self):
        self.bookmark_combo['values'] = list(self.bookmarks.keys())
        self.save_bookmarks()


   
    def load_images(self, directory):
        extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif')
        self.image_paths = []

        for ext in extensions:
            self.image_paths.extend(glob(os.path.join(directory, ext), recursive=False))

        if not self.image_paths:
            messagebox.showinfo("No Images", "No images found in the selected directory.")
            return

        self.display_thumbnails()
    def get_images(self):
        path = self.path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "The selected path does not exist.")
            return

        extensions = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif')
        self.image_paths = []
        for ext in extensions:
            self.image_paths.extend(glob(os.path.join(path, ext)))
        
        if not self.image_paths:
            messagebox.showinfo("No Images Found", "No images found in the selected directory.")
            return
        
        self.display_thumbnails()
    def change_thumbnail_size1(self):
        self.x, self.y = 64,64
        self.display_thumbnails()
        return self.x,self.y
    def change_thumbnail_size2(self):
        self.x, self.y = 128,128
        self.display_thumbnails()
        return self.x,self.y

    def change_thumbnail_size3(self):
        self.x, self.y = 180,180
        self.display_thumbnails()
        return self.x,self.y
    def change_thumbnail_size4(self):
        self.x, self.y = 256,256
        self.display_thumbnails()
        return self.x,self.y       
    def display_thumbnails(self):
        for widget in self.frame_thumbnails.winfo_children():
            widget.destroy()

        for index, img_path in enumerate(self.image_paths):
            try:
                img = Image.open(img_path)
                img.thumbnail((self.x,self.y))
                tk_img = ImageTk.PhotoImage(img)

                frame = Frame(self.frame_thumbnails, bd=10, relief="ridge")
                frame.grid(row=index // 10, column=index % 10, padx=5, pady=5)

                lbl_img = Label(frame, image=tk_img)
                lbl_img.image = tk_img  # Keep reference to avoid garbage collection
                lbl_img.grid(row=0, column=0)

                lbl_img.bind("<Button-1>", lambda e, path=img_path: self.select_image(path))
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

    def select_image(self, img_path):
        if img_path in self.selected_images:
            self.selected_images.remove(img_path)
        else:
            self.selected_images.append(img_path)
        self.display_selected_thumbnails()

    def display_selected_thumbnails(self):
        for widget in self.frame_thumbnails.winfo_children():
            widget.config(bg="alice blue")

        for img_path in self.selected_images:
            index = self.image_paths.index(img_path)
            widget = self.frame_thumbnails.grid_slaves(row=index // 10, column=index % 10)[0]
            widget.config(bg="cyan")

    def show_selected_files(self):
        if not self.selected_images:
            messagebox.showinfo("No Selection", "No images selected.")
            return

       

       
       
        for img in self.selected_images:
            self.listbox.insert(END, os.path.basename(img))

      
    def remove_selected(self, listbox):
        selected = self.listbox.curselection()
        if selected:
            file_to_remove = self.selected_images[selected[0]]
            self.selected_images.remove(file_to_remove)
            self.listbox.delete(selected)
            self.display_selected_thumbnails()

    def merge_images(self):
        if len(self.selected_images) < 2:
            messagebox.showwarning("Insufficient Images", "Select at least two images to merge.")
            return

        images = [Image.open(img) for img in self.selected_images]
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)

        merged = Image.new("RGB", (total_width, max_height))
        x_offset = 0
        for img in images:
            merged.paste(img, (x_offset, 0))
            x_offset += img.width

        self.preview_image(merged)

    def preview_image(self, img):
        self.top2 = Toplevel(self.root)
        self.top2.title("Merged Image Preview")
        tk_img = ImageTk.PhotoImage(img)
        lbl_img = Label(self.top2, image=tk_img)
        lbl_img.image = tk_img  # Keep reference
        lbl_img.grid(row=2, column=4)

    def view_full_image(self):
        if not self.image_paths:
            messagebox.showwarning("No Images", "No images to view.")
            return

        self.current_img_index = 0 if self.current_img_index == -1 else self.current_img_index
        self.open_full_image(self.image_paths[self.current_img_index])

  

        Button(self.top2, text="Previous", command=lambda: self.navigate_image(-1, self.top2)).grid(row=12,column=1)
        Button(self.top2, text="Next", command=lambda: self.navigate_image(1, self.top2)).grid(row=12, column=4)
    def navigate_image(self, direction, top2):
        self.current_img_index = (self.current_img_index + direction) % len(self.image_paths)
        self.top2.destroy()
        self.open_full_image(self.image_paths[self.current_img_index])

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(-1 * (event.delta // 120), "units")
    def update_mode_label(self):
        mode = "Recursive Directory" if self.var_recursive.get() else "Flat Directory"
        self.mode_label.config(text=f"Mode: {mode}")
        self.update_view()  # Reload images on mode change
    def clear_selection(self):
        """Clear all selected images."""
        self.selected_images = []
        self.display_selected_thumbnails()
        messagebox.showinfo("Selection Cleared", "All selected images have been cleared.")
    def save_merged_image(self):
        """Save the merged image."""
        if not hasattr(self, 'merged_image'):
            messagebox.showerror("No Merged Image", "There is no merged image to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            self.merged_image.save(file_path)
        messagebox.showinfo("Image Saved", f"Merged image saved as {file_path}")
    def update_view(self):
        """Reload images based on the current recursive setting."""
        directory = self.path_var.get()
        if os.path.exists(directory):
            self.load_images(directory)
        else:
            messagebox.showerror("Error", "The directory path is invalid.") 
if __name__ == "__main__":
    root = Tk()
    root.title("Image Thumbnail Toolz")
    Image_Thumbnail_Toolz(root)
    root.mainloop()
