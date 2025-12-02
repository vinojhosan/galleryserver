# GalleryServer

A simple image gallery server.

## Installation

Install GalleryServer directly or from the GitHub repository using pip:

```bash
pip install galleryserver
```

or 

```bash
pip install git+https://github.com/vinojhosan/galleryserver.git
```



## Usage

After installation, run the server with:

```bash
galleryserver [PORT] [OPTIONS]
```

- `PORT` (optional): Port to serve on (default: `8000`).

### Arguments

| Argument / Option           | Description                                   | Default              |
|----------------------------|-----------------------------------------------|----------------------|
| `PORT`                     | Port to serve on                              | `8000`               |
| `--thumbnail-size`         | Thumbnail size in pixels                      | `200`                |
| `--directory`, `-d`        | Directory to serve                            | Current directory (`.`) |

### Example

```bash
galleryserver 12345 -d /path/to/images --thumbnail-size 300 
```


---

## 🚀 Features

### 🖼 Modern Thumbnail Gallery
- Auto-generated thumbnails (fast + cached)
- Responsive grid layout
- Smooth fade-in animations
- Works on mobile and desktop

### 🔍 Full Image Viewer (Modal)
- Click image → opens large preview
- Double-click → opens original image in new tab
- Navigate using:
  - **← / →** arrow keys  
  - **Swipe left/right** (mobile)
  - On-screen Prev/Next buttons

### 🔎 Advanced Zoom & Pan
- Mouse wheel zoom
- Drag to pan
- Pinch-to-zoom (mobile)
- Double-tap zoom
- Reset zoom button

### 🎞 Slideshow Mode
- Auto-play slideshow
- Play/Pause toggle
- Spacebar toggles slideshow

### 🖥 Fullscreen Mode
- Click image to toggle fullscreen
- Clean, immersive view

---

🤝 Contributing

Pull requests and suggestions are welcome!

⭐ Support the Project

If you like this project, please ⭐ star it on GitHub:

https://github.com/vinojhosan/galleryserver


## 📝 License

This project is open-source and available under the MIT License.  
See the [LICENSE](LICENSE) file for details.
