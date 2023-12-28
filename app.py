import os
import openai
import pandas as pd  # Import pandas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("GPT_API_KEY")

# Define the upload folder for files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to send email
def send_email(to_email, file_path):
    from_email = os.getenv("EMAIL_USERNAME")
    app_password = os.getenv("APP_PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = 'Generated post ideas'

    msg.attach(MIMEText('Here are the generated post ideas from a client:', 'plain'))

    with open(file_path, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, app_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-posts', methods=['POST'])
def generate_posts():
    try:
        business_type = request.form['businessType']
        daily_posts = request.form['dailyPosts']
        design_style = request.form['designStyle']
        post_length = request.form['postLength']
        other_topics = request.form['otherTopics']

        logo = request.files['logo']

        # Save uploaded logo
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(logo.filename))
        logo.save(logo_path)

        prompt = f"Generate {daily_posts} facebook posts for a {business_type} business with {design_style} language. The posts should be {post_length} long. Other topics to consider are: {other_topics}."

        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                top_p=1,
                frequency_penalty=1,
                presence_penalty=1
            )
            
            generated_text = response.choices[0].text.strip()

            post_ideas = generated_text.split('\n')

            # Create a DataFrame to store post ideas
            df = pd.DataFrame({'Post Idea': post_ideas})

            # Export the DataFrame to an Excel file
            excel_file = 'output/post-ideas.xlsx'
            df.to_excel(excel_file, index=False)

            send_email('d.felida@outlook.com', excel_file)

            return jsonify({'message': 'Thank you for submitting. Your preferences have been sent.'})

        except Exception as e:
            print(e)
            return jsonify({'error': 'An error occurred.'})

       
    except Exception as e:
        print(e)
        return jsonify({'error': 'An error occurred.'})

if __name__ == '__main__':
    app.run(debug=True)
