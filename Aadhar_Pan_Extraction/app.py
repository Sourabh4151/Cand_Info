# import os
# import re
# from flask import Flask, request, jsonify, render_template
# from google.cloud import vision
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# app = Flask(__name__)

# # ✅ Ensure Google Cloud credentials are correctly set
# GOOGLE_CLOUD_CREDENTIALS = "google_cloud_credentials.json"
# if not os.path.exists(GOOGLE_CLOUD_CREDENTIALS):
#     raise FileNotFoundError(f"Google Cloud credentials file not found: {GOOGLE_CLOUD_CREDENTIALS}")
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CREDENTIALS

# # ✅ Initialize Google Cloud Vision client
# try:
#     vision_client = vision.ImageAnnotatorClient()
# except Exception as e:
#     raise RuntimeError(f"Failed to initialize Google Vision client: {e}")

# # ✅ Initialize Google Sheets API
# SHEET_ID = "1Kj28HLSkQYRkQZUWfdec1Q7NyH__70wNQ8rZ-hyTWZs"
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# try:
#     creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CLOUD_CREDENTIALS, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open_by_key(SHEET_ID).sheet1
# except Exception as e:
#     raise RuntimeError(f"Failed to connect to Google Sheets: {e}")

# # ✅ Function to extract text from images
# def extract_text(image_path):
#     try:
#         with open(image_path, "rb") as image_file:
#             content = image_file.read()
#         image = vision.Image(content=content)
#         response = vision_client.text_detection(image=image)
#         texts = response.text_annotations
#         return texts[0].description if texts else ""
#     except Exception as e:
#         print(f"Error extracting text: {e}")
#         return "Error extracting text"

# # ✅ Functions to parse details
# def parse_aadhar_front(text):
#     name = re.search(r"([^\n]+)\n([^\n]+)\nजन्म तिथि / DOB", text) # Look for two lines before DOB
#     # dob = re.search(r"जन्म तिथि / DOB : (\d{2}/\d{2}/\d{4})", text)
#     dob = re.search(r"जन्म तिथि / DOB : (\d{2}/\d{2}/\d{4})\n(महिला|पुरुष|FEMALE|MALE)", text)
#     aadhar_number = re.search(r"\d{4} \d{4} \d{4}", text)
#     return {
#         "Name": name.group(2).strip() if name else "Not Found",
#         "DOB": dob.group(1) if dob else "Not Found",
#         "Aadhar Number": aadhar_number.group(0) if aadhar_number else "Not Found",
#     }


# def parse_aadhar_back(text):
#     """
#     Extracts address information from a text string (Aadhar card back side OCR text).
#     Returns a dictionary with "Address" key containing the full address.
#     """
#     address_patterns = [
#         r"(Address|Addr):(.*?)(?=\n\d{4}|\Z)",
#         r"(House|Flat|Building) ?No\.?:? ?(.*?)(?=,|$)",
#         r"((Village|Town|City):? ?(.*?)(?=,|$))",
#         r"(Post (Office|:|)) ?(.*?)(?=,|$)",
#         r"(District|Dist\.|Dist):? ?(.*?)(?=,|$)",
#         r"(State):? ?(.*?)(?=,|$)",
#         r"(PIN|Pin Code):? ?(\d{6})",
#         r"(C/O):? ?(.*?)(?=,|$)", #added to capture C/O
#     ]

#     address_match = re.search(address_patterns[0], text, re.IGNORECASE | re.DOTALL)
#     if address_match:
#         address_block = address_match.group(2).strip()
#         address_lines = [line.strip() for line in address_block.split('\n') if line.strip()]
#         address = ', '.join(part.strip() for part in address_lines).replace(', ,', ',').strip(', ')
#         address = re.sub(r'(\w+-)\s*,', r'\1', address)
#         return {"Address": address}
    
#     return {"Address": "Not Found"}



# def parse_pan(text):
#     pan_number = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
#     return {"PAN Number": pan_number.group(0) if pan_number else "Not Found"}

# # ✅ Routes
# @app.route("/", methods=["GET"])
# def home():
#     return render_template("upload.html")

# @app.route("/upload", methods=["POST"])
# def upload_file():
#     try:
#         if "aadhar_front" not in request.files or "aadhar_back" not in request.files or "pan_card" not in request.files:
#             return jsonify({"error": "Please upload all required files"}), 400
        
#         upload_folder = "./uploads"
#         os.makedirs(upload_folder, exist_ok=True)
        
#         file_paths = {}
#         for file_key in ["aadhar_front", "aadhar_back", "pan_card"]:
#             file = request.files[file_key]
#             if file.filename == "":
#                 return jsonify({"error": f"No file selected for {file_key}"}), 400
            
#             file_path = os.path.join(upload_folder, file.filename)
#             file.save(file_path)
#             file_paths[file_key] = file_path


#        # ✅ Extract form data
#         profile = request.form.get("profile", "Not Provided")
#         mobile_number = request.form.get("mobile_number", "Not Provided")
#         job_location = request.form.get("job_location", "Not Provided")

#         # ✅ Extract details from images
#         front_text = extract_text(file_paths["aadhar_front"])
#         back_text = extract_text(file_paths["aadhar_back"])
#         pan_text = extract_text(file_paths["pan_card"])

#         front_details = parse_aadhar_front(front_text)
#         back_details = parse_aadhar_back(back_text)
#         pan_details = parse_pan(pan_text)

#         # ✅ Store details in Google Sheet
#         try:
#          sheet.append_row([
#             front_details["Name"],
#             front_details["DOB"],
#             front_details["Aadhar Number"],
#             back_details["Address"],
#             pan_details["PAN Number"],
#             profile,
#             mobile_number,
#             job_location
#         ])
#         except Exception as e:
#             print(f"Google Sheets error: {e}")
#             return jsonify({"error": "Failed to store data in Google Sheets"}), 500

#         return jsonify({
#             "message": "Details uploaded successfully to Google Sheets!",
#             "data": {
#                 "Profile": profile,
#                 "Mobile Number": mobile_number,
#                 "Job Location": job_location,
#                 "Aadhar Front": front_details,
#                 "Aadhar Back": back_details,
#                 "PAN Card": pan_details
#             }
#         }), 200

#     except Exception as e:
#         print(f"Internal Server Error: {e}")
#         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True)

import os
import re
from flask import Flask, request, jsonify, render_template
from google.cloud import vision
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# ✅ Ensure Google Cloud credentials are correctly set
GOOGLE_CLOUD_CREDENTIALS = "google_cloud_credentials.json"
if not os.path.exists(GOOGLE_CLOUD_CREDENTIALS):
    raise FileNotFoundError(f"Google Cloud credentials file not found: {GOOGLE_CLOUD_CREDENTIALS}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CREDENTIALS

# ✅ Initialize Google Cloud Vision client
try:
    vision_client = vision.ImageAnnotatorClient()
except Exception as e:
    raise RuntimeError(f"Failed to initialize Google Vision client: {e}")

# ✅ Initialize Google Sheets API
SHEET_ID = "1Kj28HLSkQYRkQZUWfdec1Q7NyH__70wNQ8rZ-hyTWZs"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CLOUD_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    raise RuntimeError(f"Failed to connect to Google Sheets: {e}")

# ✅ Function to extract text from images
def extract_text(image_path):
    try:
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        texts = response.text_annotations
        return texts[0].description if texts else ""
    except Exception as e:
        print(f"Error extracting text: {e}")
        return "Error extracting text"

# ✅ Functions to parse details
def parse_aadhar_front(text):
    name = re.search(r"([^\n]+)\n([^\n]+)\nजन्म तिथि / DOB", text) # Look for two lines before DOB
    # dob = re.search(r"जन्म तिथि / DOB : (\d{2}/\d{2}/\d{4})", text)
    dob = re.search(r"जन्म तिथि / DOB : (\d{2}/\d{2}/\d{4})\n(महिला|पुरुष|FEMALE|MALE)", text)
    aadhar_number = re.search(r"\d{4} \d{4} \d{4}", text)
    return {
        "Name": name.group(2).strip() if name else "Not Found",
        "DOB": dob.group(1) if dob else "Not Found",
        "Aadhar Number": aadhar_number.group(0) if aadhar_number else "Not Found",
    }

def parse_aadhar_back(text):
    """
    Extracts address information from a text string (Aadhar card back side OCR text).
    Returns a dictionary with "Address" key containing the full address.
    """
    address_patterns = [
        r"(Address|Addr):(.*?)(?=\n\d{4}|\Z)",
        r"(House|Flat|Building) ?No\.?:? ?(.*?)(?=,|$)",
        r"((Village|Town|City):? ?(.*?)(?=,|$))",
        r"(Post (Office|:|)) ?(.*?)(?=,|$)",
        r"(District|Dist\.|Dist):? ?(.*?)(?=,|$)",
        r"(State):? ?(.*?)(?=,|$)",
        r"(PIN|Pin Code):? ?(\d{6})",
        r"(C/O):? ?(.*?)(?=,|$)", #added to capture C/O
    ]

    address_match = re.search(address_patterns[0], text, re.IGNORECASE | re.DOTALL)
    if address_match:
        address_block = address_match.group(2).strip()
        address_lines = [line.strip() for line in address_block.split('\n') if line.strip()]
        address = ', '.join(part.strip() for part in address_lines).replace(', ,', ',').strip(', ')
        address = re.sub(r'(\w+-)\s*,', r'\1', address)
        return {"Address": address}
    
    return {"Address": "Not Found"}

def parse_pan(text):
    pan_number = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
    return {"PAN Number": pan_number.group(0) if pan_number else "Not Found"}

# ✅ Routes
@app.route("/", methods=["GET"])
def home():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "aadhar_front" not in request.files or "aadhar_back" not in request.files or "pan_card" not in request.files:
            return jsonify({"error": "Please upload all required files"}), 400
        
        upload_folder = "./uploads"
        os.makedirs(upload_folder, exist_ok=True)
        
        file_paths = {}
        for file_key in ["aadhar_front", "aadhar_back", "pan_card"]:
            file = request.files[file_key]
            if file.filename == "":
                return jsonify({"error": f"No file selected for {file_key}"}), 400
            
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
            file_paths[file_key] = file_path

       # ✅ Extract form data
        profile = request.form.get("profile", "Not Provided")
        mobile_number = request.form.get("mobile_number", "Not Provided")
        job_location = request.form.get("job_location", "Not Provided")

        # ✅ Extract details from images
        front_text = extract_text(file_paths["aadhar_front"])
        back_text = extract_text(file_paths["aadhar_back"])
        pan_text = extract_text(file_paths["pan_card"])

        front_details = parse_aadhar_front(front_text)
        back_details = parse_aadhar_back(back_text)
        pan_details = parse_pan(pan_text)

        # ✅ Store details in Google Sheet
        try:
            sheet.append_row([
                front_details["Name"],
                front_details["DOB"],
                front_details["Aadhar Number"],
                back_details["Address"],
                pan_details["PAN Number"],
                profile,
                mobile_number,
                job_location
            ])
        except Exception as e:
            print(f"Google Sheets error: {e}")
            return jsonify({"error": "Failed to store data in Google Sheets"}), 500

        return jsonify({
            "message": "Details uploaded successfully to Google Sheets!",
            "data": {
                "Profile": profile,
                "Mobile Number": mobile_number,
                "Job Location": job_location,
                "Aadhar Front": front_details,
                "Aadhar Back": back_details,
                "PAN Card": pan_details
            }
        }), 200

    except Exception as e:
        print(f"Internal Server Error: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)