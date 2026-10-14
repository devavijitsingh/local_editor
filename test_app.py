import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from app import app, UPLOAD_DIR, OUTPUT_DIR


class MediaStudioTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory()
        cls.video_path = Path(cls.fixture_dir.name) / "test_video.mp4"
        cls.audio_path = Path(cls.fixture_dir.name) / "test_audio.mp3"

        video_result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=320x240:rate=12:duration=8",
                "-f", "lavfi", "-i", "sine=frequency=1000:duration=8",
                "-shortest", "-c:v", "mpeg4", "-c:a", "aac", str(cls.video_path),
            ],
            capture_output=True,
            text=True,
        )
        if video_result.returncode != 0:
            cls.fixture_dir.cleanup()
            raise RuntimeError(f"Could not create video test fixture: {video_result.stderr}")

        audio_result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(cls.video_path), "-vn", "-c:a", "libmp3lame",
                str(cls.audio_path),
            ],
            capture_output=True,
            text=True,
        )
        if audio_result.returncode != 0:
            cls.fixture_dir.cleanup()
            raise RuntimeError(f"Could not create audio test fixture: {audio_result.stderr}")

    @classmethod
    def tearDownClass(cls):
        cls.fixture_dir.cleanup()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.created_uploads = []
        self.created_outputs = []

    def tearDown(self):
        for filename in self.created_uploads:
            (UPLOAD_DIR / filename).unlink(missing_ok=True)
        for filename in self.created_outputs:
            (OUTPUT_DIR / filename).unlink(missing_ok=True)

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'VORTEX', response.data)
        self.assertIn(b'Video Studio', response.data)
        self.assertIn(b'Audio Studio', response.data)

    def test_upload_and_probe_video(self):
        with open(self.video_path, "rb") as f:
            data = {"file": (f, "test_video.mp4")}
            res = self.app.post('/api/upload', data=data, content_type='multipart/form-data')

        self.assertEqual(res.status_code, 200)
        payload = json.loads(res.data)
        self.assertTrue(payload["success"])
        self.assertIn("filename", payload)
        self.assertEqual(payload["info"]["media_type"], "video")
        self.assertTrue(payload["info"]["has_video"])
        self.assertTrue(payload["info"]["has_audio"])
        self.assertGreater(payload["info"]["duration"], 5.0)

        uploaded_filename = payload["filename"]
        self.created_uploads.append(uploaded_filename)

        # Test Action 1: Trim Video
        trim_res = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "trim_video",
            "start_time": 1.0,
            "end_time": 4.0,
            "target_format": "mp4",
            "copy_streams": False
        })
        self.assertEqual(trim_res.status_code, 200)
        trim_data = json.loads(trim_res.data)
        self.assertTrue(trim_data["success"])
        self.assertTrue(Path(OUTPUT_DIR / trim_data["output_filename"]).exists())
        self.created_outputs.append(trim_data["output_filename"])

        # Test Action 2: Convert Video Format
        conv_res = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "convert_video",
            "target_format": "webm",
            "resolution": "854:480",
            "crf": "28"
        })
        self.assertEqual(conv_res.status_code, 200)
        conv_data = json.loads(conv_res.data)
        self.assertTrue(conv_data["success"])
        self.assertTrue(Path(OUTPUT_DIR / conv_data["output_filename"]).exists())
        self.created_outputs.append(conv_data["output_filename"])

        # Test Action 3: Extract Audio from Video
        extract_res = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "extract_audio",
            "target_format": "mp3",
            "bitrate": "192k",
            "trim": True,
            "start_time": 1.5,
            "end_time": 4.5
        })
        self.assertEqual(extract_res.status_code, 200)
        extract_data = json.loads(extract_res.data)
        self.assertTrue(extract_data["success"])
        self.assertTrue(Path(OUTPUT_DIR / extract_data["output_filename"]).exists())
        self.created_outputs.append(extract_data["output_filename"])

    def test_upload_and_probe_audio(self):
        with open(self.audio_path, "rb") as f:
            data = {"file": (f, "test_audio.mp3")}
            res = self.app.post('/api/upload', data=data, content_type='multipart/form-data')

        self.assertEqual(res.status_code, 200)
        payload = json.loads(res.data)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["info"]["media_type"], "audio")

        uploaded_filename = payload["filename"]
        self.created_uploads.append(uploaded_filename)

        # Test Action 4: Trim Audio
        trim_audio_res = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "trim_audio",
            "start_time": 0.5,
            "end_time": 3.5,
            "fade_in": 0.5,
            "fade_out": 0.5
        })
        self.assertEqual(trim_audio_res.status_code, 200)
        trim_audio_data = json.loads(trim_audio_res.data)
        self.assertTrue(trim_audio_data["success"])
        self.assertTrue(Path(OUTPUT_DIR / trim_audio_data["output_filename"]).exists())
        self.created_outputs.append(trim_audio_data["output_filename"])

        # Test audio conversion codecs, including WMA and AIFF encoders.
        for target_format in ("wav", "wma", "aiff"):
            with self.subTest(target_format=target_format):
                conv_audio_res = self.app.post('/api/process', json={
                    "filename": uploaded_filename,
                    "action": "convert_audio",
                    "target_format": target_format,
                })
                self.assertEqual(conv_audio_res.status_code, 200)
                conv_audio_data = json.loads(conv_audio_res.data)
                self.assertTrue(conv_audio_data["success"])
                self.assertTrue(Path(OUTPUT_DIR / conv_audio_data["output_filename"]).exists())
                self.created_outputs.append(conv_audio_data["output_filename"])

    def test_process_rejects_invalid_paths_and_parameters(self):
        traversal = self.app.post('/api/process', json={
            "filename": "../app.py",
            "action": "convert_audio",
            "target_format": "wav",
        })
        self.assertEqual(traversal.status_code, 404)

        with open(self.audio_path, "rb") as f:
            upload = self.app.post(
                '/api/upload',
                data={"file": (f, "validation_audio.mp3")},
                content_type='multipart/form-data',
            )
        self.assertEqual(upload.status_code, 200)
        uploaded_filename = json.loads(upload.data)["filename"]
        self.created_uploads.append(uploaded_filename)

        invalid_time = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "trim_audio",
            "start_time": "not-a-time",
            "end_time": 3,
        })
        self.assertEqual(invalid_time.status_code, 400)

        invalid_format = self.app.post('/api/process', json={
            "filename": uploaded_filename,
            "action": "convert_audio",
            "target_format": "../../app.py",
        })
        self.assertEqual(invalid_format.status_code, 400)

        bad_json_shape = self.app.post('/api/process', json=["not", "an", "object"])
        self.assertEqual(bad_json_shape.status_code, 400)

    def test_download_and_delete_reject_path_traversal(self):
        download = self.app.get('/api/download/..%2Fapp.py')
        self.assertEqual(download.status_code, 404)

        delete = self.app.delete('/api/output/..%5Capp.py')
        self.assertEqual(delete.status_code, 404)

    def test_outputs_listing(self):
        res = self.app.get('/api/outputs')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["outputs"], list)

if __name__ == '__main__':
    unittest.main()
