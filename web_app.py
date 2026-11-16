import os
import subprocess
import tempfile
import imageio_ffmpeg
import streamlit as st

st.set_page_config(
    page_title="LoopScape - Relaksasi Tidur 1 Jam",
    page_icon="🌙",
    layout="centered",
)

st.title("🌙 LoopScape Web")
st.write(
    "Ubah video pendek (kamera diam) menjadi video relaksasi tidur berdurasi"
    " **1 jam** lengkap dengan transisi halus dan suara konstan."
)

# Fitur unggah video dari perangkat apa saja (HP, Mac, Windows)
uploaded_file = st.file_uploader(
    "1. Pilih atau unggah video pendek Anda", type=["mp4", "mov", "mkv", "avi"]
)

if uploaded_file is not None:
  st.video(uploaded_file)

  if st.button("2. Proses Jadi Video Relaksasi 1 Jam", type="primary"):
    with st.spinner(
        "Sedang meracik video relaksasi 1 jam... Proses ini memakan waktu"
        " sekitar 1-2 menit, mohon jangan tutup halaman ini."
    ):
      try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        # Membuat folder sementara untuk memproses video di server/komputer
        with tempfile.TemporaryDirectory() as temp_dir:
          input_path = os.path.join(temp_dir, "input_video.mp4")
          with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

          temp_clip = os.path.join(temp_dir, "temp_clip.mp4")
          temp_1min = os.path.join(temp_dir, "temp_1min.mp4")
          list_file = os.path.join(temp_dir, "temp_list.txt")

          base_name = os.path.splitext(uploaded_file.name)[0]
          output_filename = f"{base_name}_1Jam_Relaksasi.mp4"
          output_path = os.path.join(temp_dir, output_filename)

          # TAHAP 1: Ambil detik 5 sampai 7.5, kunci posisi kamera, dan perlambat sedikit
          cmd_clip = [
              ffmpeg_exe,
              "-y",
              "-ss",
              "5",
              "-t",
              "2.5",
              "-i",
              input_path,
              "-filter_complex",
              "[0:v]deshake=edge=mirror,setpts=1.2*PTS,fps=30,format=yuv420p[v];[0:a]atempo=0.833,aresample=44100[a]",
              "-map",
              "[v]",
              "-map",
              "[a]",
              "-c:v",
              "libx264",
              "-preset",
              "veryfast",
              "-crf",
              "22",
              "-c:a",
              "aac",
              "-b:a",
              "128k",
              temp_clip,
          ]
          subprocess.run(cmd_clip, check=True)

          # TAHAP 2: Susun 25 klip dengan efek Crossfade menjadi 1 menit mulus
          inputs = []
          filter_parts = []
          num_loops = 25
          dur = 3.0
          fade = 0.6

          for i in range(num_loops):
            inputs.extend(["-i", temp_clip])

          v_prev = "[0:v]"
          a_prev = "[0:a]"
          for i in range(1, num_loops):
            offset = round(i * (dur - fade), 2)
            v_next = f"[v{i}]" if i < num_loops - 1 else "[vout]"
            a_next = f"[a{i}]" if i < num_loops - 1 else "[aout]"
            filter_parts.append(
                f"{v_prev}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset}{v_next}"
            )
            filter_parts.append(f"{a_prev}[{i}:a]acrossfade=d={fade}{a_next}")
            v_prev = v_next
            a_prev = a_next

          cmd_1min = (
              [ffmpeg_exe, "-y"]
              + inputs
              + [
                  "-filter_complex",
                  ";".join(filter_parts),
                  "-map",
                  "[vout]",
                  "-map",
                  "[aout]",
                  "-t",
                  "60",
                  "-c:v",
                  "libx264",
                  "-preset",
                  "veryfast",
                  "-crf",
                  "22",
                  "-pix_fmt",
                  "yuv420p",
                  "-c:a",
                  "aac",
                  "-b:a",
                  "128k",
                  temp_1min,
              ]
          )
          subprocess.run(cmd_1min, check=True)

          # TAHAP 3: Gandakan blok 1 menit menjadi 60 menit (1 jam)
          one_min_clean = temp_1min.replace("\\", "/")
          with open(list_file, "w", encoding="utf-8") as f:
            for _ in range(60):
              f.write(f"file '{one_min_clean}'\n")

          cmd_final = [
              ffmpeg_exe,
              "-y",
              "-f",
              "concat",
              "-safe",
              "0",
              "-i",
              list_file,
              "-c",
              "copy",
              output_path,
          ]
          subprocess.run(cmd_final, check=True)

          # Membaca hasil akhir untuk tombol unduh (Download) di browser
          with open(output_path, "rb") as final_file:
            video_bytes = final_file.read()

        st.success("✅ Video relaksasi 1 jam berhasil dibuat!")
        st.download_button(
            label="⬇️ Unduh Video 1 Jam Sekarang",
            data=video_bytes,
            file_name=output_filename,
            mime="video/mp4",
        )
      except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses video: {e}")