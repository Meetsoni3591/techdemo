import pandas as pd
from jinja2 import Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import random

# Step 1: Read the CSV file containing emails and dynamic data
def read_csv(file_path):
    """Read the CSV file and extract company information"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        return None

# Step 2: Create the email content using Jinja2
def create_email_content(data):
    """Create personalized email content using Jinja2 template"""
    template_string = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Partnership Opportunity</title>
    </head>
    <body>
        <h2>Dear {{ company_name }} Team,</h2>
        <p>I hope this email finds you well. I came across your company while researching {{ industry }} companies in {{ location }}, and I was impressed by your work.</p>
        <p>We are looking to establish partnerships with innovative companies in the {{ industry }} space, and we believe there could be great synergy between our organizations.</p>
        <p>Would you be open to a brief conversation to explore potential collaboration opportunities?</p>
        <p>Looking forward to your response.</p>
        <p>Best regards,<br>
        {{ sender_name }}<br>
        {{ sender_position }}<br>
        {{ sender_company }}</p>
    </body>
    </html>
    """
    
    template = Template(template_string)
    return template.render(data)

# Step 3: Send the email automatically using smtplib
def send_email(recipient_email, subject, html_content):
    """Send email using SMTP"""
    sender_email = "meets3591@gmail.com"
    sender_password = "worbspgwmiuuigqy"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print(f"✅ Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email to {recipient_email}: {str(e)}")
        return False

# Step 4: Automate the process for each recipient in the CSV
def automate_email_sending():
    """Automate email sending process"""
    # Read the CSV data
    data_df = read_csv('linkedin_companies_with_emails.csv')
    if data_df is None:
        return
    
    # Sender's information
    sender_info = {
        'sender_name': 'Meet Soni',
        'sender_position': 'Sales Manager',
        'sender_company': 'ABC Agency'
    }
    
    # Track sent and failed emails
    sent_emails = []
    failed_emails = []
    
    # Loop through each row and send emails
    for index, row in data_df.iterrows():
        # Get email from 'Dumpy Emails' column
        recipient_email = row['Dumpy Emails'].strip()
        if not recipient_email or recipient_email == 'No emails found':
            continue
            
        # Prepare email data
        email_data = {
            'company_name': row['Company Name'],
            'industry': row['Industry'],
            'location': row['Location'],
            **sender_info
        }
        
        # Create email content
        email_content = create_email_content(email_data)
        subject = f"Partnership Opportunity with {row['Company Name']}"
        
        # Send email with delay
        if send_email(recipient_email, subject, email_content):
            sent_emails.append({
                'Company': row['Company Name'],
                'Email': recipient_email
            })
        else:
            failed_emails.append({
                'Company': row['Company Name'],
                'Email': recipient_email
            })
        
        # Add random delay between emails (30-60 seconds)
        delay = random.uniform(30, 60)
        print(f"⏳ Waiting {delay:.1f} seconds before next email...")
        time.sleep(delay)
    
    # Save results to CSV files
    if sent_emails:
        pd.DataFrame(sent_emails).to_csv('sent_dummy_emails.csv', index=False)
        print(f"\n✅ Sent emails log saved to sent_dummy_emails.csv")
    
    if failed_emails:
        pd.DataFrame(failed_emails).to_csv('failed_dummy_emails.csv', index=False)
        print(f"⚠️ Failed emails log saved to failed_dummy_emails.csv")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"Total emails attempted: {len(sent_emails) + len(failed_emails)}")
    print(f"Successfully sent: {len(sent_emails)}")
    print(f"Failed to send: {len(failed_emails)}")

if __name__ == "__main__":
    automate_email_sending()
