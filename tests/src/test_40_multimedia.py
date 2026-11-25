import pytest

TERRA = ["mesa-dri-drivers", "mesa-vulkan-drivers", "steam"]


def test_full_ffmpeg_installed(ssh_command):
    ssh_command("rpm -q ffmpeg")
    result = ssh_command("rpm -q ffmpeg-free", check=False)
    assert result.returncode != 0, "ffmpeg-free is installed instead of the full ffmpeg"


def test_hw_video_drivers_installed(ssh_command):
    ssh_command("rpm -q intel-media-driver")
    result = ssh_command(f"rpm -q --qf '%{{vendor}}\\n' {' '.join(TERRA)}")
    # every arch of these, including steam's i686 mesa, must come from terra
    assert set(result.stdout.split()) == {"Terra"}, result.stdout


# encode with ffmpeg, then decode through gstreamer like plasma apps and browsers do
@pytest.mark.parametrize("codec", ["libx264", "libx265"])
def test_patented_codec_roundtrip(ssh_command, codec):
    out = f"/tmp/kuubik-{codec}.mp4"
    ssh_command(
        f"ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc=duration=1:size=320x240 "
        f"-f lavfi -i sine=duration=1 -c:v {codec} -c:a aac {out}"
    )
    ssh_command(f"gst-launch-1.0 -q filesrc location={out} ! decodebin ! fakesink")
