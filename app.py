import streamlit as st
import subprocess
import shutil
import os
import time
from pathlib import Path
import base64

# ========================
# CONSTANTS AND SETTINGS
# ========================
INPUT_DIR = Path("temp_inputs")
FRAME_DIR = Path("temp_frames")
OUTPUT_DIR = Path("outputs")

# ========================
# CORE FUNCTIONS
# ========================
def setup_directories():
    INPUT_DIR.mkdir(exist_ok=True)
    FRAME_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

def validate_environment():
    return all([
        any(shutil.which(x) for x in ["primitive", "primitive.exe"]),
        any(shutil.which(x) for x in ["magick", "convert"])
    ])

def generate_artwork(params):
    """Execute primitive command with all parameters"""
    cmd = [
        "primitive" + (".exe" if os.name == "nt" else ""),
        "-i", str(params["input_path"]),
        "-o", str(params["output_path"]),
        "-n", str(params["num_shapes"]),
        "-m", params["mode"],
        "-rep", str(params["rep"]),
        "-nth", str(params["nth"]),
        "-r", str(params["resize"]),
        "-s", str(params["output_size"]),
        "-a", str(params["alpha"]),
        "-bg", params["bg_color"].lstrip("#") or "ffffff",
        "-j", str(params["workers"])
    ]
    
    if params["verbose"]: cmd.append("-v")
    if params["very_verbose"]: cmd.append("-vv")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return " ".join(cmd)

def create_gif(base_name):
    """Create animated GIF from frames"""
    output_path = OUTPUT_DIR / f"{base_name}_animation.gif"
    cmd = [
        "magick" if shutil.which("magick") else "convert",
        "-delay", "10",
        "-loop", "0",
        str(FRAME_DIR / "*.png"),
        str(output_path)
    ]
    subprocess.run(cmd, check=True)
    return output_path

# ========================
# STREAMLIT UI
# ========================
st.set_page_config(page_title="Primitive Art Generator", layout="wide")

# Animated Header
st.markdown("""
    <div style='text-align:center; padding: 2rem; 
    background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
    border-radius: 15px; border: 3px solid #2c3e50;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    margin-bottom: 2rem;'>
        <h1 style='color: white; font-size: 2.5rem; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
        🎨✨ Primitive Art Generator ✨🎨
        </h1>
        <p style='color: #f7fff7; font-size: 1.2rem;'>
        Transform your images into geometric masterpieces! 🖼️➡️🔷🔶
        </p>
    </div>
""", unsafe_allow_html=True)

# Main Columns
left_col, right_col = st.columns([0.3, 0.7], gap="medium")

# Control Panel
with left_col:
    with st.form("config_form"):
        st.markdown("### ⚙️🔧 Settings Panel")
        uploaded_file = st.file_uploader("📤 Upload Image", type=["png", "jpg", "jpeg"])
        
        # Core parameters
        num_shapes = st.slider("🔢 Number of Shapes (-n)", 10, 1000, 100)
        mode = st.selectbox("🔶 Shape Mode (-m)", [
            "0=combo 🎲", "1=triangle 🔺", "2=rect ▭", "3=ellipse 🟠", 
            "4=circle ⭕", "5=rotatedrect 🔄", "6=beziers 🎢", 
            "7=rotatedellipse 🌗", "8=polygon 🔷"
        ], index=1).split("=")[0]
        
        # Color and transparency
        bg_color = st.color_picker("🎨 Background Color (-bg)", "#ffffff")
        alpha = st.slider("🌈 Alpha (-a)", 0, 255, 128)
        
        # Image sizing
        resize = st.number_input("📏 Resize Input (-r)", 64, 2048, 256)
        output_size = st.number_input("🖼️ Output Size (-s)", 128, 4096, 1024)
        
        # Advanced options
        with st.expander("⚡ Advanced Options ⚡"):
            rep = st.number_input("🔄 Repeat (-rep)", 0, 100, 0)
            nth = st.slider("🎞️ Frame Interval (-nth)", 1, 100, 1)
            workers = st.number_input("👥 Workers (-j)", 0, 16, 0)
            output_format = st.selectbox("📤 Output Format", 
                                       ["PNG", "JPG", "SVG", "GIF 🎬"])
            verbose = st.checkbox("📝 Verbose (-v)")
            very_verbose = st.checkbox("📣 Very Verbose (-vv)")
        
        submitted = st.form_submit_button("🚀🌟 Generate Artwork 🌟🚀")

# Preview Section
with right_col:
    st.markdown("### 🖼️🎨 Art Preview")
    
    # Equal image preview columns
    preview_col1, preview_col2 = st.columns(2)
    
    with preview_col1:
        st.markdown("#### 📥 Input Preview")
        input_preview = st.empty()
    
    with preview_col2:
        st.markdown("#### 📤 Output Preview")
        output_preview = st.empty()
    
    st.markdown("---")
    st.markdown("### ⚡ Generated Command ⚡")
    cmd_display = st.empty()
    
    download_section = st.container()

# Processing Logic
if submitted and uploaded_file:
    if not validate_environment():
        st.error("❌ Missing required dependencies: Install Primitive and ImageMagick")
        st.stop()
    
    setup_directories()
    start_time = time.time()
    
    try:
        # Prepare paths
        input_path = INPUT_DIR / uploaded_file.name
        base_name = Path(uploaded_file.name).stem
        output_path = OUTPUT_DIR / f"{base_name}_result.png"
        
        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Show input preview
        input_preview.image(str(input_path), use_container_width=True)
        
        # Generate artwork
        params = {
            "input_path": input_path,
            "output_path": FRAME_DIR / "%04d.png" if output_format.startswith("GIF") else output_path,
            "num_shapes": num_shapes,
            "mode": mode,
            "rep": rep,
            "nth": nth,
            "resize": resize,
            "output_size": output_size,
            "alpha": alpha,
            "bg_color": bg_color,
            "workers": workers,
            "verbose": verbose,
            "very_verbose": very_verbose
        }
        
        with st.spinner("🎨 Creating your masterpiece... Please wait ⏳"):
            command = generate_artwork(params)
            
            # Handle GIF conversion
            final_output = output_path
            if output_format.startswith("GIF"):
                final_output = create_gif(base_name)
                for frame in FRAME_DIR.glob("*.png"):
                    frame.unlink()
            
            # Display results
            output_preview.image(str(final_output), use_container_width=True)
            
            # Download link
            with open(final_output, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'''
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="data:file/{output_format.split()[0].lower()};base64,{b64}" 
                       download="{final_output.name}" 
                       style="display: inline-block; padding: 1rem 2rem; 
                              background: linear-gradient(135deg, #4ecdc4, #45b7af);
                              color: white; border-radius: 25px;
                              text-decoration: none; font-weight: bold;
                              box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                              transition: transform 0.2s ease;">
                       ⬇️✨ Download Your Artwork ✨⬇️
                    </a>
                </div>
                '''
                download_section.markdown(href, unsafe_allow_html=True)
            
            # Show command
            cmd_display.code(command)

    except subprocess.CalledProcessError as e:
        st.error(f"❌ Processing error: {e.stderr.splitlines()[-1]}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
    finally:
        shutil.rmtree(INPUT_DIR, ignore_errors=True)
        shutil.rmtree(FRAME_DIR, ignore_errors=True)

# Style Enhancements
st.markdown("""
<style>
    [data-testid="stForm"] {
        border: 2px solid #4ecdc4;
        border-radius: 15px;
        padding: 1.5rem;
        background: rgba(255,255,255,0.95);
    }
    [data-testid="stImage"] {
        border: 2px solid #4ecdc4;
        border-radius: 15px;
        padding: 10px;
        background: white;
        margin-bottom: 1rem;
    }
    [data-testid="stImage"] img {
        border-radius: 10px;
        object-fit: contain;
    }
    .stSpinner > div > div {
        border-top-color: #4ecdc4 !important;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)