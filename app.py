from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

def get_download_link(video_url, format_choice, quality):
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
    }

    # Video format selection
    if format_choice == 'mp4':
        quality_map = {
            '144p': 'bv*[height=144]+ba/bestvideo+bestaudio/best',
            '360p': 'bv*[height=360]+ba/bestvideo+bestaudio/best',
            '720p': 'bv*[height=720]+ba/bestvideo+bestaudio/best',
            '1080p': 'bv*[height=1080]+ba/bestvideo+bestaudio/best'
        }
        ydl_opts['format'] = quality_map.get(quality, 'bestvideo+bestaudio/best')

    # Audio format selection
    elif format_choice == 'm4a':
        quality_map = {
            '48kbps': 'bestaudio[abr<=48]/bestaudio',
            '128kbps': 'bestaudio[abr<=128]/bestaudio',
            '192kbps': 'bestaudio[abr<=192]/bestaudio',
            '320kbps': 'bestaudio[abr<=320]/bestaudio'
        }
        ydl_opts['format'] = quality_map.get(quality, 'bestaudio/bestaudio[ext=m4a]')

    else:
        return None



    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Multiple formats ho sakti hain, best select karna hoga
            if 'entries' in info:
                info = info['entries'][0]  # Agar playlist ka link ho

            formats = info.get('formats', [])
            if formats:
                best_format = max(formats, key=lambda f: f.get('filesize', 0) or 0)
                return best_format['url']
            
            return None
    except Exception as e:
        print("Error:", e)
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    video_url = data.get('video-url')
    format_choice = 'm4a' if data.get('download-as') == 'audio' else 'mp4'
    quality = data.get('quality')

    download_link = get_download_link(video_url, format_choice, quality)
    
    if download_link:
        return jsonify({"output": download_link})
    else:
        return jsonify({"output": "Failed to fetch download link."}), 400


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
