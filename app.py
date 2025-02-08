from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import instaloader

app = Flask(__name__)

# Instagram Credentials (set via environment variables)
INSTAGRAM_USERNAME = os.getenv("IG_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("IG_PASSWORD")

if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
    raise ValueError("Instagram username and password must be set as environment variables IG_USERNAME and IG_PASSWORD.")

# Ensure downloads directory exists
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url, download_type, save_path=DOWNLOAD_DIR):
    if not os.path.exists(save_path):
        return f"Invalid path: {save_path}"
    
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'noplaylist': False,
        'quiet': False,
    }
    
    if download_type == 'audio':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
    elif download_type == 'video':
        ydl_opts['format'] = 'bestvideo[height=1080]+bestaudio[ext=m4a]/best[height=1080]'
        ydl_opts['merge_output_format'] = 'mp4'
    else:
        return "Invalid option chosen!"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"Download complete: {info['title']}"
    except yt_dlp.DownloadError as e:
        return f"Download failed: {e}"

def download_instagram_reel(reel_url, save_path=DOWNLOAD_DIR):
    os.makedirs(save_path, exist_ok=True)
    
    L = instaloader.Instaloader(dirname_pattern=save_path)
    
    try:
        L.load_session_from_file(INSTAGRAM_USERNAME)
    except FileNotFoundError:
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        L.save_session_to_file()
    
    try:
        shortcode = reel_url.split("/p/")[-1].split("/")[0] if "/p/" in reel_url else reel_url.split("/reel/")[-1].split("/")[0]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=save_path)
        return f"Reel downloaded successfully in {save_path}"
    except Exception as e:
        return f"Failed to download reel: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json() or request.form
    url = data.get("playlist-url") or data.get("video-url")
    download_type = data.get("download-as", "video").lower()
    save_path = data.get("save-path", DOWNLOAD_DIR)
    
    if not url:
        return jsonify({"error": "No URL provided!"}), 400
    
    result = download_video(url, download_type, save_path)
    return jsonify({"output": result})

@app.route("/download-reel", methods=["POST"])
def download_reel():
    data = request.get_json() or request.form
    reel_url = data.get("reel-url")
    
    if not reel_url:
        return jsonify({"error": "No Reel URL provided!"}), 400
    
    result = download_instagram_reel(reel_url)
    return jsonify({"output": result})

@app.route('/feed', methods=['POST'])
def feedback():
    try:
        data = request.json
        name = data.get("name")
        surname = data.get("surname")
        email = data.get("email")
        query = data.get("query")
        
        if not all([name, surname, email, query]):
            return jsonify({"message": "All fields are required!"}), 400
        
        feedback_entry = f"Name: {name} {surname}\nEmail: {email}\nQuery: {query}\n---\n"
        with open("feedback.txt", "a") as f:
            f.write(feedback_entry)
        
        return jsonify({"message": "Feedback submitted successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)