from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
   

def send_creation_email(email, password):
    
    try:
        title = 'Accounts profile creation'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = f'Dear user your registration to Smart nyumba is successful. Use to login use credentials: username {email}, password {password}'
        
        html_content = render_to_string("index.html", {'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False
   
# def send_otp_message(otp, email):
    
#     try:
#         title = 'Registration OTP'
#         email_subject = title
#         EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
#         to = email
#         message = 'Account verification otp is: '
        
#         html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
#         email = EmailMultiAlternatives(
#             email_subject,
#             html_content,
#             EBIASHARA_EMAIL,
#             [to]
#         )
#         email.attach_alternative(html_content, "text/html")
#         if email.send():
            
#             print("email sending process done...")
            
#             return True
#         return False
#     except Exception as e:
#        print('ERROR:', str(e))
#        return False


def send_forgot_password_otp(otp, email):
    
    try:
        title = 'Forgot Password OTP'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = 'Forgot password reset otp is: '
        
        html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False
    
def approve_accounts_profile(otp, email, accounts_email):
    
    try:
        title = 'Accounts Profile Approval'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = f'Dear admin use the provideds otp to approve accounts profile for user {accounts_email}. Thank you!'
        
        html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False

def new_subscription_email(email):
    
    try:
        title = 'Subscription Renewal'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = 'Dear user your subscription has been renewed.'
        
        html_content = render_to_string("email.html", {'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False


#---user---
def send_creation_email(email, password):
    
    try:
        title = 'Accounts profile creation'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = f'Dear user your registration to Smart nyumba is successful. Use to login use credentials: username {email}, password {password}'
        
        html_content = render_to_string("index.html", {'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False
   
def send_otp_message(otp, email):
    
    try:
        title = 'Registration OTP'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = 'Account verification otp is: '
        
        html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            print("email sending process done...")
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False


def send_forgot_password_otp(otp, email):
    
    try:
        title = 'Forgot Password OTP'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = 'Forgot password reset otp is: '
        
        html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False
    
def approve_accounts_profile(otp, email, accounts_email):
    
    try:
        title = 'Accounts Profile Approval'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = f'Dear admin use the provideds otp to approve accounts profile for user {accounts_email}. Thank you!'
        
        html_content = render_to_string("index.html", {'otp': otp,'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False

def new_subscription_email(email):
    
    try:
        title = 'Subscription Renewal'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = 'Dear user your subscription has been renewed.'
        
        html_content = render_to_string("email.html", {'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False


def repairs_email(email, broken_property):
    
    try:
        title = 'Property Repair'
        email_subject = title
        EBIASHARA_EMAIL = settings.EMAIL_HOST_USER
        to = email
        message = f'Dear tenant you requested for a property repair on {broken_property}. Caretaker will call you shortly'
        
        html_content = render_to_string("email.html", {'title': title, 'message': message})
        email = EmailMultiAlternatives(
            email_subject,
            html_content,
            EBIASHARA_EMAIL,
            [to]
        )
        email.attach_alternative(html_content, "text/html")
        if email.send():
            
            return True
        return False
    except Exception as e:
       print('ERROR:', str(e))
       return False
   