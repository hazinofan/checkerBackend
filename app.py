from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
import csv
import os
import tqdm

app = Flask(__name__)
CORS(app)


# SMTP checker function
def process_credentials(file, host, port):
    try:
        # Determine file type based on extension
        file_ext = os.path.splitext(file.filename)[1].lower()

        credentials = []

        if file_ext == ".txt":
            # Process TXT file
            lines = file.read().decode("utf-8").splitlines()
            credentials = [line.strip().split(",") for line in lines]

        elif file_ext == ".csv":
            # Process CSV file
            decoded_file = file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            credentials = [row for row in reader]

        else:
            return {
                "error": "Unsupported file format. Please use a TXT or CSV file."
            }, []

        success = []  # Successful logins
        failed = []  # Failed logins

        # Process each credential
        for email, password in tqdm.tqdm(credentials):
            try:
                # Attempt SMTP login
                server = smtplib.SMTP(host, port)
                server.ehlo()
                server.starttls()
                server.login(email, password)
                success.append({"email": email, "status": "success"})
            except smtplib.SMTPAuthenticationError:
                failed.append(
                    {
                        "email": email,
                        "status": "failed",
                        "error": "Authentication Error",
                    }
                )
            except Exception as ex:
                failed.append({"email": email, "status": "failed", "error": str(ex)})

        return {"success": success, "failed": failed}, None

    except Exception as e:
        return None, str(e)


# Flask route to handle the file upload
@app.route("/api/checker", methods=["POST"])
def checker():
    try:
        host = request.form.get("host", "smtp.gmail.com")
        port = int(request.form.get("port", 587))
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file provided."}), 400

        results, error = process_credentials(file, host, port)
        if error:
            return jsonify({"error": error}), 500

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)