import os
import sys
import json
import math
import time
import subprocess
import threading
import webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Ensure UTF-8 output in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16 GB max local upload

SUPPORTED_VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'webm', 'flv', 'wmv', 'm4v', 'ts', 'gif']
SUPPORTED_AUDIO_FORMATS = ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a', 'opus', 'wma', 'aiff']


def run_command(cmd):
    """Execute a CLI command via subprocess and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return -1, "", str(e)


def get_media_info(filepath):
    """Use ffprobe to inspect video and audio stream details."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(filepath)
    ]
    code, stdout, stderr = run_command(cmd)
    if code != 0 or not stdout:
        return {"error": "Failed to probe file", "details": stderr}

    try:
        data = json.loads(stdout)
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        duration = float(format_info.get("duration", 0.0))
        size_bytes = int(format_info.get("size", 0))
        bit_rate = int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None

        video_stream = next((s for s in streams if s.get("codec_type") == "video" and s.get("codec_name") != "png" and s.get("codec_name") != "mjpeg"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        media_type = "video" if video_stream else ("audio" if audio_stream else "unknown")

        details = {
            "media_type": media_type,
            "duration": duration,
            "duration_formatted": format_seconds(duration),
            "size": size_bytes,
            "size_formatted": format_bytes(size_bytes),
            "bit_rate": bit_rate,
            "format_name": format_info.get("format_name", ""),
            "streams_count": len(streams),
            "has_video": video_stream is not None,
            "has_audio": audio_stream is not None,
        }

        if video_stream:
            details["video"] = {
                "codec": video_stream.get("codec_name", ""),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": eval_fraction(video_stream.get("avg_frame_rate", "0/1")),
                "pixel_format": video_stream.get("pix_fmt", "")
            }

        if audio_stream:
            details["audio"] = {
                "codec": audio_stream.get("codec_name", ""),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels"),
                "channel_layout": audio_stream.get("channel_layout", "")
            }

        return details
    except Exception as e:
        return {"error": f"Error parsing media details: {str(e)}"}


def eval_fraction(frac_str):
    try:
        if "/" in str(frac_str):
            num, den = frac_str.split("/")
            return round(float(num) / float(den), 2) if float(den) != 0 else 0
        return round(float(frac_str), 2)
    except Exception:
        return 0


def format_seconds(seconds):
    if not seconds or seconds < 0:
        return "00:00:00.000"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"


def format_bytes(b):
    if not b:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.2f} {unit}"
        b /= 1024.0
    return f"{b:.2f} PB"


def safe_child_file(directory, filename):
    if (
        not isinstance(filename, str)
        or not filename
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
    ):
        return None

    try:
        base = directory.resolve()
        target = (base / filename).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not target.is_relative_to(base) or not target.is_file():
        return None
    return target


def parse_time_range(start_time, end_time):
    try:
        start_s = float(start_time)
        end_s = float(end_time)
    except (TypeError, ValueError):
        raise ValueError("Start and end times must be valid numbers") from None

    if not math.isfinite(start_s) or not math.isfinite(end_s):
        raise ValueError("Start and end times must be finite numbers")
    if start_s < 0 or end_s <= start_s:
        raise ValueError("End time must be greater than a non-negative start time")
    return start_s, end_s


def parse_non_negative_number(value, field_name):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number") from None
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{field_name} must be a finite non-negative number")
    return parsed


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"success": False, "error": "Uploaded file exceeds the 16 GB limit"}), 413


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        filename = f"media_{int(time.time())}.dat"

    unique_name = f"{time.time_ns()}_{filename}"
    save_path = UPLOAD_DIR / unique_name
    file.save(save_path)

    info = get_media_info(save_path)
    if "error" in info:
        save_path.unlink(missing_ok=True)
        return jsonify({"success": False, "error": info["error"], "details": info.get("details", "")}), 400

    return jsonify({
        "success": True,
        "filename": unique_name,
        "original_filename": file.filename or "",
        "stream_url": f"/media/uploads/{unique_name}",
        "info": info
    })


@app.route("/media/<folder>/<path:filename>")
def stream_media(folder, filename):
    if folder == "uploads":
        base = UPLOAD_DIR
    elif folder == "outputs":
        base = OUTPUT_DIR
    else:
        return jsonify({"error": "File not found"}), 404

    if not safe_child_file(base, filename):
        return jsonify({"error": "File not found"}), 404

    # Support byte ranges for smooth HTML5 video/audio seeking
    return send_from_directory(base, filename, conditional=True)


@app.route("/api/outputs", methods=["GET"])
def list_outputs():
    outputs = []
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            if f.is_file():
                stat = f.stat()
                ext = f.suffix.lstrip(".").lower()
                is_video = ext in SUPPORTED_VIDEO_FORMATS
                is_audio = ext in SUPPORTED_AUDIO_FORMATS
                outputs.append({
                    "name": f.name,
                    "ext": ext,
                    "size": stat.st_size,
                    "size_formatted": format_bytes(stat.st_size),
                    "created_at": stat.st_mtime,
                    "created_at_formatted": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "is_video": is_video,
                    "is_audio": is_audio,
                    "stream_url": f"/media/outputs/{f.name}",
                    "download_url": f"/api/download/{f.name}"
                })
    outputs.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"success": True, "outputs": outputs})


@app.route("/api/download/<path:filename>")
def download_file(filename):
    target = safe_child_file(OUTPUT_DIR, filename)
    if target is None:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(OUTPUT_DIR, target.name, as_attachment=True)


@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    try:
        if sys.platform == "win32":
            os.startfile(str(OUTPUT_DIR))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(OUTPUT_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
        return jsonify({"success": True, "path": str(OUTPUT_DIR)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/output/<path:filename>", methods=["DELETE"])
def delete_output(filename):
    target = safe_child_file(OUTPUT_DIR, filename)
    if target is None:
        return jsonify({"success": False, "error": "File not found"}), 404
    try:
        target.unlink()
        return jsonify({"success": True})
    except OSError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/process", methods=["POST"])
def process_media():
    """
    Unified media processor supporting:
    - action: 'trim_video', 'convert_video', 'extract_audio', 'trim_audio', 'convert_audio'
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Request body must be a JSON object"}), 400

    filename = data.get("filename")
    action = data.get("action")

    if not isinstance(filename, str) or not filename or not isinstance(action, str) or not action:
        return jsonify({"success": False, "error": "Missing filename or action"}), 400

    input_path = safe_child_file(UPLOAD_DIR, filename)
    if input_path is None:
        return jsonify({"success": False, "error": "Input file not found"}), 404

    base_stem = Path(filename).stem
    prefix, separator, original_stem = base_stem.partition("_")
    clean_stem = original_stem if separator and prefix.isdigit() else base_stem

    timestamp = time.time_ns()
    start_time = data.get("start_time")  # seconds float or str
    end_time = data.get("end_time")      # seconds float or str
    target_format = data.get("target_format", "")
    if not isinstance(target_format, str):
        return jsonify({"success": False, "error": "target_format must be a string"}), 400
    target_format = target_format.lower().strip()
    copy_streams = data.get("copy_streams", False)
    if not isinstance(copy_streams, bool):
        return jsonify({"success": False, "error": "copy_streams must be a boolean"}), 400

    cmd = ["ffmpeg", "-y"]

    # 1. ACTION: TRIM VIDEO
    if action == "trim_video":
        if start_time is None or end_time is None:
            return jsonify({"success": False, "error": "start_time and end_time required"}), 400

        try:
            start_s, end_s = parse_time_range(start_time, end_time)
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

        duration_s = end_s - start_s
        out_ext = target_format if target_format else input_path.suffix.lstrip(".").lower()
        if out_ext not in SUPPORTED_VIDEO_FORMATS:
            return jsonify({"success": False, "error": "Unsupported video format"}), 400
        output_filename = f"{clean_stem}_trimmed_{timestamp}.{out_ext}"
        output_path = OUTPUT_DIR / output_filename

        # If copy stream is requested and same container, fast trim
        if copy_streams and out_ext == input_path.suffix.lstrip(".").lower():
            cmd += [
                "-ss", str(start_s),
                "-i", str(input_path),
                "-t", str(duration_s),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(output_path)
            ]
        else:
            # Precise re-encode trim
            cmd += [
                "-ss", str(start_s),
                "-i", str(input_path),
                "-t", str(duration_s),
                "-c:v", "libx264" if out_ext in ["mp4", "mkv", "mov"] else "copy",
                "-crf", "20",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path)
            ]

    # 2. ACTION: CONVERT VIDEO FORMAT
    elif action == "convert_video":
        if not target_format:
            return jsonify({"success": False, "error": "target_format is required"}), 400
        if target_format not in SUPPORTED_VIDEO_FORMATS:
            return jsonify({"success": False, "error": "Unsupported video format"}), 400

        output_filename = f"{clean_stem}_converted_{timestamp}.{target_format}"
        output_path = OUTPUT_DIR / output_filename

        resolution = data.get("resolution", "original") # e.g. "original", "1920:1080", "1280:720", "854:480"
        if not isinstance(resolution, str) or resolution not in {
            "original", "3840:2160", "1920:1080", "1280:720", "854:480"
        }:
            return jsonify({"success": False, "error": "Unsupported output resolution"}), 400
        try:
            quality_crf = int(data.get("crf", 22))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "crf must be an integer from 0 to 51"}), 400
        if not 0 <= quality_crf <= 51:
            return jsonify({"success": False, "error": "crf must be an integer from 0 to 51"}), 400
        quality_crf = str(quality_crf)
        video_codec = data.get("video_codec", "libx264")
        if not isinstance(video_codec, str) or video_codec not in {"libx264", "copy"}:
            return jsonify({"success": False, "error": "Unsupported video codec"}), 400

        cmd += ["-i", str(input_path)]

        # Video filter options
        vf_filters = []
        if resolution != "original" and ":" in resolution:
            w, h = resolution.split(":")
            vf_filters.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")

        if target_format == "gif":
            # High quality palette GIF generation
            try:
                fps = int(data.get("gif_fps", 15))
            except (TypeError, ValueError):
                return jsonify({"success": False, "error": "gif_fps must be an integer from 1 to 60"}), 400
            if not 1 <= fps <= 60:
                return jsonify({"success": False, "error": "gif_fps must be an integer from 1 to 60"}), 400
            vf = f"fps={fps},scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
            cmd += ["-vf", vf, str(output_path)]
        elif target_format == "webm":
            if vf_filters:
                cmd += ["-vf", ",".join(vf_filters)]
            cmd += ["-c:v", "libvpx-vp9", "-crf", quality_crf, "-b:v", "0", "-c:a", "libopus", str(output_path)]
        else:
            if vf_filters:
                cmd += ["-vf", ",".join(vf_filters)]
            if video_codec == "copy":
                cmd += ["-c:v", "copy", "-c:a", "copy"]
            else:
                codec = "libx264" if target_format in ["mp4", "mkv", "mov", "avi", "flv"] else "auto"
                if codec != "auto":
                    cmd += ["-c:v", codec, "-crf", quality_crf, "-preset", "fast"]
                cmd += ["-c:a", "aac", "-b:a", "192k"]
            cmd.append(str(output_path))

    # 3. ACTION: EXTRACT AUDIO FROM VIDEO (WITH OPTIONAL TRIM)
    elif action == "extract_audio":
        audio_format = target_format or data.get("audio_format", "mp3")
        bitrate = data.get("bitrate", "192k")
        do_trim = data.get("trim", False)
        if not isinstance(audio_format, str) or audio_format not in SUPPORTED_AUDIO_FORMATS:
            return jsonify({"success": False, "error": "Unsupported audio format"}), 400
        if not isinstance(bitrate, str) or bitrate not in {"128k", "192k", "256k", "320k"}:
            return jsonify({"success": False, "error": "Unsupported audio bitrate"}), 400
        if not isinstance(do_trim, bool):
            return jsonify({"success": False, "error": "trim must be a boolean"}), 400

        output_filename = f"{clean_stem}_audio_{timestamp}.{audio_format}"
        output_path = OUTPUT_DIR / output_filename

        if do_trim:
            if start_time is None or end_time is None:
                return jsonify({"success": False, "error": "start_time and end_time required when trim is enabled"}), 400
            try:
                start_s, end_s = parse_time_range(start_time, end_time)
            except ValueError as e:
                return jsonify({"success": False, "error": str(e)}), 400
            duration_s = end_s - start_s
            cmd += ["-ss", str(start_s), "-i", str(input_path), "-t", str(duration_s)]
        else:
            cmd += ["-i", str(input_path)]

        # No video stream
        cmd += ["-vn"]

        # Codec configuration per audio format
        if audio_format == "mp3":
            cmd += ["-c:a", "libmp3lame", "-b:a", bitrate]
        elif audio_format == "wav":
            cmd += ["-c:a", "pcm_s16le"]
        elif audio_format == "aac":
            cmd += ["-c:a", "aac", "-b:a", bitrate]
        elif audio_format == "flac":
            cmd += ["-c:a", "flac"]
        elif audio_format == "ogg":
            cmd += ["-c:a", "libvorbis", "-b:a", bitrate]
        elif audio_format == "opus":
            cmd += ["-c:a", "libopus", "-b:a", bitrate]
        elif audio_format == "m4a":
            cmd += ["-c:a", "aac", "-b:a", bitrate]
        elif audio_format == "wma":
            cmd += ["-c:a", "wmav2", "-b:a", bitrate]
        elif audio_format == "aiff":
            cmd += ["-c:a", "pcm_s16be"]
        else:
            cmd += ["-c:a", "copy"]

        cmd.append(str(output_path))

    # 4. ACTION: TRIM AUDIO
    elif action == "trim_audio":
        if start_time is None or end_time is None:
            return jsonify({"success": False, "error": "start_time and end_time required"}), 400

        try:
            start_s, end_s = parse_time_range(start_time, end_time)
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

        duration_s = end_s - start_s
        out_ext = target_format if target_format else input_path.suffix.lstrip(".").lower()
        if out_ext not in SUPPORTED_AUDIO_FORMATS:
            return jsonify({"success": False, "error": "Unsupported audio format"}), 400
        output_filename = f"{clean_stem}_trimmed_{timestamp}.{out_ext}"
        output_path = OUTPUT_DIR / output_filename

        try:
            fade_in = parse_non_negative_number(data.get("fade_in", 0), "fade_in")
            fade_out = parse_non_negative_number(data.get("fade_out", 0), "fade_out")
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        if fade_in > duration_s or fade_out > duration_s:
            return jsonify({"success": False, "error": "Fade durations cannot exceed the selected clip duration"}), 400

        if copy_streams and not fade_in and not fade_out and out_ext == input_path.suffix.lstrip(".").lower():
            cmd += [
                "-ss", str(start_s),
                "-i", str(input_path),
                "-t", str(duration_s),
                "-c", "copy",
                str(output_path)
            ]
        else:
            cmd += ["-ss", str(start_s), "-i", str(input_path), "-t", str(duration_s)]
            af_filters = []
            if fade_in > 0:
                af_filters.append(f"afade=t=in:st=0:d={fade_in}")
            if fade_out > 0:
                out_start = max(0, duration_s - fade_out)
                af_filters.append(f"afade=t=out:st={out_start}:d={fade_out}")

            if af_filters:
                cmd += ["-af", ",".join(af_filters)]

            # Output encoding
            if out_ext == "mp3":
                cmd += ["-c:a", "libmp3lame", "-b:a", "320k"]
            elif out_ext == "wav":
                cmd += ["-c:a", "pcm_s16le"]
            elif out_ext == "flac":
                cmd += ["-c:a", "flac"]
            elif out_ext in ["aac", "m4a"]:
                cmd += ["-c:a", "aac", "-b:a", "256k"]
            elif out_ext == "ogg":
                cmd += ["-c:a", "libvorbis", "-b:a", "256k"]
            elif out_ext == "opus":
                cmd += ["-c:a", "libopus", "-b:a", "192k"]
            elif out_ext == "wma":
                cmd += ["-c:a", "wmav2", "-b:a", "192k"]
            elif out_ext == "aiff":
                cmd += ["-c:a", "pcm_s16be"]

            cmd.append(str(output_path))

    # 5. ACTION: CONVERT AUDIO FORMAT
    elif action == "convert_audio":
        if not target_format:
            return jsonify({"success": False, "error": "target_format is required"}), 400
        if target_format not in SUPPORTED_AUDIO_FORMATS:
            return jsonify({"success": False, "error": "Unsupported audio format"}), 400

        output_filename = f"{clean_stem}_converted_{timestamp}.{target_format}"
        output_path = OUTPUT_DIR / output_filename

        bitrate = data.get("bitrate", "256k")
        sample_rate = data.get("sample_rate", "auto")
        if not isinstance(bitrate, str) or bitrate not in {"128k", "192k", "256k", "320k"}:
            return jsonify({"success": False, "error": "Unsupported audio bitrate"}), 400
        if not isinstance(sample_rate, str) or sample_rate not in {"auto", "44100", "48000", "96000"}:
            return jsonify({"success": False, "error": "Unsupported sample rate"}), 400

        cmd += ["-i", str(input_path)]

        if sample_rate != "auto":
            cmd += ["-ar", str(sample_rate)]

        if target_format == "mp3":
            cmd += ["-c:a", "libmp3lame", "-b:a", bitrate]
        elif target_format == "wav":
            cmd += ["-c:a", "pcm_s16le"]
        elif target_format == "flac":
            cmd += ["-c:a", "flac"]
        elif target_format in ["aac", "m4a"]:
            cmd += ["-c:a", "aac", "-b:a", bitrate]
        elif target_format == "ogg":
            cmd += ["-c:a", "libvorbis", "-b:a", bitrate]
        elif target_format == "opus":
            cmd += ["-c:a", "libopus", "-b:a", bitrate]
        elif target_format == "wma":
            cmd += ["-c:a", "wmav2", "-b:a", bitrate]
        elif target_format == "aiff":
            cmd += ["-c:a", "pcm_s16be"]
        else:
            cmd += ["-c:a", "copy"]

        cmd.append(str(output_path))
    else:
        return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400

    # Execute FFmpeg command
    start_time_proc = time.time()
    code, stdout, stderr = run_command(cmd)
    elapsed = round(time.time() - start_time_proc, 2)

    if code != 0 or not output_path.is_file():
        output_path.unlink(missing_ok=True)
        return jsonify({
            "success": False,
            "error": "FFmpeg processing failed",
            "details": stderr[-4000:]
        }), 500

    out_stat = output_path.stat()
    return jsonify({
        "success": True,
        "message": "Processing completed successfully!",
        "elapsed_seconds": elapsed,
        "output_filename": output_filename,
        "output_size": out_stat.st_size,
        "output_size_formatted": format_bytes(out_stat.st_size),
        "stream_url": f"/media/outputs/{output_filename}",
        "download_url": f"/api/download/{output_filename}"
    })


def open_browser():
    time.sleep(1.2)
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 60)
    print("  >> VORTEX MEDIA STUDIO - LOCAL AUDIO/VIDEO WORKSPACE")
    print("  Output Directory:", OUTPUT_DIR)
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 60)

    # Automatically launch default browser in separate thread unless suppressed
    if os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=5000, debug=False)
