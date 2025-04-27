from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import EmailTracking
import csv
import uuid
from datetime import datetime, timedelta
import io
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils import timezone

# Sender information
SENDER_NAME = "Meet Soni"
SENDER_POSITION = "Business Development Manager"
SENDER_COMPANY = "Meet Solutions"

def home(request):
    # Get all emails for display
    emails = EmailTracking.objects.all().order_by('-sent_date')
    
    # Get statistics
    total_emails = EmailTracking.objects.count()
    sent_emails = EmailTracking.objects.filter(status__in=['sent', 'opened', 'clicked']).count()
    opened_emails = EmailTracking.objects.filter(status='opened').count()
    clicked_emails = EmailTracking.objects.filter(status='clicked').count()
    unopened_emails = EmailTracking.objects.filter(status='sent').count()
    
    context = {
        'emails': emails,
        'total_emails': total_emails,
        'sent_emails': sent_emails,
        'opened_emails': opened_emails,
        'clicked_emails': clicked_emails,
        'unopened_emails': unopened_emails,
    }
    return render(request, 'index.html', context)

@csrf_exempt
def import_emails(request):
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        imported_emails = []
        for row in reader:
            tracking_id = str(uuid.uuid4())
            email = EmailTracking.objects.create(
                company_name=row['Company Name'],
                website=row['Website'],
                industry=row['Industry'],
                location=row['Location'],
                followers=row['Followers'],
                description=row['Description'],
                email=row['email'],
                tracking_id=tracking_id,
                status='unopened'
            )
            imported_emails.append({
                'company_name': email.company_name,
                'email': email.email,
                'status': email.status,
                'sent_date': email.sent_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'status': 'success',
            'emails': imported_emails
        })
    return JsonResponse({'status': 'error', 'message': 'No file uploaded'})

@csrf_exempt
def send_emails(request):
    if request.method == 'POST':
        # Get all emails with status 'unopened'
        emails_to_send = EmailTracking.objects.filter(status='unopened')
        
        # SMTP settings
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "meets3591@gmail.com"
        smtp_password = "worbspgwmiuuigqy"
        
        try:
            # Create SMTP connection
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            for email_tracking in emails_to_send:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = email_tracking.email
                msg['Subject'] = f"Partnership Opportunity with {email_tracking.company_name}"
                
                # Generate tracking URLs
                tracking_url = f"http://127.0.0.1:8000/track-cta/{email_tracking.tracking_id}/"
                tracking_pixel_url = f"http://127.0.0.1:8000/track-email/{email_tracking.tracking_id}/"
                
                # Render email template
                html_content = render_to_string('email_template.html', {
                    'company_name': email_tracking.company_name,
                    'industry': email_tracking.industry,
                    'location': email_tracking.location,
                    'email': email_tracking.email,
                    'tracking_url': tracking_url,
                    'tracking_pixel_url': tracking_pixel_url,
                    'sender_name': SENDER_NAME,
                    'sender_position': SENDER_POSITION,
                    'sender_company': SENDER_COMPANY
                })
                
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send email
                server.send_message(msg)
                
                # Update status to sent
                email_tracking.status = 'sent'
                email_tracking.sent_date = timezone.now()
                email_tracking.save()
            
            server.quit()
            return JsonResponse({'status': 'success', 'message': 'Emails sent successfully'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def track_email_open(request, tracking_id):
    try:
        email_tracking = EmailTracking.objects.get(tracking_id=tracking_id)
        if email_tracking.status == 'sent':
            email_tracking.status = 'opened'
            email_tracking.opened_date = timezone.now()
            email_tracking.save()
        # Return a 1x1 transparent pixel
        return HttpResponse(
            bytes.fromhex('47494638396101000100800000dbdbdb00000021f90401000000002c00000000010001000002024401003b'),
            content_type='image/gif'
        )
    except EmailTracking.DoesNotExist:
        return HttpResponse('Not found')

@csrf_exempt
def track_cta_click(request, tracking_id):
    try:
        email_tracking = EmailTracking.objects.get(tracking_id=tracking_id)
        # First mark as opened if not already
        if email_tracking.status == 'sent':
            email_tracking.status = 'opened'
            email_tracking.opened_date = timezone.now()
        # Then mark as clicked and increment click count
        email_tracking.status = 'clicked'
        email_tracking.clicked_date = timezone.now()
        email_tracking.click_count += 1
        email_tracking.save()
        # Return a blank response with 204 No Content status
        return HttpResponse(status=204)
    except EmailTracking.DoesNotExist:
        return HttpResponse('Not found')

def update_cold_leads(request):
    # Update emails that haven't been opened in 7 days to cold leads
    seven_days_ago = datetime.now() - timedelta(days=7)
    EmailTracking.objects.filter(
        status='sent',
        sent_date__lt=seven_days_ago
    ).update(status='unseen')
    return JsonResponse({'status': 'success'})

@csrf_exempt
def delete_email(request, tracking_id):
    if request.method == 'POST':
        try:
            email_tracking = EmailTracking.objects.get(tracking_id=tracking_id)
            email_tracking.delete()
            return JsonResponse({'status': 'success', 'message': 'Email deleted successfully'})
        except EmailTracking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Email not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}) 